#!/usr/bin/env pybricks-micropython
"""Nonmoving project commands. No external robotics library imports."""
import gc
import sys
import config


def inspect_devices():
    from hardware import snapshot
    print("Runtime:", sys.implementation)
    print("Left motor:", config.LEFT_MOTOR_PORT, "Right motor:", config.RIGHT_MOTOR_PORT)
    print("Gyro input:", config.GYRO_PORT, "Color input:", config.COLOR_PORT)
    print("CALIBRATED:", config.CALIBRATED, "ID:", config.CALIBRATION_ID)
    if hasattr(gc, "mem_free"):
        print("MicroPython free heap bytes:", gc.mem_free())
    devices = snapshot()
    if not devices:
        print("No ev3dev motor/sensor devices found")
    for device in devices:
        print(device)
    print("Read-only inspection: no device commands sent")


def monitor_devices(arguments):
    import time
    from hardware import snapshot
    sample_count = int(arguments[0]) if arguments else 20
    if not 1 <= sample_count <= 600:
        raise ValueError("Sample count must be between 1 and 600")
    for sample_index in range(sample_count):
        readings = snapshot()
        print("sample", sample_index, readings)
        time.sleep(0.1)


def check_color():
    from hardware import ColorSensor, reflection_is_black
    sensor = ColorSensor(config.COLOR_PORT)
    reflection_percent = sensor.reflection()
    threshold_percent = config.COLOR_BLACK_THRESHOLD_PERCENT
    black_detected = reflection_is_black(reflection_percent, threshold_percent)
    print("Reflection percent:", reflection_percent)
    print("Black threshold percent:", threshold_percent)
    print("Black detected:", black_detected)


def configured_path():
    from planner import plan
    config.require_geometry()
    if config.POSITION_ERROR_ALLOWANCE_M is None:
        raise ValueError("Set measured POSITION_ERROR_ALLOWANCE_M")
    assigned_course = config.course()
    robot_radius_m = config.FOOTPRINT_RADIUS_M
    position_allowance_m = config.POSITION_ERROR_ALLOWANCE_M
    return plan(assigned_course, robot_radius_m, position_allowance_m, config.GRID_SPACING_M)


def demo_path():
    from planner import demo_course, plan
    print("SYNTHETIC DEMO ONLY: not the assignment course")
    illustrative_radius_m = 0.15
    illustrative_error_m = 0.03
    illustrative_grid_spacing_m = 0.1
    return plan(demo_course(), illustrative_radius_m, illustrative_error_m, illustrative_grid_spacing_m)


def print_path(path):
    # Planner search containers are no longer needed; motors are not enabled.
    gc.collect()
    for position_m in path:
        print("waypoint_m", position_m[0], position_m[1])
    print("Plan only: no motor outputs")


def simulate_demo():
    from simulation import run_demo
    print("SYNTHETIC SIMULATION ONLY: fictional geometry/gains, no hardware")
    result = run_demo()
    print(result)


def main(arguments):
    command = arguments[0] if arguments else "inspect"
    if command == "inspect":
        inspect_devices()
    elif command == "monitor":
        monitor_devices(arguments[1:])
    elif command == "color-check":
        check_color()
    elif command == "plan":
        print_path(configured_path())
    elif command == "plan-demo":
        print_path(demo_path())
    elif command == "simulate-demo":
        simulate_demo()
    elif command == "selftest":
        from selftest import run
        run()
    else:
        raise ValueError("Commands: inspect, selftest, color-check, simulate-demo, plan-demo, plan, monitor [samples]")


if __name__ == "__main__":
    main(sys.argv[1:])
