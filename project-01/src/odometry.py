"""Incremental differential-drive odometry; no hardware or framework imports."""
import math
from geometry import wrap_degrees


class Odometry:
    def __init__(self, left_diameter, right_diameter, track, start_pose=(0, 0, 0)):
        if min(left_diameter, right_diameter, track) <= 0:
            raise ValueError("Measured dimensions must be positive")
        self.left_scale = math.pi * left_diameter / 360.0
        self.right_scale = math.pi * right_diameter / 360.0
        self.track = track
        self.x, self.y, self.heading = start_pose
        self.previous = None
        self.gyro_offset = None
        self.encoder_heading_change = 0.0

    def update(self, left_angle, right_angle, gyro_angle):
        """Angles in degrees, forward-positive wheels, CCW-positive gyro.

        Initial sample establishes baselines without resetting devices. Gyro
        angles must be continuous; a sensor reset during travel invalidates pose.
        """
        if self.previous is None:
            self.previous = (left_angle, right_angle)
            self.gyro_offset = self.heading - gyro_angle
            return self.pose()
        dl = (left_angle - self.previous[0]) * self.left_scale
        dr = (right_angle - self.previous[1]) * self.right_scale
        new_heading = gyro_angle + self.gyro_offset
        midpoint = math.radians((self.heading + new_heading) / 2.0)
        ds = (dl + dr) / 2.0
        self.x += ds * math.cos(midpoint)
        self.y += ds * math.sin(midpoint)
        self.encoder_heading_change = math.degrees((dr - dl) / self.track)
        self.heading = new_heading
        self.previous = (left_angle, right_angle)
        return self.pose()

    def pose(self):
        return (self.x, self.y, wrap_degrees(self.heading))

    def sensor_position(self, forward, left):
        angle = math.radians(self.heading)
        return (self.x + forward * math.cos(angle) - left * math.sin(angle),
                self.y + forward * math.sin(angle) + left * math.cos(angle))
