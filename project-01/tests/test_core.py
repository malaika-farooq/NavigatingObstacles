"""Host-side behavioral tests; no robot libraries or robot connection needed."""
from pathlib import Path
import ast
import math
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import config
import hardware
from geometry import segment_hits_box, wrap_degrees
from control import WheelPI, heading_rate, wheel_targets
from motion import next_segment
from odometry import Odometry
from planner import CourseMap, demo_course, plan, simplify


class PlannerTests(unittest.TestCase):
    def test_obstacle_detour_checks_every_segment(self):
        course = demo_course()
        path = plan(course, 0.15, 0.03, 0.1)
        self.assertEqual(path[0], course["start"])
        self.assertEqual(path[-1], course["goal"])
        self.assertGreater(len(path), 2)
        world = CourseMap(course, 0.15, 0.03)
        self.assertTrue(all(world.segment_clear(a, b) for a, b in zip(path, path[1:])))

    def test_wall_blocks_course(self):
        course = demo_course()
        course["obstacles"] = [(1.5, y / 10) for y in range(0, 21, 2)]
        with self.assertRaises(ValueError):
            plan(course, 0.15, 0.03, 0.1)

    def test_boundary_start_is_rejected(self):
        course = demo_course()
        course["start"] = (0.1, 1)
        with self.assertRaises(ValueError):
            plan(course, 0.15, 0.03, 0.1)

    def test_edge_collision_between_clear_endpoints(self):
        self.assertTrue(segment_hits_box((0, 0), (2, 0), (0.9, -0.1, 1.1, 0.1)))
        self.assertTrue(segment_hits_box((0, 0.1), (2, 0.1), (0.9, -0.1, 1.1, 0.1)))
        self.assertFalse(segment_hits_box((0, 1), (2, 1), (0.9, -0.1, 1.1, 0.1)))

    def test_clear_course_retains_exact_endpoints(self):
        course = demo_course()
        course["obstacles"] = []
        self.assertEqual(plan(course, 0.15, 0.03, 0.1), [course["start"], course["goal"]])

    def test_simplification_keeps_reversal(self):
        self.assertEqual(simplify([(0, 0), (1, 0), (0, 0)]), [(0, 0), (1, 0), (0, 0)])


class OdometryTests(unittest.TestCase):
    def test_first_sample_does_not_move_pose(self):
        odo = Odometry(0.1, 0.1, 0.2, (1, 2, 90))
        self.assertEqual(odo.update(700, -80, 35), (1, 2, 90))

    def test_known_forward_and_reverse_motion(self):
        odo = Odometry(0.1, 0.1, 0.2)
        odo.update(100, 100, 0)
        self.assertAlmostEqual(odo.update(460, 460, 0)[0], math.pi * 0.1)
        self.assertAlmostEqual(odo.update(100, 100, 0)[0], 0)

    def test_in_place_turn_and_sensor_offset(self):
        odo = Odometry(0.1, 0.1, 0.2)
        odo.update(0, 0, 0)
        x, y, heading = odo.update(-180, 180, 90)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 0)
        self.assertEqual(heading, 90)
        lens = odo.sensor_position(0.1, 0.02)
        self.assertAlmostEqual(lens[0], -0.02)
        self.assertAlmostEqual(lens[1], 0.1)

    def test_continuous_heading_crosses_360(self):
        odo = Odometry(0.1, 0.1, 0.2, (0, 0, 359))
        odo.update(0, 0, 359)
        x, y, heading = odo.update(36, 36, 361)
        self.assertGreater(x, 0)
        self.assertAlmostEqual(y, 0)
        self.assertEqual(heading, 1)


class ControllerTests(unittest.TestCase):
    def test_left_turn_wheel_signs(self):
        left, right = wheel_targets(0, 1, 0.2, 0.1, 0.1)
        self.assertLess(left, 0)
        self.assertGreater(right, 0)
        self.assertGreater(heading_rate(1, 359, 1, 1), 0)
        self.assertEqual(wrap_degrees(359), -1)

    def test_pi_saturation_does_not_accumulate_integral(self):
        controller = WheelPI(1, 1, 20)
        for unused in range(100):
            self.assertEqual(controller.update(100, 0, 0.02), 20)
        self.assertEqual(controller.integral, 0)
        self.assertEqual(controller.update(0, 0, 0.02), 0)

    def test_segment_uses_current_pose(self):
        heading, length = next_segment((1, 1, 0), (1, 2))
        self.assertEqual((heading, length), (90, 1))


class HardwareBoundaryTests(unittest.TestCase):
    def test_discovery_uses_address_not_device_number(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, port in [("motor7", "outA"), ("motor1", "outB")]:
                device = root / name
                device.mkdir()
                (device / "address").write_text("ev3-ports:" + port)
                (device / "driver_name").write_text("lego-ev3-l-motor")
            path = hardware.find(directory, "outA", "lego-ev3-l-motor")
            self.assertEqual(Path(path).name, "motor7")

    def test_motion_is_blocked_by_unmeasured_config(self):
        with self.assertRaises(ValueError):
            config.require_motion_calibration()

    def test_robot_imports_are_builtin_only(self):
        allowed = {"os", "sys", "time", "math"} | {p.stem for p in SRC.glob("*.py")}
        for path in SRC.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [name.name.split(".")[0] for name in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [(node.module or "").split(".")[0]]
                else:
                    continue
                for module in modules:
                    self.assertIn(module, allowed, str(path))


if __name__ == "__main__":
    unittest.main()
