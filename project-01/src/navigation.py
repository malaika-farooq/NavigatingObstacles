"""Our sampled waypoint controller. No device access, clock, or external libraries.

One step consumes time/encoder/gyro measurements and returns desired raw duties.
The caller must independently enforce timing, motor stop/watchdog, and aborts.
This is not a standalone hardware runner or proof of localization accuracy.
"""
import gc
import math
from control import WheelPI, clamp, heading_rate, wheel_targets
from geometry import distance, finite, wrap_degrees
from motion import next_segment
from odometry import Odometry


class Navigator:
    """One route controller; step() returns borrowed result/pose buffers.

    Consumers retaining history must copy values before the next step. Automatic
    GC remains enabled; explicit collection runs at measured stopped transitions.
    """
    TERMINAL = ("DONE", "ABORTED")

    def __init__(self, dimensions, start_pose, world, settings):
        self._validate_geometry(dimensions, start_pose)
        self._validate_settings(settings)
        self.left_diameter, self.right_diameter, self.track = dimensions
        self.settings = dict(settings)
        self.odom = Odometry(*dimensions, start_pose=start_pose)
        self.world = world
        wheel_kp = settings["wheel_kp"]
        wheel_ki = settings["wheel_ki"]
        maximum_duty = settings["max_duty"]
        self.left_pi = WheelPI(wheel_kp, wheel_ki, maximum_duty)
        self.right_pi = WheelPI(wheel_kp, wheel_ki, maximum_duty)
        self._initialize_route_state()
        self._initialize_buffers()

    @staticmethod
    def _validate_geometry(dimensions, start_pose):
        valid_dimensions = all(finite(value) and value > 0 for value in dimensions)
        valid_start = len(start_pose) == 3 and all(finite(value) for value in start_pose)
        if not valid_dimensions or not valid_start:
            raise ValueError("Invalid measured geometry or starting pose")

    @staticmethod
    def _validate_settings(settings):
        required = ("speed_m_s", "acceleration_m_s2", "yaw_rate_rad_s", "heading_kp",
                    "wheel_kp", "wheel_ki", "max_duty", "position_tolerance_m",
                    "heading_tolerance_deg", "settle_s", "stopped_deg_s",
                    "max_gap_s", "leg_timeout_s", "route_timeout_s",
                    "stall_s", "stall_degrees", "stall_target_deg_s", "stall_duty",
                    "max_wheel_deg_s", "max_gyro_deg_s", "gyro_jump_slack_deg",
                    "heading_disagreement_deg")
        for key in required:
            if key not in settings or not finite(settings[key]) or settings[key] <= 0:
                raise ValueError("Set a positive finite controller setting: " + key)
        if settings["max_duty"] > 100 or settings["stall_duty"] > settings["max_duty"]:
            raise ValueError("Invalid duty limits")
        if settings["heading_tolerance_deg"] >= 90:
            raise ValueError("Heading tolerance must be below 90 degrees")

    def _initialize_route_state(self):
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
        self.stall_times = [None, None]
        self.stall_angles = [0.0, 0.0]

    def _initialize_buffers(self):
        self._sample = [0.0, 0.0, 0.0, 0.0]
        self._previous_sample = [0.0, 0.0, 0.0, 0.0]
        self._pose = [0.0, 0.0, 0.0]
        self._previous_position = [0.0, 0.0]
        self._wheel_speeds = [0.0, 0.0]
        self._target_speeds = [0.0, 0.0]
        self._duties = [0.0, 0.0]
        self._segment = [0.0, 0.0]
        self.elapsed_s = 0.0
        self.odom.pose_into(self._pose)
        self._result = {"state": self.state, "reason": "", "pose": self._pose,
                        "pose_valid": True, "waypoint_index": 0,
                        "left_duty": 0.0, "right_duty": 0.0}

    def start(self, waypoints):
        if self.state != "IDLE" or self.previous is None:
            raise ValueError("Sample an idle controller before starting a route")
        points = self._validated_route(waypoints)
        self.route = points
        self.started_at = self.previous[0]
        self.leg_started_at = self.started_at
        self.state = "TURN"
        self._skip_reached()

    def _validated_route(self, waypoints):
        points = []
        for point in waypoints:
            valid_point = len(point) == 2 and all(finite(value) for value in point)
            if not valid_point:
                raise ValueError("Invalid waypoint")
            points.append(tuple(point))
        if not points:
            raise ValueError("Route must contain a waypoint")
        segment_start = self._pose
        for segment_end in points:
            if not self.world.segment_clear(segment_start, segment_end):
                raise ValueError("Route violates configured clearance")
            segment_start = segment_end
        return points

    def abort(self, reason):
        self.state = "ABORTED"
        self.reason = reason
        self.pose_valid = False
        return self._output(0, 0)

    def _output(self, left=0, right=0):
        """Return a reused result and pose buffer; copy values to retain history."""
        result = self._result
        result["state"] = self.state
        result["reason"] = self.reason
        result["pose_valid"] = self.pose_valid
        result["waypoint_index"] = self.index
        result["left_duty"] = left
        result["right_duty"] = right
        return result

    def _rest(self):
        self.speed = 0.0
        self.left_pi.reset()
        self.right_pi.reset()
        self.stall_times[0] = None
        self.stall_times[1] = None

    def _skip_reached(self):
        while self.index < len(self.route):
            if distance(self._pose, self.route[self.index]) > self.settings["position_tolerance_m"]:
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

    def _sample_error(self, sample):
        for value in sample:
            if not finite(value):
                return "nonfinite sensor sample"
        if self.previous is None:
            return ""
        elapsed_s = sample[0] - self.previous[0]
        if elapsed_s <= 0 or elapsed_s > self.settings["max_gap_s"]:
            return "invalid sample timing"
        gyro_change_deg = abs(sample[3] - self.previous[3])
        gyro_rate_allowance_deg = self.settings["max_gyro_deg_s"] * elapsed_s
        gyro_change_limit_deg = gyro_rate_allowance_deg + self.settings["gyro_jump_slack_deg"]
        if gyro_change_deg > gyro_change_limit_deg:
            return "gyro discontinuity"
        left_change_deg = abs(sample[1] - self.previous[1])
        right_change_deg = abs(sample[2] - self.previous[2])
        encoder_change_limit_deg = self.settings["max_wheel_deg_s"] * elapsed_s + 2
        if max(left_change_deg, right_change_deg) > encoder_change_limit_deg:
            return "encoder discontinuity"
        return ""

    def _save_sample(self, sample):
        for value_index in (0, 1, 2, 3):
            self._previous_sample[value_index] = sample[value_index]
        self.previous = self._previous_sample

    def _initialize_sample(self, sample):
        timestamp_s, left_angle_deg, right_angle_deg, gyro_angle_deg = sample
        self.odom.update(left_angle_deg, right_angle_deg, gyro_angle_deg, self._pose)
        self.gyro_baseline = gyro_angle_deg
        self._save_sample(sample)

    def _update_measurements(self, sample):
        timestamp_s, left_angle_deg, right_angle_deg, gyro_angle_deg = sample
        elapsed_s = timestamp_s - self.previous[0]
        left_change_deg = left_angle_deg - self.previous[1]
        right_change_deg = right_angle_deg - self.previous[2]
        self._wheel_speeds[0] = left_change_deg / elapsed_s
        self._wheel_speeds[1] = right_change_deg / elapsed_s
        self._previous_position[0] = self._pose[0]
        self._previous_position[1] = self._pose[1]
        self.odom.update(left_angle_deg, right_angle_deg, gyro_angle_deg, self._pose)
        self.encoder_heading += self.odom.encoder_heading_change
        self.elapsed_s = elapsed_s
        self._save_sample(sample)

    def _localization_error(self, previous_position, gyro_angle_deg):
        estimated_position = self._pose
        if not self.world.point_clear(estimated_position):
            return "estimated pose violates clearance"
        if not self.world.segment_clear(previous_position, estimated_position):
            return "estimated travel violates clearance"
        gyro_heading_change_deg = gyro_angle_deg - self.gyro_baseline
        heading_disagreement_deg = abs(gyro_heading_change_deg - self.encoder_heading)
        if heading_disagreement_deg > self.settings["heading_disagreement_deg"]:
            return "gyro and encoders disagree"
        return ""

    def _motion_timed_out(self, timestamp_s):
        route_elapsed_s = timestamp_s - self.started_at
        leg_elapsed_s = timestamp_s - self.leg_started_at
        route_expired = route_elapsed_s > self.settings["route_timeout_s"]
        leg_expired = leg_elapsed_s > self.settings["leg_timeout_s"]
        return route_expired or leg_expired

    def _settle_at_waypoint(self, remaining_m, wheels_stopped, timestamp_s):
        self._rest()
        if remaining_m > self.settings["position_tolerance_m"]:
            self.state = "TURN"
            self.settled_since = None
        elif self._stable(wheels_stopped, timestamp_s):
            gc.collect()
            self.index += 1
            self.leg_started_at = timestamp_s
            self.state = "TURN"
            self._skip_reached()

    def _turn_is_complete(self, heading_error_deg, wheels_stopped, timestamp_s):
        heading_aligned = abs(heading_error_deg) <= self.settings["heading_tolerance_deg"]
        if not heading_aligned:
            self.settled_since = None
            self.speed = 0.0
            return False
        self._rest()
        if self._stable(wheels_stopped, timestamp_s):
            gc.collect()
            self.state = "DRIVE"
            self.settled_since = None
        return True

    def _update_drive_speed(self, remaining_m, elapsed_s):
        acceleration_m_s2 = self.settings["acceleration_m_s2"]
        braking_speed_m_s = math.sqrt(2 * acceleration_m_s2 * remaining_m)
        approach_speed_m_s = 2 * remaining_m
        desired_speed_m_s = min(self.settings["speed_m_s"], braking_speed_m_s, approach_speed_m_s)
        maximum_speed_change_m_s = acceleration_m_s2 * elapsed_s
        requested_speed_change_m_s = desired_speed_m_s - self.speed
        applied_speed_change_m_s = clamp(requested_speed_change_m_s,
                                        -maximum_speed_change_m_s, maximum_speed_change_m_s)
        self.speed += applied_speed_change_m_s

    def _wheel_commands(self, target_heading_deg, wheel_speeds_deg_s, elapsed_s):
        actual_heading_deg = self._pose[2]
        yaw_rate_rad_s = heading_rate(target_heading_deg, actual_heading_deg,
                                     self.settings["heading_kp"], self.settings["yaw_rate_rad_s"])
        wheel_targets(self.speed, yaw_rate_rad_s, self.track, self.left_diameter,
                      self.right_diameter, self._target_speeds)
        self._duties[0] = self.left_pi.update(self._target_speeds[0], wheel_speeds_deg_s[0], elapsed_s)
        self._duties[1] = self.right_pi.update(self._target_speeds[1], wheel_speeds_deg_s[1], elapsed_s)

    def _wheel_stalled(self, wheel_index, target_speed_deg_s, duty, sample):
        commanded_to_move = abs(target_speed_deg_s) >= self.settings["stall_target_deg_s"]
        sufficient_duty = abs(duty) >= self.settings["stall_duty"]
        if not commanded_to_move or not sufficient_duty:
            self.stall_times[wheel_index] = None
            return False
        timestamp_s = sample[0]
        wheel_angle_deg = sample[wheel_index + 1]
        previous_progress_time_s = self.stall_times[wheel_index]
        progress_deg = abs(wheel_angle_deg - self.stall_angles[wheel_index])
        made_progress = progress_deg >= self.settings["stall_degrees"]
        if previous_progress_time_s is None or made_progress:
            self.stall_times[wheel_index] = timestamp_s
            self.stall_angles[wheel_index] = wheel_angle_deg
            return False
        stalled_duration_s = timestamp_s - previous_progress_time_s
        return stalled_duration_s >= self.settings["stall_s"]

    def _command_output(self, target_heading_deg, wheel_speeds_deg_s, elapsed_s, sample):
        self._wheel_commands(target_heading_deg, wheel_speeds_deg_s, elapsed_s)
        for wheel_index in (0, 1):
            target_speed_deg_s = self._target_speeds[wheel_index]
            requested_duty = self._duties[wheel_index]
            if self._wheel_stalled(wheel_index, target_speed_deg_s, requested_duty, sample):
                return self.abort("wheel " + str(wheel_index) + " stalled")
        return self._output(self._duties[0], self._duties[1])

    def _advance_waypoint(self, timestamp_s, wheel_speeds_deg_s, elapsed_s, sample):
        target_position = self.route[self.index]
        estimated_pose = self._pose
        if not self.world.segment_clear(estimated_pose, target_position):
            return self.abort("corrective segment violates clearance")
        next_segment(estimated_pose, target_position, self._segment)
        target_heading_deg, remaining_m = self._segment
        heading_error_deg = wrap_degrees(target_heading_deg - estimated_pose[2])
        fastest_wheel_deg_s = max(abs(wheel_speeds_deg_s[0]), abs(wheel_speeds_deg_s[1]))
        wheels_stopped = fastest_wheel_deg_s <= self.settings["stopped_deg_s"]
        if self.state == "SETTLE":
            self._settle_at_waypoint(remaining_m, wheels_stopped, timestamp_s)
            return self._output()
        if remaining_m <= self.settings["position_tolerance_m"]:
            self.state = "SETTLE"
            self.settled_since = None
            self._rest()
            return self._output()
        if self.state == "TURN":
            if self._turn_is_complete(heading_error_deg, wheels_stopped, timestamp_s):
                return self._output()
        elif abs(heading_error_deg) > 45:
            self.state = "TURN"
            self._rest()
            return self._output()
        elif self.state == "DRIVE":
            self._update_drive_speed(remaining_m, elapsed_s)
        return self._command_output(target_heading_deg, wheel_speeds_deg_s, elapsed_s, sample)

    def step(self, now_s, left_angle_deg, right_angle_deg, gyro_angle_deg, abort=False):
        if self.state in self.TERMINAL:
            return self._output()
        if abort:
            return self.abort("operator abort")
        sample = self._sample
        sample[0] = now_s
        sample[1] = left_angle_deg
        sample[2] = right_angle_deg
        sample[3] = gyro_angle_deg
        sample_error = self._sample_error(sample)
        if sample_error:
            return self.abort(sample_error)
        if self.previous is None:
            self._initialize_sample(sample)
            return self._output()
        self._update_measurements(sample)
        localization_error = self._localization_error(self._previous_position, gyro_angle_deg)
        if localization_error:
            return self.abort(localization_error)
        if self.state == "IDLE":
            return self._output()
        if self._motion_timed_out(now_s):
            return self.abort("motion timeout")
        return self._advance_waypoint(now_s, self._wheel_speeds, self.elapsed_s, sample)
