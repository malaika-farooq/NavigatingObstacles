"""Robot configuration: meters, degrees, seconds; no third-party imports.


"""
RUNTIME = "pybricks-micropython 2.0.0 on ev3dev-stretch"
CALIBRATION_ID = "2026-11-02-rebuild-ruler"  # Rebuilt robot: ruler geometry, hand-checked signs; no distance/turn runs yet.
# Set True on 2026-10-29 at the builder's direction to run the course demo. Distance
# calibration is incomplete: one 1 m drive ended ~17% short of the wheel counters.
CALIBRATED = True

LEFT_MOTOR_PORT = "B"  # Rebuilt robot: first run turned the wrong way, so A and B are swapped.
RIGHT_MOTOR_PORT = "A"
LEFT_FORWARD_SIGN = -1   # Positive raw A drove backward in observed floor test.
RIGHT_FORWARD_SIGN = -1  # Positive raw B also drove away from the front caster.
GYRO_PORT = "1"          # Confirmed by the builder; verify discovery on reconnection.
GYRO_CCW_SIGN = -1       # Observed CCW hand turn decreased raw gyro angle.
# Real angle / gyro angle. Measured with spin-test on 2026-11-02: two full circles by hand
# (720 deg true) read 556 deg on the raw gyro, so 720/556 = 1.295. An earlier ruler estimate
# from the first 90 deg turn gave ~1.17. Below 1.0 would mean the gyro over-reads.
GYRO_SCALE = 1.0  # Hand spin, 4 x 90 deg: 359 and 356 raw per 360 deg. 1.31 was for the earlier gyro mounting.

# Builder-measured tires: 70 mm diameter, 34.9 mm (1.375 in) wide. Two 1.000 m hand pushes (no
# motors) gave a mean effective diameter of 0.0699 m (0.0711 and 0.0686). The left wheel
# turned more than the right in both pushes (+4.6%, +2.5%) and in most drives (+3% on
# average over six runs), so the left is set about 3.4% smaller. Gyro handles heading.
LEFT_WHEEL_DIAMETER_M = 0.07176   # Rebuilt robot: 2.825 in (71.755 mm) measured with a ruler, both wheels.
RIGHT_WHEEL_DIAMETER_M = 0.07176  # The old left/right split came from the old build; redo with push-test.
# Under-power correction: ruler distance / encoder distance. 1.0 until measured; the
# 1 m test suggests about 0.8 (ruler 0.78-0.79 m vs counters 0.99 m).
DISTANCE_SCALE = 0.931  # Wood floor: 1 m test ran 36 in (0.914 m); raised from 0.93 after the robot ended 6 in past the goal.
WHEEL_TRACK_M = 0.13335  # Rebuilt robot: 6.875 in outside-to-outside minus 1.625 in tire width = 5.25 in (133.35 mm).
FOOTPRINT_RADIUS_M = 0.17  # Remeasured: 17 cm from wheel midpoint to farthest point (was 0.2413 m).
POSITION_ERROR_ALLOWANCE_M = 0.05
 # Planning margin; the 0.61 m corridor allows up to ~0.064 with the 0.2413 m footprint.

# Course values live in course.py, in the PDF's header-file format.
import course as _course
WORKSPACE_M = _course.workspace_m()  # (width, height), origin at lower-left.
START_POSE = (_course.start[0], _course.start[1], _course.start_heading_deg)
GOAL_M = _course.goal
OBSTACLES_M = _course.obstacle_centers_m()  # Centers of axis-aligned squares.
OBSTACLE_SIDE_M = 0.305
GOAL_RADIUS_M = 0.305
GRID_SPACING_M = 0.1524   # Half a tile (6 in, from the measured 12 in tile): lands on tile centers and corners.

# These bound future tuning experiments, not a calibrated motion controller.
CONTROL_PERIOD_MS = 20
MAX_DUTY_PERCENT = 35  # 25 saturated on the floor at 0.07 m/s; see 1 m drive test.
MAX_MOTION_TIME_S = 10


def require_geometry():
    for name in ("LEFT_WHEEL_DIAMETER_M", "RIGHT_WHEEL_DIAMETER_M",
                 "WHEEL_TRACK_M", "FOOTPRINT_RADIUS_M"):
        value = globals()[name]
        if value is None or value <= 0:
            raise ValueError("Measure and set " + name)


def require_motion_calibration():
    require_geometry()
    from geometry import finite
    if START_POSE is None or not finite(START_POSE[2]):
        raise ValueError("Confirm start_heading_deg in course.py")
    if not CALIBRATED or CALIBRATION_ID == "unmeasured":
        raise ValueError("Motion disabled: calibration has not been confirmed")
    for name in ("LEFT_FORWARD_SIGN", "RIGHT_FORWARD_SIGN", "GYRO_CCW_SIGN"):
        if globals()[name] not in (-1, 1):
            raise ValueError("Confirm " + name)


def course():
    if WORKSPACE_M is None or START_POSE is None or GOAL_M is None:
        raise ValueError("Set actual WORKSPACE_M, START_POSE and GOAL_M in config.py")
    return {"workspace": WORKSPACE_M, "start": START_POSE[:2], "goal": GOAL_M,
            "obstacles": OBSTACLES_M, "obstacle_side": OBSTACLE_SIDE_M,
            "goal_radius": GOAL_RADIUS_M}
