#!/usr/bin/env pybricks-micropython
"""Nonmoving entrypoints. No robot framework imports and no automatic execution."""
import sys
import config


def main(args):
    command = args[0] if args else "inspect"
    if command == "inspect":
        from hardware import snapshot
        print("Runtime:", sys.implementation)
        print("Configuration:", config.RUNTIME)
        print("Left motor:", config.LEFT_MOTOR_PORT, "Right motor:", config.RIGHT_MOTOR_PORT)
        print("CALIBRATED:", config.CALIBRATED, "ID:", config.CALIBRATION_ID)
        devices = snapshot()
        if not devices:
            print("No ev3dev motor/sensor devices found")
        for device in devices:
            print(device)
        print("Read-only inspection: no motor or sensor-mode commands sent")
    elif command == "selftest":
        from selftest import run
        run()
    elif command in ("plan", "plan-demo"):
        from planner import demo_course, plan
        if command == "plan-demo":
            print("SYNTHETIC DEMO ONLY: not the assignment course")
            path = plan(demo_course(), 0.15, 0.03, 0.1)
        else:
            config.require_geometry()
            if config.POSITION_ERROR_ALLOWANCE_M is None:
                raise ValueError("Set measured POSITION_ERROR_ALLOWANCE_M")
            path = plan(config.course(), config.FOOTPRINT_RADIUS_M,
                        config.POSITION_ERROR_ALLOWANCE_M, config.GRID_SPACING_M)
        for point in path:
            print("waypoint_m", point[0], point[1])
        print("Plan only: no motor outputs")
    elif command == "monitor":
        import time
        from hardware import snapshot
        count = int(args[1]) if len(args) > 1 else 20
        if not 1 <= count <= 600:
            raise ValueError("Sample count must be between 1 and 600")
        for i in range(count):
            print("sample", i, snapshot())
            time.sleep(0.1)
    else:
        raise ValueError("Commands: inspect, selftest, plan-demo, plan, monitor [samples]")


if __name__ == "__main__":
    main(sys.argv[1:])
