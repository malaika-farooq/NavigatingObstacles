"""Offline closed-loop and failure-injection tests; no robot connection."""
import ast
from pathlib import Path
import sys
import unittest
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from navigation import Navigator
from planner import CourseMap, demo_course
from simulation import SimRobot, demo_settings, run_demo


class NavigationTests(unittest.TestCase):
    def make_controller(self, changes=None, route=None):
        settings = demo_settings()
        if changes:
            settings.update(changes)
        start = (0.4, 1.0, 0.0)
        robot = SimRobot(start)
        nav = Navigator(robot.dimensions, start, CourseMap(demo_course(), 0.15, 0.03), settings)
        nav.step(*robot.sample())
        nav.start(route or [(0.4, 1.0), (0.4, 1.6)])
        return nav, robot

    def assert_stopped(self, output, reason=None):
        self.assertEqual(output["state"], "ABORTED")
        self.assertFalse(output["pose_valid"])
        self.assertEqual((output["left_duty"], output["right_duty"]), (0, 0))
        if reason:
            self.assertIn(reason, output["reason"])

    def test_closed_loop_obstacle_route_with_settling(self):
        result = run_demo()
        self.assertTrue(result["simulation_pass"])
        states = [s for unused, s in result["transitions"]]
        self.assertIn("TURN", states)
        self.assertIn("DRIVE", states)
        self.assertIn("SETTLE", states)
        self.assertEqual(states[-1], "DONE")

    def test_unequal_motor_response_is_corrected(self):
        result = run_demo(motor_gains=(6.0, 8.0))
        self.assertTrue(result["simulation_pass"])
        self.assertEqual(result["clearance_violations"], 0)

    def test_integer_degree_sensors(self):
        result = run_demo(quantization_deg=1)
        self.assertTrue(result["simulation_pass"])

    def test_equal_wheel_slip_is_not_hidden_by_reported_completion(self):
        result = run_demo(traction=(0.85, 0.85))
        self.assertEqual(result["state"], "DONE")
        self.assertFalse(result["simulation_pass"])
        self.assertGreater(result["peak_position_error_m"], 0.1)
        self.assertGreater(result["true_goal_error_m"], 0.1)

    def test_gyro_drift_can_defeat_position_estimate(self):
        result = run_demo(gyro_drift_deg_s=0.1)
        self.assertTrue(result["simulation_pass"])
        self.assertGreater(result["peak_position_error_m"], 0.05)
        self.assertLess(result["true_goal_error_m"], result["goal_radius_m"])

    def test_operator_abort_is_terminal(self):
        nav, robot = self.make_controller()
        output = nav.step(0.02, 0, 0, 0, abort=True)
        self.assert_stopped(output, "operator")
        self.assert_stopped(nav.step(0.04, 10, 10, 0))
        with self.assertRaises(ValueError):
            nav.start([(0.4, 1.2)])

    def test_delayed_sample_invalidates_pose(self):
        nav, unused = self.make_controller()
        self.assert_stopped(nav.step(1, 0, 0, 0), "timing")

    def test_duplicate_and_backwards_time(self):
        for timestamp in (0, -1):
            nav, unused = self.make_controller()
            self.assert_stopped(nav.step(timestamp, 0, 0, 0), "timing")

    def test_invalid_numeric_sample(self):
        for value in (float("nan"), float("inf"), None):
            nav, unused = self.make_controller()
            self.assert_stopped(nav.step(0.02, value, 0, 0), "nonfinite")

    def test_sensor_discontinuity(self):
        nav, unused = self.make_controller()
        self.assert_stopped(nav.step(0.02, 0, 0, 90), "gyro")
        nav, unused = self.make_controller()
        self.assert_stopped(nav.step(0.02, 1000, 0, 0), "encoder")

    def test_blocked_wheels_abort(self):
        nav, robot = self.make_controller()
        output = {"left_duty": 0, "right_duty": 0}
        for unused in range(150):
            robot.advance(output["left_duty"], output["right_duty"], blocked=(True, True))
            output = nav.step(*robot.sample())
            if output["state"] == "ABORTED":
                break
        self.assert_stopped(output, "stalled")

    def test_leg_and_route_timeouts(self):
        for key in ("leg_timeout_s", "route_timeout_s"):
            nav, robot = self.make_controller({key: 0.3})
            for unused in range(20):
                robot.advance(0, 0)
                output = nav.step(*robot.sample())
                if output["state"] == "ABORTED":
                    break
            self.assert_stopped(output, "timeout")

    def test_invalid_route_does_not_start(self):
        start = (0.4, 1.0, 0)
        nav = Navigator((0.056, 0.056, 0.12), start,
                        CourseMap(demo_course(), 0.15, 0.03), demo_settings())
        nav.step(0, 0, 0, 0)
        for route in ([], [(2.6, 1)], [(float("nan"), 0.4)], [(0.01, 1)]):
            with self.assertRaises(ValueError):
                nav.start(route)
            self.assertEqual(nav.state, "IDLE")

    def test_duty_limit_is_enforced_for_entire_route(self):
        outputs = []
        run_demo(record=lambda robot, output: outputs.append(dict(output)))
        self.assertTrue(all(abs(o["left_duty"]) <= 25 and abs(o["right_duty"]) <= 25 for o in outputs))
        self.assertEqual((outputs[-1]["left_duty"], outputs[-1]["right_duty"]), (0, 0))

    def test_single_blocked_wheel_stops_route(self):
        nav, robot = self.make_controller()
        output = {"left_duty": 0, "right_duty": 0}
        for unused in range(300):
            robot.advance(output["left_duty"], output["right_duty"], blocked=(True, False))
            output = nav.step(*robot.sample())
            if output["state"] == "ABORTED":
                break
        self.assert_stopped(output)
        self.assertTrue("stalled" in output["reason"] or "disagree" in output["reason"])

    def test_gradual_sensor_disagreement(self):
        nav, unused = self.make_controller()
        for i in range(1, 30):
            output = nav.step(i*0.02, 0, 0, i)
            if output["state"] == "ABORTED":
                break
        self.assert_stopped(output, "disagree")

    def test_corrective_segment_is_checked_against_map(self):
        nav, unused = self.make_controller()
        nav.world.boxes.append((0.3, 1.25, 0.5, 1.35))
        self.assert_stopped(nav.step(0.02, 0, 0, 0), "corrective segment")

    def test_invalid_settings_are_rejected(self):
        for changes in ({"max_duty": 101}, {"wheel_kp": float("nan")}, {"max_gap_s": 0}):
            with self.assertRaises(ValueError):
                self.make_controller(changes)

    def test_result_and_pose_buffers_are_reused(self):
        navigator, unused = self.make_controller()
        first_result = navigator.step(0.02, 0, 0, 0)
        first_pose_buffer = first_result["pose"]
        saved_pose = tuple(first_pose_buffer)
        second_result = navigator.step(0.04, -1, 1, 1)
        self.assertIs(first_result, second_result)
        self.assertIs(first_pose_buffer, second_result["pose"])
        self.assertNotEqual(saved_pose[2], second_result["pose"][2])

    def test_gc_runs_at_stopped_transition_not_each_tick(self):
        navigator, unused = self.make_controller(route=[(0.4, 1), (0.8, 1)])
        with mock.patch("navigation.gc.collect") as collect:
            for sample_index in range(1, 21):
                output = navigator.step(sample_index * 0.02, 0, 0, 0)
            self.assertEqual(output["state"], "DRIVE")
            self.assertEqual(collect.call_count, 1)

    def test_gc_is_not_forced_while_turning(self):
        navigator, robot = self.make_controller()
        output = {"left_duty": 0, "right_duty": 0}
        with mock.patch("navigation.gc.collect") as collect:
            for sample_index in range(25):
                robot.advance(output["left_duty"], output["right_duty"])
                output = navigator.step(*robot.sample())
            self.assertEqual(output["state"], "TURN")
            collect.assert_not_called()

    def test_old_python_syntax_compatibility(self):
        for path in SRC.glob("*.py"):
            ast.parse(path.read_text(), filename=str(path), feature_version=(3, 4))


if __name__ == "__main__":
    unittest.main()
