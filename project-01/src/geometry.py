"""Small geometry functions shared by planning, odometry and control."""
import math


def finite(value):
    return isinstance(value, (int, float)) and value == value and abs(value) != float("inf")


def wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def segment_hits_box(a, b, box):
    """Closed segment/AABB intersection; touching counts as collision."""
    low, high = 0.0, 1.0
    for axis in (0, 1):
        delta = b[axis] - a[axis]
        minimum, maximum = box[axis], box[axis + 2]
        if abs(delta) < 1e-12:
            if a[axis] < minimum or a[axis] > maximum:
                return False
        else:
            t1 = (minimum - a[axis]) / delta
            t2 = (maximum - a[axis]) / delta
            low = max(low, min(t1, t2))
            high = min(high, max(t1, t2))
            if low > high:
                return False
    return True
