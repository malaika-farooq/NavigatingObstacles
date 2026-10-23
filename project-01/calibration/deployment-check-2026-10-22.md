# EV3 deployment and nonmoving checks — October 22, 2026

Deployed clean main revision `99050430b2b0a3e2c4ea7941934a118efb1edc6f` over USB SSH.
Release: `20261023T003617Z-1ed71111ecea` (UTC; October 22 locally).
Source digest: `1ed71111ecea72f34049a55204b392898ec8a6fe39d9adbaee30c91f0ccd0e5c`.
All 12 source files were uploaded and SHA-256 checked before the `current` symlink was atomically activated. The deployment manifest reports a clean source tree and no robot packages.

## Runtime checks

- Actual runtime: `pybricks-micropython` 2.0.0 final, underlying MicroPython `v1.11`, build date `2020-05-06`; `sys.version` is `3.4.0`.
- `time.ticks_ms` and `time.ticks_diff` are available.
- `gc.collect()` succeeds, `gc.isenabled()` is true, and free heap after collection was 8,192,928 bytes.
- On-brick `main.py selftest` passed: geometry, odometry, planner, control, and navigation abort; no motor outputs.
- On-brick `main.py plan-course` passed using explicitly assumed radius 0.13 m and error allowance 0.05 m. This validates execution of the map/planner on the runtime, not physical clearance.

## Synthetic controller check on the EV3

`main.py simulate-demo` completed successfully under the actual MicroPython runtime: state `DONE`, `simulation_pass=True`, zero simulated clearance violations, and true simulated goal error approximately 0.0115 m. The simulated duration was 57.34 s; this is not hardware timing or a physical trial. No hardware adapters or motor outputs were used by the simulation. The combined remote check command exited successfully.

## Read-only device checks

`main.py inspect`, `color-check`, and `monitor 20` used the existing sensor modes; no motor or sensor-mode commands were issued.

| Device | Observed result |
| --- | --- |
| Left motor A | LEGO large motor; encoder 0, speed 0, empty state throughout monitoring |
| Right motor B | LEGO large motor; encoder 0, speed 0, empty state throughout monitoring |
| Gyro input 1 | LEGO gyro, `GYRO-ANG`, degrees; all 20 samples −639° |
| Color input 4 | LEGO color, `COL-REFLECT`, percent; all 20 samples 59–60% |

`color-check` read 60%, applied the accepted inclusive black threshold of 29%, and returned `Black detected: False`. The surface under the sensor was not separately identified during this deployment. No recalibration was performed. The short repeated readings are not a long-term gyro drift measurement; monitor sleeps 0.1 s between reads, with additional file-access overhead.

`CALIBRATED` remains false. Wheel track, footprint, color offsets, starting heading, gains and physical error bounds still require the checks described in the current plan. Software compatibility does not establish physical navigation performance or an independent motor watchdog.
