"""Geometry shared by obstacle checks, odometry and steering."""
import math

NUMBER_TYPES = (int, float)
INFINITY = float("inf")


def finite(value):
    is_number = isinstance(value, NUMBER_TYPES)
    if not is_number:
        return False
    is_nan = value != value
    is_infinite = abs(value) == INFINITY
    return not is_nan and not is_infinite


def wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


def distance(start, end):
    difference_x = end[0] - start[0]
    difference_y = end[1] - start[1]
    squared_distance = difference_x * difference_x + difference_y * difference_y
    return math.sqrt(squared_distance)


def segment_hits_box(start, end, box):
    """Closed segment/axis-aligned-box intersection; touching is a collision."""
    entry_fraction = 0.0
    exit_fraction = 1.0
    for axis in (0, 1):
        segment_change = end[axis] - start[axis]
        minimum_coordinate = box[axis]
        maximum_coordinate = box[axis + 2]
        if abs(segment_change) < 1e-12:
            outside_axis = start[axis] < minimum_coordinate or start[axis] > maximum_coordinate
            if outside_axis:
                return False
            continue
        first_crossing = (minimum_coordinate - start[axis]) / segment_change
        second_crossing = (maximum_coordinate - start[axis]) / segment_change
        axis_entry = min(first_crossing, second_crossing)
        axis_exit = max(first_crossing, second_crossing)
        entry_fraction = max(entry_fraction, axis_entry)
        exit_fraction = min(exit_fraction, axis_exit)
        if entry_fraction > exit_fraction:
            return False
    return True
