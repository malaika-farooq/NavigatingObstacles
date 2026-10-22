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

    def sample(self):
        values = (self.angles[0], self.angles[1], self.heading-self.initial_heading+self.gyro_drift*self.time)
        if self.quantization > 0:
            values = tuple(round(v/self.quantization)*self.quantization for v in values)
        return (self.time,) + values

    def advance(self, left_duty, right_duty, dt=0.02, blocked=(False, False)):
        if dt <= 0:
            raise ValueError("Simulation dt must be positive")
        travel = []
        for i, duty in enumerate((left_duty, right_duty)):
            target = duty*self.motor_gains[i]
            self.speeds[i] += (target-self.speeds[i]) * (1-math.exp(-dt/0.08))
            if blocked[i]:
                self.speeds[i] = 0.0
            delta = self.speeds[i]*dt
            self.angles[i] += delta
            travel.append(delta*math.pi*self.dimensions[i]/360*self.traction[i])
        yaw = (travel[1]-travel[0])/self.dimensions[2]
        middle = math.radians(self.heading)+yaw/2
        ds = (travel[0]+travel[1])/2
        self.x += ds*math.cos(middle)
        self.y += ds*math.sin(middle)
        self.heading += math.degrees(yaw)
        self.time += dt

    def pose(self):
        return (self.x, self.y, wrap_degrees(self.heading))


def run_demo(motor_gains=(7.2, 7.2), traction=(1.0, 1.0), gyro_drift_deg_s=0.0,
             max_steps=16000, record=None, quantization_deg=0.0):
    course = demo_course()
    world = CourseMap(course, 0.15, 0.03)
    route = plan(course, 0.15, 0.03, 0.1)
    start = (course["start"][0], course["start"][1], 0.0)
    robot = SimRobot(start, motor_gains=motor_gains, traction=traction, gyro_drift_deg_s=gyro_drift_deg_s,
                     quantization_deg=quantization_deg)
    nav = Navigator(robot.dimensions, start, world, demo_settings())
    nav.step(*robot.sample())
    nav.start(route)
    output = {"left_duty": 0, "right_duty": 0}
    collisions = 0
    peak_error = 0.0
    transitions = []
    previous_state = None
    for unused in range(max_steps):
        old_position = robot.pose()[:2]
        robot.advance(output["left_duty"], output["right_duty"])
        # Independent truth check: the estimator cannot see all simulated slip.
        if not world.segment_clear(old_position, robot.pose()[:2]):
            collisions += 1
        output = nav.step(*robot.sample())
        peak_error = max(peak_error, distance(output["pose"], robot.pose()))
        if output["state"] != previous_state:
            transitions.append((robot.time, output["state"]))
            previous_state = output["state"]
        if record is not None:
            record(robot, output)
        if output["state"] in nav.TERMINAL:
            break
    else:
        output = nav.abort("simulation step limit")
    success = (output["state"] == "DONE" and collisions == 0 and
               distance(robot.pose(), course["goal"]) <= nav.settings["position_tolerance_m"])
    return {"state": output["state"], "reason": output["reason"], "time_s": robot.time,
            "simulation_pass": success,
            "estimated_pose": output["pose"], "true_pose": robot.pose(),
            "true_goal_error_m": distance(robot.pose(), course["goal"]),
            "peak_position_error_m": peak_error, "clearance_violations": collisions,
            "transitions": transitions, "route": route}
