<!-- Current planning changes: see CURRENT_PLAN.md. Workspace uses the PDF 4.88 x 3.05 m layout; starting heading remains unconfirmed. Wavefront endpoint connectors consider all visible cells. -->

# Project 01 agent handoff

Updated: October 22, 2026. Read this before operating the robot or changing the runtime.

## Latest deployment

Revision `9905043` is deployed as `20261023T003617Z-1ed71111ecea`; all source checksums verified. On-brick self-test, device inspection, color check, and PDF-map preview passed with no motor or sensor-mode commands. Both motor encoders/speeds remained zero during 20 monitored samples; gyro input 1 stayed −639°, color input 4 read 59–60%. Runtime is Pybricks MicroPython 2.0.0 and GC is enabled. See [deployment record](calibration/deployment-check-2026-10-22.md). This supersedes historical interrupted-deployment statements below; physical motion calibration and the independent watchdog remain incomplete.

## Current plan and accepted calibration

Read [CURRENT_PLAN.md](CURRENT_PLAN.md) first for completed checks and ordered remaining work. The user accepted white tabletop 57% and black bubble wrap 1% after remounting: **black threshold 29%, inclusive**. The configured color references and threshold are implemented through the hardware classifier and nonmoving `color-check` CLI. Nominal kit wheel diameters are now 0.056 m, sourced from LEGO's 56 x 28 mm tire listing; they are not measured effective rolling diameters. Both forward signs and gyro CCW sign are -1. Wheel spacing is deferred, other motion geometry remains incomplete, and `CALIBRATED` remains false. The starter work was merged to main at a143094; new updates do not imply on-brick deployment. Historical pending-threshold, unknown-sign, unset-diameter and branch-only statements below are superseded by this section and the current plan.

## Latest confirmed signs and physical observations

All three signs in `src/config.py` are now confirmed as **-1**: left motor forward, right motor forward, and gyro CCW. The user confirmed the five-second two-wheel test moved toward the front caster with no visible veering. A manual counterclockwise turn from a captured steady -483-degree gyro baseline produced five steady -548-degree readings. The actual hand-turn angle was not measured; do not treat this as a 90-degree accuracy calibration. Both motors were stopped with zero speed during the gyro checks, and no new motor commands were issued. See the calibration records. These results supersede older pending-sign statements below. Geometry and full motion calibration are still incomplete, `CALIBRATED` remains false, and the updated source has not been deployed by these diagnostics.

## Latest motor check

After direction confirmation, both wheels were tested together at raw -90 counts/s, first for two seconds and then for five seconds as requested. The five-second run recorded encoder changes A -444 / B -454 counts, raw gyro -374° to -375°, and both final speeds zero. User observation and measured floor distance remain pending; this is not complete straight-line calibration. No further motion should start automatically on reading this handoff.

The user subsequently placed the robot on the floor and authorized motor tests. Both motors responded to short positive/negative kernel-timed speed pulses. Longer observed tests established that positive raw commands drive **both wheels backward, away from the front caster**. `LEFT_FORWARD_SIGN` and `RIGHT_FORWARD_SIGN` are now **-1** in `src/config.py`. Both motors were stopped after testing. See [motor-check record](calibration/motor-check-2026-10-22.md). Gyro CCW sign and geometry remain unconfirmed. These diagnostics supersede historical statements below that no motor commands have been issued or motor directions are unknown, but do not validate the navigation controller or finish the interrupted deployment. Overall `CALIBRATED` remains false.

## Latest connected sensor results

Both sensors are now discovered on the actual brick: gyro **input 1**, color **input 4**. A stationary 101-sample check over 11.73 seconds showed no observable gyro angle change (-48 degrees throughout); motor encoder positions were unchanged. Color reflection was 5% with the lens more than 1 cm above a white table, then **83–85%** when the user placed white paper close beneath it. Mounting height and black/floor contrast still need calibration; gyro direction and known-angle response have not been checked. Built-in `gc.collect()` and `gc.mem_free()` also work on this actual Pybricks 2 build, reporting approximately 8.18 MB free heap in the diagnostic. See [sensor-check record](calibration/sensor-check-2026-10-22.md). These direct diagnostics did not activate the earlier deployment, run the full controller, or issue motor commands. They supersede older statements below that sensors and the GC API had not yet been verified.

## Current scope, style and memory decisions

The user requested small functions with one responsibility, intermediate variables that document the math, and strict alignment with the assignment PDF. Navigation, planning, odometry, control, device reads and CLI dispatch have been refactored accordingly. Keep the task focused on the supplied map/start/goal, collision-free travel inside the workspace, and report/demo evidence. Do not introduce unknown-obstacle exploration, required seam localization or shortest-path optimization. The optional plotting script and unused seam-correction flag were removed.

