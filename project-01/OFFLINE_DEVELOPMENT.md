# Offline navigation development

This document records the offline implementation phase. For subsequent connected tests, accepted 29% color threshold, confirmed signs, nominal 56 mm wheel diameters and the remaining plan, read [CURRENT_PLAN.md](CURRENT_PLAN.md). Historical statements here about unset calibration and unverified sensor/GC APIs are superseded by the current plan and calibration records. The full updated controller still needs on-brick runtime verification.

This work does not connect to the EV3, change firmware, enable motor outputs, or fill in actual calibration. Robot-side code continues to use built-in modules and our own implementation only. Stay on the selected Pybricks 2 runtime.

The current implementation is limited to the PDF's known-course navigation task. Small functions separate sample validation, odometry, steering, waypoint transitions and grid search. Intermediate variables name the physical quantities and units. The simulator and its logs are test support for the report; the optional plotting tool and unused seam-correction switch have been removed.

## What has been added

`src/navigation.py` contains a sampled waypoint controller. The caller supplies a monotonic timestamp in seconds, two forward-positive encoder angles, and a continuous counterclockwise-positive gyro angle. The controller returns left/right raw-duty requests, estimated pose, waypoint index, state and fault reason. It has no device or clock access.

The state sequence is:

```text
IDLE -> TURN -> DRIVE -> SETTLE -> next waypoint -> DONE
                  any active state -> ABORTED
```

Before starting, the controller requires an initial sensor sample and validates every segment against the supplied clearance map. It uses current estimated pose for headings/corrective paths, acceleration-limits forward speed, reduces speed near a waypoint, and waits for measured wheel motion to settle before advancing. Wheel PI controls the model's speed; heading feedback generates differential wheel targets.

Faults return zero requested duties, invalidate pose and prevent restart of that controller instance:

- Operator abort.
- Duplicate/backward timestamps or excessive sample gaps.
- Nonfinite inputs and implausible encoder/gyro jumps.
- Accumulated gyro/encoder heading disagreement.
- Estimated position, measured travel or a corrective segment violating map clearance.
- Individual wheel stalls under meaningful commands.
- Per-leg and full-route timeouts.

These are sampled software checks. A delayed-sample fault only runs when another sample reaches the controller. **It is not an independent physical motor watchdog.** Actual hardware still needs a timed loop, measured/calibrated gains, output ownership, a reachable abort, process-failure handling and a separately validated stop/watchdog before motor operation. Zero raw duty is also not the same as invoking the motor's brake command.

## Offline simulator

`src/simulation.py` models a fictional two-wheel robot with first-order motor response. It keeps simulated true pose separate from the controller's odometry. There is no hardware import, SSH connection or dependency on the current robot configuration.

The illustrative dimensions are 0.056 m wheel diameters and 0.12 m track. The planning envelope uses radius 0.15 m plus a 0.03 m error allowance. **These are synthetic model inputs, not measurements of this EV3.** All gains, response constants and fault thresholds in `demo_settings()` are also simulation values; do not copy them to calibrated configuration without bench work.

Current scenarios and observed model results:

| Scenario | Controller state | Independent simulated outcome |
| --- | --- | --- |
| Ideal model | DONE | Target error about 11 mm; no inflated-clearance violations |
| Unequal motor response | DONE | About 11 mm; feedback compensates in this model |
| One-degree sensor quantization | DONE | About 12 mm; no inflated-clearance violations |
| 15% equal-wheel traction loss | DONE | About 339 mm target error; inflated-clearance violations |
| 0.1 degree/s gyro drift | DONE | About 125 mm error; still inside the PDF's 305 mm goal radius |

The last two cases demonstrate localization limitations. **`DONE` means the estimator believes it reached the final waypoint.** `simulation_pass`/`truth_pass` additionally checks that the simulated robot center is inside the PDF's 0.305 m goal radius and that its footprint clearance was maintained. The small waypoint tolerance is not an extra assignment requirement. The drift case has substantial pose error but still passes these task checks; the slip case fails. The footprint check uses the conservative robot-envelope model without the planner's extra position-error allowance. The robot will not have access to simulated true pose, and gyro/encoder agreement cannot prove that slip is absent. The PDF does not precisely define whether the whole footprint or the robot center must enter the goal; the simulation uses the center and the demonstration criterion still needs confirmation.

The model does not reproduce actual EV3 friction, latency, caster motion, chassis flex, floor seams, illumination, sensor noise distributions or gyro temperature effects. Passing model scenarios validates logic, not physical navigation reliability.

## Run and inspect

From the repository root:

```bash
python3 -m unittest discover -s project-01/tests -v
python3 project-01/src/main.py selftest
python3 project-01/src/main.py simulate-demo
python3 project-01/scripts/simulate.py
```

There are **38 local behavioral tests** at this revision, covering geometry/odometry/planning, route following, unequal motors, quantization, slip, gyro drift, stall/abort/timing/timeout paths, route revalidation, numeric validation, Python 3.4-compatible syntax, buffer reuse and collection at stopped transitions.

The simulator prints the directory it creates. That directory includes one CSV trace per scenario and `report.json` with source checksums, model settings, course, state transitions and independent true/estimated results. Each run uses a new directory by default; an explicitly supplied `--output` must not already exist. Logs are ignored by Git.

## Garbage collection and buffer ownership

The MicroPython 1.11 documentation includes `gc.collect()` and heap inspection through `gc.mem_free()`/`gc.mem_alloc()`. The actual Pybricks build still needs the new runtime inspection command run on it. No firmware change is required by this code.

The controller allocates its sample, previous-sample, pose, speed, duty and result containers once. The output dictionary and its `pose` list are **borrowed mutable buffers**, reused on the next tick. A logger must write immediately or copy the individual values. Tests retain explicit snapshots where needed. Odometry and wheel-target calculations accept optional caller-owned output buffers while preserving convenient tuple returns for non-control callers.

Automatic GC is never disabled. Explicit collection occurs after measured wheel speeds have stayed within the stopped tolerance at TURN-to-DRIVE and completed-waypoint transitions. Planning-only commands also collect after the grid search has returned. There is no forced collection on every drive or turn tick. Floating-point calculations, function return values and sysfs reads still allocate, so the change reduces container churn rather than promising zero allocation. Measure heap use and GC pauses on the real brick, and choose timing limits from those observations.

References: [MicroPython 1.11 GC API](https://docs.micropython.org/en/v1.11/library/gc.html), [MicroPython allocation guidance](https://docs.micropython.org/en/v1.11/reference/speed_python.html).

## What remains when the robot returns

1. Complete the earlier interrupted deployment and run the expanded compatibility self-test on the actual MicroPython runtime. The new modules have **not** been executed on the EV3; a Python syntax check is not a runtime compatibility certificate.
2. Confirm connected ports, motor/gyro signs, actual geometry and gyro startup behavior. Calibration values remain unset.
3. Implement and bench-test the independent stop/watchdog and hardware loop. Use monotonic elapsed time based on `ticks_diff`; account for counter wrap rather than treating `ticks_ms()/1000` as unbounded time.
4. Tune wheel/heading controllers and verify straight travel, turns, stopping and fault behavior with the real robot. Set fault thresholds from measurements and expected sampling behavior.
5. Enter the actual course and evaluate physical clearance and error. Calibrate and adjust the existing approach first; adding external position references is not a required assignment feature.
6. Add location-gated color goal confirmation and repeat representative full-course runs. Controller completion alone is not proof that the physical robot reached the goal.
