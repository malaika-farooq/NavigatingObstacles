#!/usr/bin/env python3
"""Offline simulation with CSV traces and JSON results. No network/device access."""
import argparse
import csv
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from simulation import demo_settings, run_demo
from planner import demo_course

SCENARIOS = {
    "ideal": {},
    "uneven": {"motor_gains": (6.0, 8.0)},
    "quantized": {"quantization_deg": 1},
    "slip": {"traction": (0.85, 0.85)},
    "drift": {"gyro_drift_deg_s": 0.1},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["all"] + list(SCENARIOS), default="all")
    parser.add_argument("--output", type=Path, help="new directory for CSV/JSON artifacts")
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or PROJECT / "logs" / ("simulation-" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT, capture_output=True, text=True)
    report = {"notice": "Fictional model; not EV3 calibration or physical validation",
              "git_commit": revision.stdout.strip(), "utc": stamp,
              "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((PROJECT / "src").glob("*.py"))},
              "fictional_dimensions_m": [0.056, 0.056, 0.12],
              "course": demo_course(), "settings": demo_settings(), "scenarios": {}}
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for name in names:
        with (output / (name + ".csv")).open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "state", "left_duty", "right_duty", "estimated_x_m",
                             "estimated_y_m", "estimated_heading_deg", "true_x_m", "true_y_m",
                             "true_heading_deg", "left_encoder_deg", "right_encoder_deg"])

            def record(robot, command):
                writer.writerow([robot.time, command["state"], command["left_duty"], command["right_duty"]]
                                + list(command["pose"]) + list(robot.pose()) + robot.angles)

            result = run_demo(record=record, **SCENARIOS[name])
        result["model_changes"] = SCENARIOS[name]
        report["scenarios"][name] = result
        print("%s: state=%s, truth_pass=%s, true_goal_error=%.3f m, max_pose_error=%.3f m" %
              (name, result["state"], result["simulation_pass"], result["true_goal_error_m"],
               result["peak_position_error_m"]))
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Saved", output)
    print("Slip/drift scenarios intentionally demonstrate limitations; inspect truth_pass, not just DONE.")


if __name__ == "__main__":
    main()