The simulated final-arrival check now uses the PDF's **0.305 m goal radius**, rather than the 0.015 m intermediate-waypoint tolerance. The gyro-drift example still has significant localization error but finishes inside that goal area; do not repeat the older claim that it necessarily fails arrival. Physical footprint clearance and estimator error are reported separately.

**38 local tests pass.** The controller reuses its input/output and pose buffers. `Navigator.step()` returns a borrowed mutable dictionary whose `pose` list is also reused; log values immediately or copy a snapshot. Automatic garbage collection remains enabled; explicit `gc.collect()` is limited to measured stopped transitions and idle planning commands. MicroPython 1.11 documents GC support, but the actual EV3 build's heap API and pause durations have not been checked. The runtime command now checks these capabilities. No robot connection was used for this refactor. Earlier sections below are historical context where they mention 35 tests, optional plotting, or a failed drift-arrival scenario.

## Latest offline continuation

The user subsequently requested development **without the robot connected**. Work continues on `nick-project-01-starter`; no robot/network access or deployment is part of this offline work. A handoff-only copy was separately pushed to `main` at `f9a29d4`; starter code remains on its branch.

Since the original handoff below, `navigation.py` adds a sampled turn/drive/settle controller with duty limits, route revalidation, stall/timing/timeout/abort handling. `simulation.py` and laptop scripts exercise it against a fictional plant and export CSV/JSON results and optional plots. **35 local tests pass.** Ideal, unequal-motor and one-degree-quantized scenarios pass; equal-wheel slip and gyro drift intentionally expose a mismatch between reported completion and simulated true arrival.

Read [OFFLINE_DEVELOPMENT.md](OFFLINE_DEVELOPMENT.md) for implementation details, results and remaining work. Robot code still imports no external robotics libraries, calibration remains unset, the CLI has no physical-motion command, and an independent hardware watchdog/runner is still missing. New code has not been tested under the actual EV3 interpreter. The interrupted deployment described below remains interrupted; no later on-brick verification is implied by the offline test results. The following original handoff records the baseline before this continuation.

**Latest port correction from the builder:** left motor **A**, right motor **B**, gyro sensor input **1**, color sensor input **4**. `src/config.py` now reflects these assignments. They supersede the earlier proposed sensor inputs 2/3 and wiring illustrations. No new device discovery occurred during offline development; confirm the sensors when reconnecting. The user briefly called the sensor ports C/D, then clarified the numbered inputs 1/4.

## Objective and user decisions

Build and program a LEGO MINDSTORMS Education EV3 to navigate a known obstacle course. Continue from the existing starter; the next priority is hardware verification and repeatable motion, not more framework setup.

- **No external robotics libraries.** The user explicitly repeated this restriction. Robot source uses only built-in `os`, `sys`, `time`, `math`, and our own modules. Do not add `pybricks` API imports, `ev3dev2`, `DriveBase`, external planners, or robotics/sensor-fusion packages.
- **Stay on Pybricks MicroPython 2.0.0 running on ev3dev-stretch.** Here Pybricks is the interpreter, not an imported robotics library. Our own adapter accesses the Linux motor/sensor drivers through `/sys/class/`.
- **The firmware upgrade was explicitly canceled.** No internal firmware was flashed. Do not resume any upgrade or run cached flashing scripts without a new user instruction.
- Use CLI tools, SSH/SCP, and Git. No LEGO desktop application, VS Code extension, robot virtual environment, or robot-side pip installation is needed. `uv` is optional for laptop tools and does not manage the EV3 MicroPython runtime.
- Do not infer physical dimensions, motor signs, actual course coordinates, or completed calibration from example values.
- The user requested and authorized starter setup and a branch push. **No motors have been moved by the agent.** Arrange physical readiness with the user before a future powered bench test; the starter CLI deliberately has no motion command.

## Repository and Git status at handoff

- Laptop repository: `/home/toytoi/Repos/school/NavigatingObstacles`.
- Remote: `https://github.com/malaika-farooq/NavigatingObstacles.git`.
- Current pushed starter branch: **`nick-project-01-starter`**.
- Starter commit: **`eddc6c7`**, `Add Project 01 EV3 starter code and build guide`.
- Branch URL: <https://github.com/malaika-farooq/NavigatingObstacles/tree/nick-project-01-starter>.
- Starter has **not** been merged into `main`. Earlier, branch `nick` added `project-01/proj1.pdf`; that was merged into `main` at `9ae4c23`, and both `main` and `nick` were pushed.
- This handoff is a subsequent documentation change; use `git status` to determine whether it has been committed/pushed. Do not mistake the starter commit above for the handoff commit.

