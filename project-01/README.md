# Project 01: EV3 navigation

New agent or teammate: start with [HANDOFF.md](HANDOFF.md) for project decisions, verified hardware/runtime facts, the interrupted deployment status, and ordered next steps.

Target: **Pybricks MicroPython 2.0.0 on ev3dev-stretch**, using only built-in modules and our own code. No `pybricks`, `ev3dev2`, robotics framework, NumPy, or external planner imports. The Linux hardware drivers provide raw device access; our adapter uses their sysfs files directly. We retain the existing firmware and SD-card setup.

## Layout

```text
src/
  config.py       Actual ports, measured geometry, calibration, course
  hardware.py     Own motor/sensor sysfs adapter and read-only discovery
  geometry.py     Collision and angle helpers
  control.py      Own heading P, wheel PI, differential-drive calculations
  odometry.py     Encoder distance + gyro heading, with lens offsets
  planner.py      Own BFS, inflated obstacles, continuous edge checks
  motion.py       Output gate and waypoint-to-motion calculations
  navigation.py   Sampled turn/drive/settle controller with fault handling
  simulation.py   Fictional motor/robot model for offline development
  main.py         Nonmoving CLI commands
  selftest.py     Small on-brick compatibility/logic check
scripts/ev3.py    Laptop deployment, runtime checks, diagnostics, log retrieval
scripts/simulate.py       Offline scenarios, CSV traces and JSON reports
scripts/plot_simulation.py Optional laptop-only matplotlib plots
tests/           Laptop behavioral tests (standard-library unittest)
calibration/     Measured calibration records
logs/            Downloaded trial data (ignored by Git)
build-plan/      Assembly companion and adversarial review
```

Robot orientation: **front caster, rear drive wheels**. Looking forward from behind: **A = left motor, B = right**. The builder confirmed **gyro input 1 and color input 4**; device discovery must verify them on reconnection. Forward motor signs and gyro sign still require physical tests. Ports can be changed in `src/config.py`. Earlier build-guide wiring diagrams use suggested inputs 2/3; the confirmed 1/4 configuration takes precedence.

## Start locally

Run from the repository root; no virtual environment or pip packages are required:

```bash
python3 -m unittest discover -s project-01/tests -v
python3 project-01/src/main.py selftest
python3 project-01/src/main.py plan-demo
python3 project-01/src/main.py simulate-demo
python3 project-01/scripts/simulate.py
```

The demo uses a synthetic course and illustrative dimensions. It does not use your actual robot measurements or execute a route. Real `plan` requires the actual configuration; it fails clearly when values are missing. The assignment PDF has conflicting overlaid workspace widths, so no width or sample goal is silently treated as authoritative.

See [offline development](OFFLINE_DEVELOPMENT.md) for the sampled controller, simulation scenarios, fault tests, and interpretation of simulated completion versus actual target arrival. Simulation never imports hardware or changes calibration. CSV/JSON outputs go into ignored `logs/simulation-*` directories. Optional plotting uses matplotlib on the laptop only; it adds no robot dependency.

## Connect, deploy and inspect

Your laptop needs Python 3, Git, OpenSSH (`ssh` and `scp`). `uv` is optional for future laptop-only tools. Nothing needs to be installed with pip on the brick.

```bash
export EV3_HOST=ev3dev.local
python3 project-01/scripts/ev3.py runtime
python3 project-01/scripts/ev3.py deploy
python3 project-01/scripts/ev3.py inspect
python3 project-01/scripts/ev3.py selftest
python3 project-01/scripts/ev3.py plan-demo
python3 project-01/scripts/ev3.py monitor --samples 20
python3 project-01/scripts/ev3.py fetch-logs
```

SSH asks for the robot account's password interactively; credentials are never stored in the repository. The original image's default password is `maker` if unchanged. First connection records the host key. An IPv6 link-local address can also be used, including the laptop USB interface scope, for example:

```bash
export EV3_HOST='fe80::16:53ff:fe81:c7fa%enp52s0f4u1'
```

That example is this session's detected brick address and laptop interface, not a portable default. If the link drops while waiting for DHCP, configure the **USB interface only** with IPv6 link-local networking. See [ev3dev networking](https://www.ev3dev.org/docs/networking/). Do not change the laptop's Wi-Fi connection for deployment.

Deployment copies a timestamped release, verifies source checksums on the brick, and then updates the `current` symlink. It never starts robot code. The remote project is `/home/robot/navigating-obstacles/project-01`; previous releases and logs are preserved. Each release records the Git commit, whether the working tree is dirty, and checksums of the actual source files. A dirty deployment is identifiable by its source checksums even before it is committed.

`inspect`, `monitor`, `plan`, `plan-demo`, and `selftest` never issue motor or sensor-mode commands. Monitor captures raw readings in the sensor's current mode; it is not automatically a calibrated heading or color measurement. `monitor` saves a diagnostic text log on the brick. Use `fetch-logs` to download it.

## Development sequence

1. Inspect device ports and confirm configuration, then test runtime compatibility on the actual brick.
2. Implement explicit, short bench direction tests with wheels lifted, a timeout and a working abort/watchdog. Do not begin with a route runner.
3. Measure wheel scales, track, footprint, gyro direction/drift and optional lens offsets. Record all trial failures and chosen controller gains.
4. Integrate a timed control loop using `control.py` and `hardware.py`. Add acceleration limiting, stall detection, button abort, independent motor watchdog and stop-on-exception. `run-direct` does not stop just because a remote SSH connection disappears; `finally` cannot protect against SIGKILL. Validate these before floor motion.
5. Build and test distance and absolute-heading primitives, then update odometry throughout motion. Treat pose as uncertain after a slip/stall; realign before restarting unless independent localization recovers it.
6. Populate the actual course and test the planner. Integrate waypoint execution only after full-route clearance/error trials support it. Account for corrected paths and turning envelopes.

This is an **offline-tested controller and starter hardware structure**, not a tuned autonomous navigation implementation. `Navigator.step()` computes bounded duties from supplied samples and is exercised against a fictional model. It does not open devices, schedule a real-time loop, or independently stop physical motors. There is intentionally no command that executes physical motion. `MotionSession` remains the boundary for future hardware integration; the CLI cannot enable it. `CALIBRATED` remains false and physical dimensions remain unset.

Use the configured footprint radius plus measured position-error allowance when planning. The expanded-box/circle model is conservative; a rejected grid search is not proof that the physical course is impossible. BFS minimizes grid hops, not physical route length, and exact endpoint connectors can have arbitrary headings. Routes require physical validation. Seam correction stays disabled; a black floor reading is not sufficient to declare arrival outside the mapped goal region.

References: [ev3dev motor interface](https://www.ev3dev.org/docs/tutorials/tacho-motors/), [sensor interface](https://docs.ev3dev.org/projects/lego-linux-drivers/en/ev3dev-stretch/sensor_class.html), [Pybricks 2 CLI runtime](https://www.ev3dev.org/docs/programming-languages/).
