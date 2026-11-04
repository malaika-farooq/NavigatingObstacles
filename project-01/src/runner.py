"""Hardware runner: connects the Navigator to the real motors, encoders and gyro.

Built-in modules and our own code only. This is the only place that moves the
robot. Motors are stopped on every exit path: normal finish, abort, controller
failure, Ctrl-C, or any exception. A second terminal can also run `stop`.

The controller settings below are conservative starting values from the
simulation. They are NOT tuned on the real robot.
"""
import math
import os
import time
import config
from hardware import Gyro, Motor, MOTOR_ROOT, discover, write
from navigation import Navigator
from planner import CourseMap

ABORT_FLAG = "/tmp/ev3-abort"   # Create this file to stop a run: `touch /tmp/ev3-abort`
ABORT_CHECK_EVERY = 5           # Check the flag every N control steps.
LOG_DIR = "/home/robot/navigating-obstacles/project-01/logs"  # Fetch with `ev3.py fetch-logs`.
LOG_EVERY = 5                   # Print status every N control steps (0.1 s at 20 ms).
GYRO_SETTLE_S = 1.5             # Robot must stay still while the gyro starts.


def run_settings():
    return {"speed_m_s": 0.06, "acceleration_m_s2": 0.12, "yaw_rate_rad_s": 0.45, "min_turn_yaw_rate_rad_s": 0.3,
            "heading_kp": 2.5, "wheel_kp": 0.12, "wheel_ki": 0.45,
            "max_duty": config.MAX_DUTY_PERCENT,
            "position_tolerance_m": 0.015, "heading_tolerance_deg": 2.0,
            "settle_s": 0.2, "stopped_deg_s": 5.0, "max_gap_s": 0.5,
            "leg_timeout_s": 90, "route_timeout_s": 240, "stall_s": 1.5,
            "stall_degrees": 2, "stall_target_deg_s": 15, "stall_duty": 8,
            "max_wheel_deg_s": 800, "max_gyro_deg_s": 180,
            "gyro_jump_slack_deg": 3,
            # Floor tests: the gyro held the robot straight while the wheel counters
            # drifted 16 deg in 0.9 m (wheel slip). The gyro steers; keep the
            # cross-check as a gross-failure net only. Gyro jumps are still caught.
            "heading_disagreement_deg": 360}


_log_file = None


def _timestamp():
    try:
        return int(time.time())
    except AttributeError:
        return time.ticks_ms()


def _open_log(name):
    """Start a log file in LOG_DIR; if it cannot be opened the run still goes on."""
    global _log_file
    path = "%s/%s-%d.txt" % (LOG_DIR, name, _timestamp())
    try:
        _log_file = open(path, "w")
        print("Logging to", path)
    except OSError:
        _log_file = None
        print("Could not open a log file; printing only")


def _emit(text):
    print(text)
    if _log_file is not None:
        _log_file.write(text + "\n")
        _log_file.flush()


def _close_log():
    global _log_file
    if _log_file is not None:
        _log_file.close()
        _log_file = None


def stop_all_motors():
    """Independent stop: writes `stop` to every motor. Safe to run from a second terminal."""
    for device in discover(MOTOR_ROOT):
        write(device["path"], "stop_action", "brake")
        write(device["path"], "command", "stop")
    print("Sent stop to", len(discover(MOTOR_ROOT)), "motors")


def _abort_requested():
    try:
        os.stat(ABORT_FLAG)
        return True
    except OSError:
        return False


def _clear_abort_flag():
    try:
        os.remove(ABORT_FLAG)
    except OSError:
        pass


def _open_devices():
    left = Motor(config.LEFT_MOTOR_PORT, config.LEFT_FORWARD_SIGN, config.MAX_DUTY_PERCENT)
    right = Motor(config.RIGHT_MOTOR_PORT, config.RIGHT_FORWARD_SIGN, config.MAX_DUTY_PERCENT)
    gyro = Gyro(config.GYRO_PORT, config.GYRO_CCW_SIGN, config.GYRO_SCALE)
    gyro.initialize()
    time.sleep(GYRO_SETTLE_S)
    return left, right, gyro