Read [README.md](README.md), [config.py](src/config.py), and [the adversarial review](build-plan/adversarial-review.md) after this handoff.

## Assignment requirements and ambiguities

Source of truth: [proj1.pdf](proj1.pdf), copied from the user's Downloads folder.

- Start, goal, and obstacle coordinates are supplied before a run; interactive course input is unnecessary.
- Obstacles are axis-aligned **0.305 m square black cardboard pieces laid on the floor**. The PDF does not give their thickness. Do not assume upright blocks.
- The goal is a black circle with radius **0.305 m**.
- The PDF says obstacle, start, and goal centers align with floor-tile intersections.
- If a route exists, the assignment guarantees a route at least **0.61 m wide**. The robot still needs clearance for its entire footprint and navigation error.
- Reach the goal without crossing an obstacle tile or leaving the workspace. Speed and shortest path are secondary.
- Submit a report explaining the build and navigation strategy, include actual code, and give a demonstration. The document lists October 31, 2026 as the current due date, alongside old overlaid text.
- **Workspace dimensions conflict in overlaid text:** 4.88 x 3.05 m versus 3.66 x 3.05 m. Confirm the actual dimensions instead of treating the sample illustration or coordinate list as the assigned course.
- Starting heading and the precise goal-arrival criterion also need to be established for implementation.
- The PDF itself does not prohibit libraries or prescribe MicroPython; the library restriction comes directly from the user and still applies.

## Physical build and sensor decisions

The user's robot has **two driven wheels at the rear and a caster at the front**, like a tricycle. Looking from behind toward the front caster:

| Item | Confirmed / recommended status |
| --- | --- |
| Left large motor | **Port A**, confirmed by user |
| Right large motor | **Port B**, confirmed by user |
| Motor forward signs | Unconfirmed; establish with wheels lifted |
| Gyro input | **1**, subsequently confirmed by the builder; discovery pending |
| Color input | **4**, subsequently confirmed by the builder; discovery pending |
| Latest device inspection | Two large motors on A/B; sensors were still being connected and were not enumerated |
| Wheel/track/footprint measurements | Not supplied; config values remain `None` |

Recommended sensing: built-in wheel encoders + one gyro + an optional downward color sensor. Skip ultrasonic and touch sensors for avoiding these flat cardboard obstacles. They do not solve this course's main odometry problem.

- **Gyro:** rigidly mount to the main chassis, with its sensing axis vertical so it measures left/right turns. It need not be at the robot center or wheel axle. Do not mount on a freely rotating axle, caster, or flexible arm. Keep the robot still during connection/startup; measure drift rather than merely zeroing the display.
- **Color sensor:** point straight down, preferably near the centerline and a little ahead of the rear drive-wheel axle. Use a short rigid mount, not the moving caster assembly. Keep the lens close to the floor without scraping; the previously suggested 5–10 mm range is an experimental starting point, not a fixed manufacturer requirement. Measure lens offsets from the drive-wheel midpoint.
- **Caster:** bracket fixed to chassis, intended ball rolling or wheel/fork movement free. Centering is preferred but not mandatory. Both drive wheels must stay loaded during turns and seam crossings.
- The official driving base is the starting point, not a requirement to copy every conceptual sketch. Preserve a working drivetrain and modify only measured weaknesses: loose joints, snagging caster, or a protruding sensor boom.
- The 12-page [build guide](build-plan/ev3-build-plan.pdf) links LEGO's exact assembly manuals. Its original layouts are conceptual, and some show a rear caster. **Follow the actual front-caster geometry.** Combined gyro/color module fit and parts inventory have not been physically verified.

## What is implemented versus unfinished

| File | Current behavior |
| --- | --- |
| `src/config.py` | A/B mapping, calibration gates, unset dimensions/signs/course; seam correction disabled |
| `src/hardware.py` | Own sysfs discovery, read-only snapshots, raw-duty motor adapter, gyro/color mode access |
| `src/geometry.py` | Angle wrapping, distances, continuous segment/rectangle collision test |
| `src/control.py` | Own heading proportional calculation, differential-drive wheel targets, wheel PI with anti-windup |
| `src/odometry.py` | Incremental encoder distance + continuous gyro heading; configurable initial pose and lens offset transform |
| `src/planner.py` | Own four-neighbor BFS with inflated obstacles, boundary clearance, exact endpoint connections and edge validation |
| `src/motion.py` | Explicit output gate and next-segment calculations; **not an executing navigation controller** |
| `src/main.py` | `inspect`, `monitor`, `selftest`, `plan-demo`, `plan`; all nonmoving |
| `src/selftest.py` | Small logic/compatibility check designed for the actual MicroPython runtime |
| `scripts/ev3.py` | Laptop SSH/SCP deployment, runtime/diagnostic commands, monitoring and log retrieval |
| `tests/test_core.py` | 16 passing laptop tests, including robot import restrictions |

