"""Encoder distance and gyro heading, referenced to the drive-wheel midpoint."""
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
        self.previous_left_angle = None
        self.previous_right_angle = None
        self.gyro_offset = None
        self.encoder_heading_change = 0.0

    def _set_baseline(self, left_angle, right_angle, gyro_angle):
        self.previous_left_angle = left_angle
        self.previous_right_angle = right_angle
        self.gyro_offset = self.heading - gyro_angle

    def _integrate_travel(self, left_distance_m, right_distance_m, new_heading_deg):
        midpoint_heading_deg = (self.heading + new_heading_deg) / 2.0
        midpoint_heading_rad = math.radians(midpoint_heading_deg)
        center_distance_m = (left_distance_m + right_distance_m) / 2.0
        heading_change_rad = (right_distance_m - left_distance_m) / self.track
        self.x += center_distance_m * math.cos(midpoint_heading_rad)
        self.y += center_distance_m * math.sin(midpoint_heading_rad)
        self.encoder_heading_change = math.degrees(heading_change_rad)
        self.heading = new_heading_deg

    def update(self, left_angle, right_angle, gyro_angle, output=None):
        """Forward-positive encoders and continuous CCW-positive gyro, in degrees.

        First sample establishes a baseline without resetting devices. Supplying
        output reuses a three-value buffer instead of allocating a pose tuple.
        """
        if self.previous_left_angle is None:
            self._set_baseline(left_angle, right_angle, gyro_angle)
        else:
            left_change_deg = left_angle - self.previous_left_angle
            right_change_deg = right_angle - self.previous_right_angle
            left_distance_m = left_change_deg * self.left_scale
            right_distance_m = right_change_deg * self.right_scale
            new_heading_deg = gyro_angle + self.gyro_offset
            self._integrate_travel(left_distance_m, right_distance_m, new_heading_deg)
            self.previous_left_angle = left_angle
            self.previous_right_angle = right_angle
        if output is not None:
            return self.pose_into(output)
        return self.pose()

    def pose_into(self, output):
        output[0] = self.x
        output[1] = self.y
        output[2] = wrap_degrees(self.heading)
        return output

    def pose(self):
        return self.x, self.y, wrap_degrees(self.heading)

    def sensor_position(self, forward, left):
        heading_rad = math.radians(self.heading)
        forward_x_m = forward * math.cos(heading_rad)
        forward_y_m = forward * math.sin(heading_rad)
        left_x_m = -left * math.sin(heading_rad)
        left_y_m = left * math.cos(heading_rad)
        sensor_x_m = self.x + forward_x_m + left_x_m
        sensor_y_m = self.y + forward_y_m + left_y_m
        return sensor_x_m, sensor_y_m
