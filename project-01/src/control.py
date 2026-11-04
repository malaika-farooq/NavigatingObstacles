"""Wheel and heading control calculations; gains require physical calibration."""
import math
from geometry import wrap_degrees


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def heading_rate(target_deg, actual_deg, kp, max_rate_rad_s):
    if kp < 0 or max_rate_rad_s <= 0:
        raise ValueError("Invalid heading-controller limits")
    heading_error_deg = wrap_degrees(target_deg - actual_deg)
    heading_error_rad = math.radians(heading_error_deg)
    requested_yaw_rad_s = kp * heading_error_rad
    return clamp(requested_yaw_rad_s, -max_rate_rad_s, max_rate_rad_s)


def wheel_targets(speed_m_s, yaw_rad_s, track_m, left_diameter_m, right_diameter_m, output=None):
    if min(track_m, left_diameter_m, right_diameter_m) <= 0:
        raise ValueError("Measured dimensions must be positive")
    turn_speed_m_s = yaw_rad_s * track_m / 2.0
    left_speed_m_s = speed_m_s - turn_speed_m_s
    right_speed_m_s = speed_m_s + turn_speed_m_s
    left_circumference_m = math.pi * left_diameter_m
    right_circumference_m = math.pi * right_diameter_m
    left_speed_deg_s = left_speed_m_s * 360.0 / left_circumference_m
    right_speed_deg_s = right_speed_m_s * 360.0 / right_circumference_m
    if output is None:
        return left_speed_deg_s, right_speed_deg_s
    output[0] = left_speed_deg_s
    output[1] = right_speed_deg_s
    return output


class WheelPI:
    """Wheel speed (deg/s) to bounded raw duty (%), with anti-windup."""
    def __init__(self, kp, ki, limit):
        if kp < 0 or ki < 0 or not 0 < limit <= 100:
            raise ValueError("Invalid wheel-controller gains/limit")
        self.kp = kp
        self.ki = ki
        self.limit = limit
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def update(self, target_deg_s, actual_deg_s, dt_s):
        if dt_s <= 0:
            raise ValueError("Controller dt must be positive")
        speed_error_deg_s = target_deg_s - actual_deg_s
        candidate_integral = self.integral + speed_error_deg_s * dt_s
        proportional_duty = self.kp * speed_error_deg_s
        candidate_duty = proportional_duty + self.ki * candidate_integral
        within_output_limit = abs(candidate_duty) <= self.limit
        reduces_saturation = candidate_duty * speed_error_deg_s < 0
        if within_output_limit or reduces_saturation:
            self.integral = candidate_integral
        requested_duty = proportional_duty + self.ki * self.integral
        return clamp(requested_duty, -self.limit, self.limit)