The scaffold contains real calculations, not just empty files. It is **not a completed autonomous robot program**. Missing work includes timed control-loop integration, calibrated gains, acceleration limiting, abort/watchdog behavior, stall handling, distance/turn primitives, route execution, goal confirmation and actual physical trials.

`CALIBRATED = False`, `CALIBRATION_ID = "unmeasured"`, motor signs and geometry are unset. Do not flip these flags merely to get past a validation error. The low-level motor adapter uses `run-direct`, bypassing kernel speed/position PID so our control logic can be written independently.

**Important motor-output limitation:** `run-direct` can remain active if a control program disappears. `try/finally` alone does not handle SIGKILL, lost process execution, or power failure. Implement and validate an independent stop/watchdog and reachable abort before floor motion. Never run two hardware controllers concurrently.

The planner uses a conservative circle envelope and expanded axis-aligned boxes. It can reject physically feasible paths. Grid BFS minimizes hops, not metric length; exact endpoint connectors can have arbitrary headings. A failed search is not proof that the course is impossible, and the demo route is not the actual assignment route.

## Verification already performed

**Laptop, passed:**

```bash
python3 -m unittest discover -s project-01/tests -v
python3 project-01/src/main.py selftest
python3 project-01/src/main.py plan-demo
python3 project-01/scripts/ev3.py --help
```

The 16 tests cover obstacle detours, blocked courses, boundary rejection, collisions between otherwise clear endpoints, retained exact endpoints, path reversal, odometry baselines/forward/reverse/turns/heading continuity, sensor offsets, controller signs/limits/anti-windup, current-pose segment calculation, port-based discovery, calibration blocking and built-in-only robot imports.

**On the EV3, verified before deployment:**

- SSH works over USB IPv6.
- OS: `ev3dev-stretch`; kernel: `4.14.117-ev3dev-2.3.5-ev3`.
- `/usr/bin/brickrun`, `/usr/bin/pybricks-micropython`, `/usr/bin/micropython`, `/usr/bin/python3` exist.
- Executing `brickrun -r -- pybricks-micropython` works. `sys.implementation` reported Pybricks **2.0.0**, MicroPython source tag `v1.11`, build date `2020-05-06`. `sys.version` printed `3.4.0`; this is not a current CPython installation.
- Built-in `os`, `time`, `math`, `sys`, filesystem access, `time.ticks_ms`, `time.ticks_diff`, and `time.sleep_ms` were checked under that actual interpreter.
- Home directory writable; about 27 GB free at the earlier check.
- Only the built-in runtime checks above are proven on-brick. **The deployed starter's self-test, inspect and demo have not yet run there.**

No agent-driven motor motion, physical sensor calibration, stopping/watchdog test, or actual course trial has occurred.

## Interrupted deployment: first operational task

Remote project root: `/home/robot/navigating-obstacles/project-01`.

Deployment was deliberately interrupted at the user's pause request:

1. A timestamped release directory and `logs/` were created.
2. All nine `src/*.py` files and `deployment.json` were copied successfully.
3. Remote source checksum verification completed successfully.
4. **The final SSH command that would publish the `current` symlink was interrupted at its password prompt.** Do not assume `current` exists or references that release.

The uploaded manifest was generated before commit `eddc6c7`, so it records an older Git revision and a dirty working tree. Source checksums, not the old revision alone, identify that upload. The cleanest continuation is to rerun `deploy` from the current committed source; it retains earlier releases.

Then run `runtime`, `inspect`, `selftest`, and `plan-demo` on the brick. Fix any actual MicroPython compatibility issues before writing the motion loop. Do not describe these checks as completed until their outputs are observed.

## Connection details and commands

Linux laptop uses NetworkManager. Last working USB configuration:

```bash
export EV3_HOST='fe80::16:53ff:fe81:c7fa%enp52s0f4u1'
export EV3_KNOWN_HOSTS=/tmp/navigating-obstacles-ev3-known-hosts
```

