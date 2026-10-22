"""Motion integration boundary. No motor activity on import.

The CLI deliberately has no motion command yet: direction tests, calibrated
gains, a timed loop, stall detection, and an independent motor watchdog/abort
path must be completed before raw run-direct control is used on the floor.
"""
import math
from geometry import distance, wrap_degrees


def next_segment(pose, waypoint):
    """Calculate the next turn/travel from actual estimated pose, not old plan lengths."""
    length = distance(pose, waypoint)
    if length < 1e-9:
        return (pose[2], 0.0)
    heading = math.degrees(math.atan2(waypoint[1] - pose[1], waypoint[0] - pose[0]))
    return (wrap_degrees(heading), length)


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
