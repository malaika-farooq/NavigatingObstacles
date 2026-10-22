"""Small on-brick compatibility/logic check. No hardware imports or outputs."""
import math
from geometry import segment_hits_box, wrap_degrees
from odometry import Odometry
from planner import CourseMap, demo_course, plan
from control import WheelPI, heading_rate, wheel_targets
from motion import next_segment


def run():
    assert wrap_degrees(359) == -1
    assert segment_hits_box((0, 0), (2, 0), (0.9, -0.1, 1.1, 0.1))
    assert not segment_hits_box((0, 1), (2, 1), (0.9, -0.1, 1.1, 0.1))
    odo = Odometry(0.1, 0.1, 0.2, (1, 1, 90))
    odo.update(0, 0, 0)
    x, y, angle = odo.update(360, 360, 0)
    assert abs(x-1) < 1e-8 and abs(y-1-math.pi*0.1) < 1e-8
    assert angle == 90
    course = demo_course()
    path = plan(course, 0.15, 0.03, 0.1)
    world = CourseMap(course, 0.15, 0.03)
    assert len(path) > 2
    assert all(world.segment_clear(a, b) for a, b in zip(path, path[1:]))
    left, right = wheel_targets(0, 1, 0.2, 0.1, 0.1)
    assert left < 0 < right
    assert heading_rate(1, 359, 1, 1) > 0
    assert WheelPI(1, 1, 20).update(100, 0, 0.02) == 20
    assert next_segment((0, 0, 0), (0, 1)) == (90, 1)
    print("SELFTEST PASS: geometry, odometry, planner, control; no motor outputs")
