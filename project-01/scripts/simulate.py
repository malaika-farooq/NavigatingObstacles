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


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["all"] + list(SCENARIOS), default="all")
    parser.add_argument("--output", type=Path, help="new directory for CSV/JSON artifacts")
    return parser.parse_args()


def report_metadata(timestamp):
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT, capture_output=True, text=True)
    checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted((PROJECT / "src").glob("*.py"))}
    return {"notice": "Fictional model; not EV3 calibration or physical validation",
            "git_commit": revision.stdout.strip(), "utc": timestamp,
            "source_sha256": checksums, "fictional_dimensions_m": [0.056, 0.056, 0.12],
            "course": demo_course(), "settings": demo_settings(), "scenarios": {}}


def record_sample(writer, robot, command):
    control_values = [robot.time, command["state"], command["left_duty"], command["right_duty"]]
    estimated_pose = list(command["pose"])
    true_pose = list(robot.pose())
    encoder_angles = robot.angles
    writer.writerow(control_values + estimated_pose + true_pose + encoder_angles)


def run_scenario(name, output_directory):
    trace_path = output_directory / (name + ".csv")
    with trace_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "state", "left_duty", "right_duty", "estimated_x_m",
                         "estimated_y_m", "estimated_heading_deg", "true_x_m", "true_y_m",
                         "true_heading_deg", "left_encoder_deg", "right_encoder_deg"])

        def record(robot, command):
            record_sample(writer, robot, command)

        result = run_demo(record=record, **SCENARIOS[name])
    result["model_changes"] = SCENARIOS[name]
    return result


def print_result(name, result):
    print("%s: state=%s, truth_pass=%s, true_goal_error=%.3f m, max_pose_error=%.3f m" %
          (name, result["state"], result["simulation_pass"], result["true_goal_error_m"],
           result["peak_position_error_m"]))


def main():
    arguments = parse_arguments()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_directory = arguments.output or PROJECT / "logs" / ("simulation-" + timestamp)
    output_directory.mkdir(parents=True, exist_ok=False)
    report = report_metadata(timestamp)
    scenario_names = list(SCENARIOS) if arguments.scenario == "all" else [arguments.scenario]
    for name in scenario_names:
        result = run_scenario(name, output_directory)
        report["scenarios"][name] = result
        print_result(name, result)
    report_path = output_directory / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("Saved", output_directory)
    print("Arrival uses the PDF's 0.305 m goal radius; pose error is reported separately.")


if __name__ == "__main__":
    main()
