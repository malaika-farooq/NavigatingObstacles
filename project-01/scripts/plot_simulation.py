#!/usr/bin/env python3
"""Optional laptop-only plotting (matplotlib); robot and simulation need no packages."""
import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="directory written by simulate.py")
    args = parser.parse_args()
    report = json.loads((args.directory / "report.json").read_text())
    course = report["course"]
    colors = {"ideal": "#167d86", "uneven": "#24598a", "quantized": "#8258a5",
              "slip": "#c05b20", "drift": "#b63247"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), layout="constrained")
    fig.suptitle("Offline navigation model: illustrative inputs, not EV3 calibration", fontsize=15)
    for ax, title in zip(axes[:2], ("Successful model scenarios", "Failure scenarios: actual paths")):
        ax.set_title(title)
        for x, y in course["obstacles"]:
            half = course["obstacle_side"] / 2
            ax.add_patch(Rectangle((x-half, y-half), 2*half, 2*half, color="#303942"))
        ax.scatter(*course["start"], marker="o", color="black", label="Start", zorder=5)
        ax.scatter(*course["goal"], marker="x", color="black", label="Target", zorder=5)
        sample = next(iter(report["scenarios"].values()))
        ax.plot([p[0] for p in sample["route"]], [p[1] for p in sample["route"]],
                "--", color="#9aa4ac", label="Planned center path")
        ax.set(xlim=(0, course["workspace"][0]), ylim=(0, course["workspace"][1]),
               xlabel="x (m)", ylabel="y (m)")
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)
    for name, result in report["scenarios"].items():
        with (args.directory / (name + ".csv")).open() as stream:
            rows = list(csv.DictReader(stream))
        times = [float(r["time_s"]) for r in rows]
        xs = [float(r["true_x_m"]) for r in rows]
        ys = [float(r["true_y_m"]) for r in rows]
        errors = [math.hypot(float(r["estimated_x_m"])-x, float(r["estimated_y_m"])-y)
                  for r, x, y in zip(rows, xs, ys)]
        ax = axes[0] if result["simulation_pass"] else axes[1]
        ax.plot(xs, ys, color=colors[name], label=name)
        axes[2].plot(times, errors, color=colors[name], label=name)
    axes[2].set(title="Estimator error against simulated truth", xlabel="Time (s)", ylabel="Position error (m)")
    axes[2].grid(alpha=0.2)
    for ax in axes:
        ax.legend(fontsize=8)
    fig.savefig(args.directory / "overview.png", dpi=170)
    fig.savefig(args.directory / "overview.pdf")
    plt.close(fig)
    print(args.directory / "overview.png")


if __name__ == "__main__":
    main()