def _make_navigator(world):
    dimensions = (config.LEFT_WHEEL_DIAMETER_M * config.DISTANCE_SCALE,
                  config.RIGHT_WHEEL_DIAMETER_M * config.DISTANCE_SCALE,
                  config.WHEEL_TRACK_M)
    return Navigator(dimensions, config.START_POSE, world, run_settings())


def _log(now_s, output, left_deg, right_deg, gyro_deg):
    pose = output["pose"]
    _emit("t=%.1f %s wp=%d x=%.3f y=%.3f hdg=%.1f duty=%.0f/%.0f wheels=%.0f/%.0f gyro=%.1f" % (
        now_s, output["state"], output["waypoint_index"], pose[0], pose[1], pose[2],
        output["left_duty"], output["right_duty"], left_deg, right_deg, gyro_deg))


def _control_loop(left, right, gyro, navigator, route):
    """Drive the route. Returns the final controller output. Caller stops the motors."""
    start_ticks = time.ticks_ms()
    period_ms = config.CONTROL_PERIOD_MS
    left.enable()
    right.enable()
    output = None
    step_index = 0
    while True:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ticks)
        now_s = elapsed_ms / 1000.0
        abort = step_index % ABORT_CHECK_EVERY == 0 and _abort_requested()
        left_deg = left.angle_degrees()
        right_deg = right.angle_degrees()
        gyro_deg = gyro.angle_degrees()
        output = navigator.step(now_s, left_deg, right_deg, gyro_deg, abort)
        if step_index == 0:
            navigator.start(route)   # First sample taken: baseline is set.
        if step_index % LOG_EVERY == 0 or navigator.state in navigator.TERMINAL:
            _log(now_s, output, left_deg, right_deg, gyro_deg)
        if navigator.state in navigator.TERMINAL:
            return output
        left.set_duty(output["left_duty"])
        right.set_duty(output["right_duty"])
        step_index += 1
        time.sleep_ms(period_ms)


def _execute(route, world):
    """Run one route with guaranteed motor stop. Prints the outcome."""
    left, right, gyro = _open_devices()
    navigator = _make_navigator(world)
    _clear_abort_flag()
    _open_log("run")
    _emit("Route: " + str(route))
    print("Starting in 3 s. Abort: Ctrl-C, or `touch", ABORT_FLAG, "`, or `main.py stop`.")
    time.sleep(3)
    output = None
    try:
        output = _control_loop(left, right, gyro, navigator, route)
    except KeyboardInterrupt:
        print("Ctrl-C: stopping")
    finally:
        _stop_both(left, right)
    _report(output)
    _close_log()


def _stop_both(left, right):
    for motor in (left, right):
        try:
            motor.stop()
        except Exception as error:
            print("Motor stop error:", error)
    try:
        stop_all_motors()
    except Exception as error:
        print("Fallback stop error:", error)


def _report(output):
    if output is None:
        _emit("Run ended before the controller finished")
        return
    pose = output["pose"]
    _emit("FINISHED state: %s reason: %s" % (output["state"], output["reason"]))
    _emit("Estimated pose: x=%.3f y=%.3f heading=%.1f" % (pose[0], pose[1], pose[2]))
    goal_x_m, goal_y_m = config.GOAL_M
    goal_error_m = math.sqrt((pose[0] - goal_x_m) ** 2 + (pose[1] - goal_y_m) ** 2)
    _emit("Estimated distance to goal: %.3f m (goal radius %.3f m)" % (
        goal_error_m, config.GOAL_RADIUS_M))
    reached = output["state"] == "DONE" and goal_error_m <= config.GOAL_RADIUS_M
    _emit("GOAL REACHED (by dead reckoning): " + ("YES" if reached else "NO"))
    _emit("Measure the real position with a ruler and compare.")


def run_course():
    """Plan the assigned course and drive it. Needs full motion calibration."""
    from planner import plan
    config.require_motion_calibration()
    if config.POSITION_ERROR_ALLOWANCE_M is None:
        raise ValueError("Set measured POSITION_ERROR_ALLOWANCE_M")
    radius_m = config.FOOTPRINT_RADIUS_M
    allowance_m = config.POSITION_ERROR_ALLOWANCE_M
    route = plan(config.course(), radius_m, allowance_m, config.GRID_SPACING_M)
    world = CourseMap(config.course(), radius_m, allowance_m)
    _execute(route, world)
