"""Our control math; gains require bench calibration before use on the EV3."""
import math
from geometry import wrap_degrees


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def heading_rate(target_deg, actual_deg, kp, max_rate_rad_s):
    if kp < 0 or max_rate_rad_s <= 0:
        raise ValueError("Invalid heading-controller limits")
    error = math.radians(wrap_degrees(target_deg - actual_deg))
    return clamp(kp * error, -max_rate_rad_s, max_rate_rad_s)


def wheel_targets(speed_m_s, yaw_rad_s, track_m, left_diameter_m, right_diameter_m):
    if min(track_m, left_diameter_m, right_diameter_m) <= 0:
        raise ValueError("Measured dimensions must be positive")
    return ((speed_m_s - yaw_rad_s * track_m / 2) * 360 / (math.pi * left_diameter_m),
            (speed_m_s + yaw_rad_s * track_m / 2) * 360 / (math.pi * right_diameter_m))


class WheelPI:
    """Wheel speed (deg/s) -> raw duty (%), with conditional anti-windup."""
    def __init__(self, kp, ki, limit):
        if kp < 0 or ki < 0 or not 0 < limit <= 100:
            raise ValueError("Invalid wheel-controller gains/limit")
        self.kp, self.ki, self.limit = kp, ki, limit
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def update(self, target_deg_s, actual_deg_s, dt_s):
        if dt_s <= 0:
            raise ValueError("Controller dt must be positive")
        error = target_deg_s - actual_deg_s
        candidate = self.integral + error * dt_s
        raw = self.kp * error + self.ki * candidate
        if abs(raw) <= self.limit or raw * error < 0:
            self.integral = candidate
        return clamp(self.kp * error + self.ki * self.integral, -self.limit, self.limit)
