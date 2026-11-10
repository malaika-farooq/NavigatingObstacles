"""Failure-path checks for sensor diagnostics; no real device access."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import hardware
import main as diagnostics


class DiagnosticTests(unittest.TestCase):
    def test_laptop_logger_captures_brickrun_stderr_as_json_lines(self):
        path = Path(__file__).resolve().parents[1] / "scripts" / "ev3.py"
        spec = importlib.util.spec_from_file_location("laptop_ev3", path)
        laptop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(laptop)
        process = mock.Mock(stdout=iter(['{"event":"sample"}\n', 'brickrun message\n']))
        process.wait.return_value = 0
        with tempfile.TemporaryDirectory() as directory, \
             mock.patch.object(laptop, "PROJECT", Path(directory)), \
             mock.patch.object(laptop.subprocess, "Popen", return_value=process) as popen, \
             mock.patch("builtins.print"):
            laptop.run_logged("fake-host", "inspect", [])
            log = next((Path(directory) / "logs").glob("*.jsonl"))
            records = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(records[0], {"event": "sample"})
            self.assertEqual(records[1]["event"], "diagnostic")
            self.assertEqual(popen.call_args.kwargs["stderr"], laptop.subprocess.STDOUT)

    def test_color_mode_writer_rejects_motor(self):
        motor = {"path": "/sys/class/tacho-motor/motor0", "driver": "lego-ev3-m-motor"}
        with mock.patch.object(hardware, "discover", return_value=[]), mock.patch("builtins.open") as opened:
            with self.assertRaises(ValueError):
                hardware.select_color_mode(motor, "RGB-RAW")
            opened.assert_not_called()

    def test_read_failure_restores_original_mode(self):
        color = {"path": "fake", "driver": "lego-ev3-color"}
        idle = {"sensors": [], "motors": []}
        with mock.patch.object(diagnostics, "snapshot", side_effect=[idle, OSError("unplugged"), idle]), \
             mock.patch.object(diagnostics, "color_device", return_value=color), \
             mock.patch.object(diagnostics, "read", return_value="COL-AMBIENT"), \
             mock.patch.object(diagnostics, "select_color_mode") as select, \
             mock.patch.object(diagnostics, "emit"), \
             mock.patch.object(diagnostics.time, "sleep"):
            with self.assertRaises(OSError):
                diagnostics.monitor(1, 0.1, "rgb")
            self.assertEqual(select.call_args_list,
                             [mock.call(color, "RGB-RAW"), mock.call(color, "COL-AMBIENT")])

    def test_nonidle_motor_prevents_sensor_mode_change(self):
        running = {"motors": [{"address": "ev3-ports:outD", "speed": 10, "state": "running"}]}
        with mock.patch.object(diagnostics, "snapshot", return_value=running), \
             mock.patch.object(diagnostics, "select_color_mode") as select:
            with self.assertRaises(RuntimeError):
                diagnostics.monitor(1, 0.1, "rgb")
            select.assert_not_called()


if __name__ == "__main__":
    unittest.main()
