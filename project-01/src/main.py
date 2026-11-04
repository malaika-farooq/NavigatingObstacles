#!/usr/bin/env pybricks-micropython
"""Project commands. Only stop and run move the robot."""
import gc
import sys
import config


def inspect_devices():
    from hardware import snapshot
    print("Runtime:", sys.implementation)
    print("Left motor:", config.LEFT_MOTOR_PORT, "Right motor:", config.RIGHT_MOTOR_PORT)
    print("Gyro input:", config.GYRO_PORT)
    print("CALIBRATED:", config.CALIBRATED, "ID:", config.CALIBRATION_ID)
    if hasattr(gc, "mem_free"):
        print("MicroPython free heap bytes:", gc.mem_free())
    devices = snapshot()
    if not devices:
        print("No ev3dev motor/sensor devices found")
    for device in devices:
        print(device)
    print("Read-only inspection: no device commands sent")


def configured_path():
    from planner import plan
    config.require_geometry()
    if config.POSITION_ERROR_ALLOWANCE_M is None:
        raise ValueError("Set measured POSITION_ERROR_ALLOWANCE_M")
    assigned_course = config.course()
    robot_radius_m = config.FOOTPRINT_RADIUS_M
    position_allowance_m = config.POSITION_ERROR_ALLOWANCE_M
    return plan(assigned_course, robot_radius_m, position_allowance_m, config.GRID_SPACING_M)


def print_path(path):
    # Planner search containers are no longer needed; motors are not enabled.
    gc.collect()
    for position_m in path:
        print("waypoint_m", position_m[0], position_m[1])
    print("Plan only: no motor outputs")


def main(arguments):
    command = arguments[0] if arguments else "inspect"
    if command == "inspect":
        inspect_devices()
    elif command == "plan":
        print_path(configured_path())
    elif command == "stop":
        from runner import stop_all_motors
        stop_all_motors()
    elif command == "run":
        from runner import run_course
        run_course()
    elif command == "spin":
        from spin_test import run
        run()
    elif command == "turn":
        from spin_test import turn
        turn()
    else:
        raise ValueError("Commands: inspect, plan, stop, run, spin, turn")


if __name__ == "__main__":
    main(sys.argv[1:])
