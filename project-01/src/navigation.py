"""Our sampled waypoint controller. No device access, clock, or external libraries.

One step consumes time/encoder/gyro measurements and returns desired raw duties.
The caller must independently enforce timing, motor stop/watchdog, and aborts.
This is not a standalone hardware runner or proof of localization accuracy.
"""
import math
from control import WheelPI, clamp, heading_rate, wheel_targets
from geometry import distance, finite, wrap_degrees
from motion import next_segment
from odometry import Odometry


class Navigator:
    TERMINAL = ("DONE", "ABORTED")

    def __init__(self, dimensions, start_pose, world, settings):
        self.left_diameter, self.right_diameter, self.track = dimensions
        if not all(finite(v) and v > 0 for v in dimensions):
            raise ValueError("Invalid measured geometry")
        if len(start_pose) != 3 or not all(finite(v) for v in start_pose):
            raise ValueError("Invalid starting pose")
        required = ("speed_m_s", "acceleration_m_s2", "yaw_rate_rad_s", "heading_kp",
                    "wheel_kp", "wheel_ki", "max_duty", "position_tolerance_m",
                    "heading_tolerance_deg", "settle_s", "stopped_deg_s",
                    "max_gap_s", "leg_timeout_s", "route_timeout_s",
                    "stall_s", "stall_degrees", "stall_target_deg_s", "stall_duty",
                    "max_wheel_deg_s", "max_gyro_deg_s", "gyro_jump_slack_deg",
                    "heading_disagreement_deg")
        self.settings = dict(settings)
        for key in required:
            if key not in settings or not finite(settings[key]) or settings[key] <= 0:
                raise ValueError("Set a positive finite controller setting: " + key)
        if settings["max_duty"] > 100 or settings["stall_duty"] > settings["max_duty"]:
            raise ValueError("Invalid duty limits")
        if settings["heading_tolerance_deg"] >= 90:
            raise ValueError("Heading tolerance must be below 90 degrees")
        self.odom = Odometry(*dimensions, start_pose=start_pose)
        self.world = world
        self.left_pi = WheelPI(settings["wheel_kp"], settings["wheel_ki"], settings["max_duty"])
        self.right_pi = WheelPI(settings["wheel_kp"], settings["wheel_ki"], settings["max_duty"])
        self.state = "IDLE"
        self.reason = ""
        self.pose_valid = True
        self.previous = None
        self.route = []
        self.index = 0
        self.speed = 0.0
        self.settled_since = None
        self.started_at = None
        self.leg_started_at = None
        self.encoder_heading = 0.0
        self.gyro_baseline = None
        self.stall_marks = [None, None]

    def start(self, waypoints):
        if self.state != "IDLE" or self.previous is None:
            raise ValueError("Sample an idle controller before starting a route")
        points = []
        for point in waypoints:
            if len(point) != 2 or not all(finite(v) for v in point):
                raise ValueError("Invalid waypoint")
            points.append(tuple(point))
        if not points:
            raise ValueError("Route must contain a waypoint")
        last = self.odom.pose()[:2]
        for point in points:
            if not self.world.segment_clear(last, point):
                raise ValueError("Route violates configured clearance")
            last = point
        self.route = points
        self.started_at = self.previous[0]
        self.leg_started_at = self.started_at
        self.state = "TURN"
        self._skip_reached()

    def abort(self, reason):
        self.state = "ABORTED"
        self.reason = reason
        self.pose_valid = False
        return self._output(0, 0)

    def _output(self, left=0, right=0):
        return {"state": self.state, "reason": self.reason, "pose": self.odom.pose(),
                "pose_valid": self.pose_valid, "waypoint_index": self.index,
                "left_duty": left, "right_duty": right}

    def _rest(self):
        self.speed = 0.0
        self.left_pi.reset()
        self.right_pi.reset()
        self.stall_marks = [None, None]

    def _skip_reached(self):
        while self.index < len(self.route):
            if distance(self.odom.pose(), self.route[self.index]) > self.settings["position_tolerance_m"]:
                break
            self.index += 1
        if self.index == len(self.route):
            self.state = "DONE"
        self.settled_since = None
        self._rest()

    def _stable(self, condition, now):
        if not condition:
            self.settled_since = None
            return False
        if self.settled_since is None:
            self.settled_since = now
        return now - self.settled_since >= self.settings["settle_s"]

    def step(self, now_s, left_angle_deg, right_angle_deg, gyro_angle_deg, abort=False):
        if self.state in self.TERMINAL:
            return self._output()
        if abort:
            return self.abort("operator abort")
        sample = (now_s, left_angle_deg, right_angle_deg, gyro_angle_deg)
        if not all(finite(v) for v in sample):
            return self.abort("nonfinite sensor sample")
        if self.previous is None:
            self.previous = sample
            self.gyro_baseline = gyro_angle_deg
            self.odom.update(left_angle_deg, right_angle_deg, gyro_angle_deg)
            return self._output()
        old = self.previous
        dt = now_s - old[0]
        s = self.settings
        if dt <= 0 or dt > s["max_gap_s"]:
            return self.abort("invalid sample timing")
        if abs(gyro_angle_deg - old[3]) > s["max_gyro_deg_s"] * dt + s["gyro_jump_slack_deg"]:
            return self.abort("gyro discontinuity")
        if max(abs(left_angle_deg-old[1]), abs(right_angle_deg-old[2])) > s["max_wheel_deg_s"] * dt + 2:
            return self.abort("encoder discontinuity")
        speeds = ((left_angle_deg-old[1])/dt, (right_angle_deg-old[2])/dt)
        old_position = self.odom.pose()[:2]
        self.odom.update(left_angle_deg, right_angle_deg, gyro_angle_deg)
        self.encoder_heading += self.odom.encoder_heading_change
        self.previous = sample
        if not self.world.point_clear(self.odom.pose()[:2]):
            return self.abort("estimated pose violates clearance")
        if not self.world.segment_clear(old_position, self.odom.pose()[:2]):
            return self.abort("estimated travel violates clearance")
        # This detects some inconsistencies, not equal-wheel slip or true pose.
        if abs((gyro_angle_deg-self.gyro_baseline)-self.encoder_heading) > s["heading_disagreement_deg"]:
            return self.abort("gyro and encoders disagree")
        if self.state == "IDLE":
            return self._output()
        if now_s-self.started_at > s["route_timeout_s"] or now_s-self.leg_started_at > s["leg_timeout_s"]:
            return self.abort("motion timeout")
        target = self.route[self.index]
        pose = self.odom.pose()
        if not self.world.segment_clear(pose[:2], target):
            return self.abort("corrective segment violates clearance")
        heading, remaining = next_segment(pose, target)
        error = wrap_degrees(heading-pose[2])
        stopped = max(abs(speeds[0]), abs(speeds[1])) <= s["stopped_deg_s"]
        if self.state == "SETTLE":
            self._rest()
            if remaining > s["position_tolerance_m"]:
                self.state = "TURN"
                self.settled_since = None
            elif self._stable(stopped, now_s):
                self.index += 1
                self.leg_started_at = now_s
                self.state = "TURN"
                self._skip_reached()
            return self._output()
        if remaining <= s["position_tolerance_m"]:
            self.state = "SETTLE"
            self.settled_since = None
            self._rest()
            return self._output()
        if self.state == "TURN":
            if abs(error) <= s["heading_tolerance_deg"]:
                self._rest()
                if self._stable(stopped, now_s):
                    self.state = "DRIVE"
                    self.settled_since = None
                return self._output()
            self.settled_since = None
            self.speed = 0.0
        elif abs(error) > 45:
            self.state = "TURN"
            self._rest()
            return self._output()
        elif self.state == "DRIVE":
            desired = min(s["speed_m_s"], math.sqrt(2*s["acceleration_m_s2"]*remaining), 2*remaining)
            self.speed += clamp(desired-self.speed, -s["acceleration_m_s2"]*dt, s["acceleration_m_s2"]*dt)
        yaw = heading_rate(heading, pose[2], s["heading_kp"], s["yaw_rate_rad_s"])
        targets = wheel_targets(self.speed, yaw, self.track, self.left_diameter, self.right_diameter)
        duties = (self.left_pi.update(targets[0], speeds[0], dt),
                  self.right_pi.update(targets[1], speeds[1], dt))
        for i in (0, 1):
            angle = sample[i+1]
            mark = self.stall_marks[i]
            if abs(targets[i]) < s["stall_target_deg_s"] or abs(duties[i]) < s["stall_duty"]:
                self.stall_marks[i] = None
            elif mark is None or abs(angle-mark[1]) >= s["stall_degrees"]:
                self.stall_marks[i] = (now_s, angle)
            elif now_s-mark[0] >= s["stall_s"]:
                return self.abort("wheel " + str(i) + " stalled")
        return self._output(*duties)
