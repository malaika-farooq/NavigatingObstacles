"""Deterministic illustrative simulator, built-in math only. Never imports hardware.

Constants below belong to a fictional robot. They do not populate config.py or
predict the EV3's real motor response, slip, gyro drift, or caster behavior.
"""
import math
from geometry import distance, wrap_degrees
from navigation import Navigator
from planner import CourseMap, demo_course, plan


def demo_settings():
    return {"speed_m_s": 0.07, "acceleration_m_s2": 0.12, "yaw_rate_rad_s": 0.45,
            "heading_kp": 2.5, "wheel_kp": 0.12, "wheel_ki": 0.45, "max_duty": 25,
            "position_tolerance_m": 0.015, "heading_tolerance_deg": 2.0,
            "settle_s": 0.2, "stopped_deg_s": 5.0, "max_gap_s": 0.2,
            "leg_timeout_s": 90, "route_timeout_s": 240, "stall_s": 0.8,
            "stall_degrees": 2, "stall_target_deg_s": 15, "stall_duty": 8,
            "max_wheel_deg_s": 800, "max_gyro_deg_s": 180,
            "gyro_jump_slack_deg": 3, "heading_disagreement_deg": 15}


class SimRobot:
    def __init__(self, pose, dimensions=(0.056, 0.056, 0.12),
                 motor_gains=(7.2, 7.2), traction=(1.0, 1.0), gyro_drift_deg_s=0.0,
                 quantization_deg=0.0):
        self.x, self.y, self.heading = pose
        self.initial_heading = pose[2]
        self.dimensions = dimensions
        self.motor_gains = motor_gains
        self.traction = traction
        self.gyro_drift = gyro_drift_deg_s
        self.quantization = quantization_deg
        self.angles = [0.0, 0.0]
        self.speeds = [0.0, 0.0]
        self.time = 0.0

    def _quantize(self, value_deg):
        if self.quantization <= 0:
            return value_deg
        sensor_counts = round(value_deg / self.quantization)
        return sensor_counts * self.quantization

    def sample(self):
        heading_change_deg = self.heading - self.initial_heading
        gyro_bias_deg = self.gyro_drift * self.time
        gyro_reading_deg = heading_change_deg + gyro_bias_deg
        left_reading_deg = self._quantize(self.angles[0])
        right_reading_deg = self._quantize(self.angles[1])
        gyro_reading_deg = self._quantize(gyro_reading_deg)
        return self.time, left_reading_deg, right_reading_deg, gyro_reading_deg

    def _advance_wheel(self, wheel_index, duty, elapsed_s, blocked):
        target_speed_deg_s = duty * self.motor_gains[wheel_index]
        previous_speed_deg_s = self.speeds[wheel_index]
        motor_response_fraction = 1 - math.exp(-elapsed_s / 0.08)
        speed_change_deg_s = (target_speed_deg_s - previous_speed_deg_s) * motor_response_fraction
        current_speed_deg_s = previous_speed_deg_s + speed_change_deg_s
        if blocked:
            current_speed_deg_s = 0.0
        self.speeds[wheel_index] = current_speed_deg_s
        encoder_change_deg = current_speed_deg_s * elapsed_s
        self.angles[wheel_index] += encoder_change_deg
        wheel_circumference_m = math.pi * self.dimensions[wheel_index]
        nominal_travel_m = encoder_change_deg * wheel_circumference_m / 360.0
        actual_travel_m = nominal_travel_m * self.traction[wheel_index]
        return actual_travel_m

    def _advance_pose(self, left_travel_m, right_travel_m):
        heading_change_rad = (right_travel_m - left_travel_m) / self.dimensions[2]
        midpoint_heading_rad = math.radians(self.heading) + heading_change_rad / 2.0
        center_travel_m = (left_travel_m + right_travel_m) / 2.0
        self.x += center_travel_m * math.cos(midpoint_heading_rad)
        self.y += center_travel_m * math.sin(midpoint_heading_rad)
        self.heading += math.degrees(heading_change_rad)

    def advance(self, left_duty, right_duty, dt=0.02, blocked=(False, False)):
        if dt <= 0:
            raise ValueError("Simulation dt must be positive")
        left_travel_m = self._advance_wheel(0, left_duty, dt, blocked[0])
        right_travel_m = self._advance_wheel(1, right_duty, dt, blocked[1])
        self._advance_pose(left_travel_m, right_travel_m)
        self.time += dt

    def pose(self):
        return self.x, self.y, wrap_degrees(self.heading)


def _create_demo(motor_gains, traction, gyro_drift_deg_s, quantization_deg):
    course = demo_course()
    robot_radius_m = 0.15
    position_allowance_m = 0.03
    planning_map = CourseMap(course, robot_radius_m, position_allowance_m)
    footprint_map = CourseMap(course, robot_radius_m, 0.0)
    route = plan(course, robot_radius_m, position_allowance_m, 0.1)
    start_x_m, start_y_m = course["start"]
    start_pose = (start_x_m, start_y_m, 0.0)
    robot = SimRobot(start_pose, motor_gains=motor_gains, traction=traction,
                     gyro_drift_deg_s=gyro_drift_deg_s, quantization_deg=quantization_deg)
    navigator = Navigator(robot.dimensions, start_pose, planning_map, demo_settings())
    navigator.step(*robot.sample())
    navigator.start(route)
    return course, footprint_map, route, robot, navigator


def _simulation_result(course, route, robot, output, peak_error_m, collisions, transitions):
    true_pose = robot.pose()
    true_goal_error_m = distance(true_pose, course["goal"])
    reached_goal_area = true_goal_error_m <= course["goal_radius"]
    route_completed = output["state"] == "DONE"
    passed_task_checks = route_completed and reached_goal_area and collisions == 0
    return {"state": output["state"], "reason": output["reason"], "time_s": robot.time,
            "simulation_pass": passed_task_checks, "estimated_pose": tuple(output["pose"]),
            "true_pose": true_pose, "true_goal_error_m": true_goal_error_m,
            "goal_radius_m": course["goal_radius"], "peak_position_error_m": peak_error_m,
            "clearance_violations": collisions, "transitions": transitions, "route": route}


def run_demo(motor_gains=(7.2, 7.2), traction=(1.0, 1.0), gyro_drift_deg_s=0.0,
             max_steps=16000, record=None, quantization_deg=0.0):
    course, footprint_map, route, robot, navigator = _create_demo(
        motor_gains, traction, gyro_drift_deg_s, quantization_deg)
    output = {"left_duty": 0, "right_duty": 0}
    collisions = 0
    peak_error_m = 0.0
    transitions = []
    previous_state = None
    for step_index in range(max_steps):
        previous_position = robot.pose()
        robot.advance(output["left_duty"], output["right_duty"])
        if not footprint_map.segment_clear(previous_position, robot.pose()):
            collisions += 1
        output = navigator.step(*robot.sample())
        position_error_m = distance(output["pose"], robot.pose())
        peak_error_m = max(peak_error_m, position_error_m)
        if output["state"] != previous_state:
            transitions.append((robot.time, output["state"]))
            previous_state = output["state"]
        if record is not None:
            record(robot, output)
        if output["state"] in navigator.TERMINAL:
            break
    else:
        output = navigator.abort("simulation step limit")
    return _simulation_result(course, route, robot, output, peak_error_m, collisions, transitions)
