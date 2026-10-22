"""Robot configuration: meters, degrees, seconds; no third-party imports.

None means unmeasured/unconfirmed, never an implicit hardware default.
Front = caster end. Left/right are viewed from behind looking forward.
"""
RUNTIME = "pybricks-micropython 2.0.0 on ev3dev-stretch"
CALIBRATION_ID = "unmeasured"
CALIBRATED = False

LEFT_MOTOR_PORT = "A"  # Confirmed by the builder.
RIGHT_MOTOR_PORT = "B"
LEFT_FORWARD_SIGN = None  # +1 or -1 after a raised-wheel direction test.
RIGHT_FORWARD_SIGN = None
GYRO_PORT = "1"          # Confirmed by the builder; verify discovery on reconnection.
COLOR_PORT = "4"         # Confirmed by the builder; optional, set None to omit.
GYRO_CCW_SIGN = None     # +1 or -1: logical counterclockwise is positive.

LEFT_WHEEL_DIAMETER_M = None
RIGHT_WHEEL_DIAMETER_M = None
WHEEL_TRACK_M = None
FOOTPRINT_RADIUS_M = None  # Farthest point from midpoint of drive wheels.
POSITION_ERROR_ALLOWANCE_M = None
COLOR_OFFSET_FORWARD_M = None
COLOR_OFFSET_LEFT_M = None
SEAM_CORRECTION_ENABLED = False

# Fill with the actual assigned course. PDF has conflicting workspace widths.
WORKSPACE_M = None       # (width, height), origin at lower-left.
START_POSE = None        # (x_m, y_m, counterclockwise_heading_degrees).
GOAL_M = None            # (x_m, y_m).
OBSTACLES_M = []         # Centers of axis-aligned cardboard squares.
OBSTACLE_SIDE_M = 0.305
GRID_SPACING_M = 0.1525

# These bound future tuning experiments, not a calibrated motion controller.
CONTROL_PERIOD_MS = 20
MAX_DUTY_PERCENT = 25
MAX_MOTION_TIME_S = 10


def require_geometry():
    for name in ("LEFT_WHEEL_DIAMETER_M", "RIGHT_WHEEL_DIAMETER_M",
                 "WHEEL_TRACK_M", "FOOTPRINT_RADIUS_M"):
        value = globals()[name]
        if value is None or value <= 0:
            raise ValueError("Measure and set " + name)


def require_motion_calibration():
    require_geometry()
    if not CALIBRATED or CALIBRATION_ID == "unmeasured":
        raise ValueError("Motion disabled: calibration has not been confirmed")
    for name in ("LEFT_FORWARD_SIGN", "RIGHT_FORWARD_SIGN", "GYRO_CCW_SIGN"):
        if globals()[name] not in (-1, 1):
            raise ValueError("Confirm " + name)


def course():
    if WORKSPACE_M is None or START_POSE is None or GOAL_M is None:
        raise ValueError("Set actual WORKSPACE_M, START_POSE and GOAL_M in config.py")
    return {"workspace": WORKSPACE_M, "start": START_POSE[:2], "goal": GOAL_M,
            "obstacles": OBSTACLES_M, "obstacle_side": OBSTACLE_SIDE_M}
