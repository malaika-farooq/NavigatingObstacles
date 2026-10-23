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

    def test_pdf_course_input_matches_header(self):
        import course
        self.assertEqual(len(course.obstacle_centers_m()), 13)
        self.assertAlmostEqual(course.workspace_m()[0], 4.88)
        self.assertEqual(config.course()["goal"], (3.658, 1.829))

    def test_pdf_course_plans_with_footprint_clearance(self):
        for radius_m in (0.10, 0.13, 0.16):
            path = plan(config.course(), radius_m, 0.05, config.GRID_SPACING_M)
            world = CourseMap(config.course(), radius_m, 0.05)
            self.assertEqual(path[0], config.course()["start"])
            self.assertEqual(path[-1], config.course()["goal"])
            self.assertTrue(all(world.segment_clear(a, b) for a, b in zip(path, path[1:])))

    def test_wavefront_is_zero_at_goal_and_decreases_by_one(self):
        from planner import CourseMap as Map, _build_grid, wavefront
        world = Map(config.course(), 0.13, 0.05)
        nodes = _build_grid(world, 0.1525, 10000)
        goal_cell = (24, 12)
        potential = wavefront(world, nodes, [goal_cell])
        self.assertEqual(potential[goal_cell], 0)
        for cell, value in potential.items():
            if value > 0:
                lower = [potential.get((cell[0] + dx, cell[1] + dy))
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                self.assertIn(value - 1, lower)

    def test_route_segments_are_axis_aligned_between_grid_cells(self):
        path = plan(config.course(), 0.13, 0.05, 0.1525)
        inner = path[1:-1]
        for a, b in zip(inner, inner[1:]):
            self.assertTrue(abs(a[0] - b[0]) < 1e-9 or abs(a[1] - b[1]) < 1e-9)

    def test_padding_inside_count_is_rejected(self):
        import course
        saved_count = course.num_obstacles
        course.num_obstacles = 14
        try:
            with self.assertRaises(ValueError):
                course.obstacle_centers_m()
        finally:
            course.num_obstacles = saved_count

    def test_endpoint_connectors_bypass_an_isolated_nearest_cell(self):
        course = {"workspace": (1.5, 1.5), "start": (1.091, 0.743),
                  "goal": (0.320, 1.243), "obstacles": [(0.291, 0.915), (0.631, 1.297)],
                  "obstacle_side": 0.18, "goal_radius": 0.1}
        # Exercise both an isolated goal cell and the reversed start case.
        for start, goal in ((course["start"], course["goal"]),
                            (course["goal"], course["start"])):
            course["start"], course["goal"] = start, goal
            path = plan(course, 0.06, 0.01, 0.15)
            world = CourseMap(course, 0.06, 0.01)
            self.assertEqual(path[0], start)
            self.assertEqual(path[-1], goal)
            self.assertTrue(all(world.segment_clear(a, b) for a, b in zip(path, path[1:])))

    def test_nearby_corner_is_preserved_to_avoid_cutting_obstacle(self):
        from planner import _without_repeats
        course = {"workspace": (1.0, 1.0), "obstacles": [(0.5, 0.5)],
                  "obstacle_side": 0.18}
        world = CourseMap(course, 0.01, 0.0)
        points = [(0.399, 0.401), (0.399, 0.399), (0.401, 0.399)]
        self.assertFalse(world.segment_clear(points[0], points[-1]))
        path = simplify(_without_repeats(points))
        self.assertTrue(all(world.segment_clear(a, b) for a, b in zip(path, path[1:])))

    def test_heading_is_optional_for_planning_but_required_for_motion(self):
        from unittest import mock
        # Supply the other calibration values to isolate the heading gate.
        with mock.patch.multiple(config, WHEEL_TRACK_M=0.12, FOOTPRINT_RADIUS_M=0.13,
                                 CALIBRATED=True, START_POSE=(0.305, 1.219, None)):
            self.assertTrue(plan(config.course(), 0.13, 0.05, 0.1525))
            with self.assertRaisesRegex(ValueError, "start_heading_deg"):
                config.require_motion_calibration()
            config.START_POSE = (0.305, 1.219, 90.0)
            config.require_motion_calibration()

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
    def test_black_detection_uses_calibrated_boundary(self):
        threshold = config.COLOR_BLACK_THRESHOLD_PERCENT
        self.assertTrue(hardware.reflection_is_black(1, threshold))
        self.assertTrue(hardware.reflection_is_black(29, threshold))
        self.assertFalse(hardware.reflection_is_black(30, threshold))
        self.assertFalse(hardware.reflection_is_black(57, threshold))

    def test_black_detection_rejects_invalid_samples_and_thresholds(self):
        for invalid in (-1, 101, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                hardware.reflection_is_black(invalid, 29)
            with self.assertRaises(ValueError):
                hardware.reflection_is_black(1, invalid)

    def test_color_detection_reads_reflection_without_changing_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mode").write_text("COL-REFLECT")
            (root / "decimals").write_text("0")
            (root / "value0").write_text("1")
            sensor = hardware.ColorSensor.__new__(hardware.ColorSensor)
            sensor.path = directory
            self.assertTrue(sensor.is_black(29))
            (root / "value0").write_text("57")
            self.assertFalse(sensor.is_black(29))
            (root / "mode").write_text("COL-COLOR")
            with self.assertRaises(ValueError):
                sensor.is_black(29)
            self.assertEqual((root / "mode").read_text(), "COL-COLOR")

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
        allowed = {"os", "sys", "time", "math", "gc"} | {p.stem for p in SRC.glob("*.py")}
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