- Account: `robot`; unchanged image default password is `maker` (public default, not a stored project secret).
- `ev3dev.local` did not resolve during this session. IPv4 DHCP waited/retried and dropped the USB link; IPv6 link-local worked.
- A **temporary, non-autoconnect NetworkManager profile** named `ev3-usb-upgrade` was created with IPv4 disabled and IPv6 link-local. Despite its historical name it only configures USB networking; it does not upgrade anything. It may disappear after NetworkManager/laptop restart.
- If still present, `nmcli --wait 10 connection up ev3-usb-upgrade` restored connectivity. Rediscover with `lsusb -d 0694:`, `ip -brief address`, `nmcli device status` and `ip -6 neigh` before trusting a stale interface scope/address. Configure only the robot USB link; leave laptop Wi-Fi alone.
- The known-hosts file is temporary. If missing or if using another laptop, establish the device identity and use a new known-host entry rather than disabling verification.

From the repository root, after network setup:

```bash
python3 project-01/scripts/ev3.py runtime
python3 project-01/scripts/ev3.py deploy
python3 project-01/scripts/ev3.py inspect
python3 project-01/scripts/ev3.py selftest
python3 project-01/scripts/ev3.py plan-demo
python3 project-01/scripts/ev3.py monitor --samples 20
python3 project-01/scripts/ev3.py fetch-logs
```

SSH/SCP may prompt several times during deployment. The scripts never store credentials. Deployment copies into a new release, checks each source checksum, then publishes the `current` symlink without running robot code. `monitor` saves diagnostic text on the brick; snapshots report the current sensor mode, not an assumed calibrated physical quantity. Sensor discovery numbers are dynamic: resolve addresses such as `ev3-ports:outA`, not `motor0`.

Keep robot code compatible with this older MicroPython. Laptop-only scripts can use modern Python. No packages need to be added to the brick for the existing scaffold.

## Ordered next steps and acceptance criteria

1. **Finish nonmoving deployment/runtime checks.** Confirm actual device ports when the user finishes connecting sensors. Update configuration only with observed/confirmed assignments.
2. **Finish mechanical inspection and measurements.** Rigid mounts, no rubbing/dragging cables, freely moving caster, both drive wheels loaded. Record effective wheel diameters, wheel-center track, footprint radius and optional lens offsets.
3. **Implement a bounded raised-wheel bench test.** Explicit motion command, conservative limits, independently working stop/watchdog, reachable abort. Establish motor forward signs and gyro CCW sign; do not start with a route runner.
4. **Measure gyro startup behavior.** Keep still, log angle over representative run durations, compare physical turns against an independent square/angle reference. Avoid switching angle/rate modes during travel. Zeroing angle alone is not drift calibration.
5. **Implement own motion loop and primitives.** Wheel PI + heading feedback + speed ramps + odometry + timeout/stall/abort handling. Start with 0.305 m travel, then repeated 1 m straight runs and 90-degree turns in both directions. Use absolute map headings; update pose throughout stopping and turning.
6. **Evaluate real error and clearance.** Independently replace/alignment-check the robot for each trial. Measure intermediate deviations and tight turns, not only square closure. Compute available error as minimum planned center clearance minus footprint radius. Choose an allowance from repeated full-route tests with reserve. Compare smooth low/moderate speeds rather than assuming the slowest speed is best.
7. **Integrate actual course planning and execution.** Confirm workspace, initial heading, assigned coordinates and goal criterion. Test straight, L-shaped, one-obstacle and full-course routes. Recompute movements from estimated pose and validate corrective segments; do not blindly play nominal segment lengths.
8. **Add color-based goal confirmation and evaluate landmarks only if useful.** Obstacles and goal are both black, so require expected location context. One seam observation corrects at most one positional constraint; reject ambiguous associations. Seam correction remains disabled until actual-floor experiments pass.
9. **Report and demonstrate.** Record build choices, calibration IDs, source revision, test failures and repeated full-course performance. Ten consecutive unassisted route successes with clearance reserve was proposed as an initial project screen, not a grading requirement or a statistical guarantee.

Encoders plus gyro cannot detect/correct every slip. After a stall, slip or unexplained displacement, stop and treat pose as uncertain. Physically realign/restart unless an independent, validated localization method recovers it. Do not hide error by resetting the reported pose to a planned waypoint.

## Canceled-upgrade artifacts and scope boundary

The laptop has cached Pybricks 4.1.0 firmware and a prepared flashing helper under `/home/toytoi/.cache/navigating-obstacles-ev3-upgrade/`. The robot-home backup is there as well. These are outside the repository and are **not** part of the active development workflow. No firmware write occurred. Leave them alone; do not execute `prepare_ev3.py --flash` or interpret earlier upgrade discussion as current authorization.

The user ultimately chose Pybricks 2 and asked for the starter branch. Continue that work, retaining the no-external-robotics-libraries restriction and distinguishing tested calculations from untested hardware behavior.
