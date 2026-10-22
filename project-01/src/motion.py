"""Motion integration boundary. No motor activity on import.

The CLI deliberately has no motion command yet: direction tests, calibrated
gains, a timed loop, stall detection, and an independent motor watchdog/abort
path must be completed before raw run-direct control is used on the floor.
"""
import math
from geometry import distance, wrap_degrees


def next_segment(pose, waypoint, output=None):
    """Heading and distance from current pose; optional two-value output buffer."""
    remaining_m = distance(pose, waypoint)
    target_heading_deg = pose[2]
    if remaining_m >= 1e-9:
        difference_x_m = waypoint[0] - pose[0]
        difference_y_m = waypoint[1] - pose[1]
        target_heading_rad = math.atan2(difference_y_m, difference_x_m)
        target_heading_deg = wrap_degrees(math.degrees(target_heading_rad))
    if output is None:
        return target_heading_deg, remaining_m
    output[0] = target_heading_deg
    output[1] = remaining_m
    return output


class MotionSession:
    """Explicit output gate for later control-loop integration.

    Even a finally block cannot brake after SIGKILL or power loss. Do not treat
    this gate as the independent watchdog that an executing motion loop needs.
    """
    def __init__(self, config):
        config.require_motion_calibration()
        from hardware import Motor
        self.left = Motor(config.LEFT_MOTOR_PORT, config.LEFT_FORWARD_SIGN, config.MAX_DUTY_PERCENT)
        self.right = Motor(config.RIGHT_MOTOR_PORT, config.RIGHT_FORWARD_SIGN, config.MAX_DUTY_PERCENT)
        self.pose_valid = True

    def enable(self):
        try:
            self.left.enable()
            self.right.enable()
        except BaseException:
            self.abort()
            raise

    def stop(self):
        try:
            self.left.stop()
        finally:
            self.right.stop()

    def abort(self):
        self.pose_valid = False
        self.stop()
