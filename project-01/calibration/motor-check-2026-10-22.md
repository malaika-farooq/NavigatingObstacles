# Initial floor motor check — October 22, 2026

The user placed the robot on the floor and requested motor tests. A direct diagnostic ran under the existing Pybricks MicroPython 2 interpreter, using only built-in `os` and `time` and ev3dev sysfs. No firmware update, external robotics library, or navigation-controller deployment was involved.

Both large motors were discovered by port address (A left, B right), with normal polarity and no initial running state. Battery voltage was 7.75 V. Each motor received a positive pulse followed by a negative pulse: target speed 90 encoder counts/s, duration 400 ms, with stopped pauses between pulses. This was kernel-regulated speed control, not a 90% duty command or our own PI controller. The kernel `run-timed` command bounded each pulse independently of the laptop connection; explicit stop commands were also issued after each pulse and in final cleanup.

| Motor | Target counts/s | Encoder before | Encoder after | Change | Gyro before | Gyro after |
| --- | --- | --- | --- | --- | --- | --- |
| A | +90 | 9 | 36 | +27 | -144° | -146° |
| A | -90 | 36 | 12 | -24 | -146° | -144° |
| B | +90 | 34 | 65 | +31 | -144° | -141° |
| B | -90 | 65 | 34 | -31 | -141° | -144° |

Both motors responded with the requested encoder sign, and the diagnostic completed with both stopped. No `stalled` or `overloaded` flags were observed in roughly 50 ms polling intervals; brief unsampled events cannot be excluded. The small pulses produced opposite gyro changes for A and B, and the final gyro reading matched the starting reading at integer-degree resolution.

At the user's request, a single positive A pulse was repeated after a five-second observation pause, with the same 90 counts/s and 400 ms settings. The encoder changed from 0 to 26, gyro from -144° to -145°, and both motors were stopped at completion. The changed starting encoder position occurred between diagnostics; neither diagnostic reset encoder positions. Direction observation is still pending.

The user found the short pulse too small to judge. A further positive A pulse used the same 90 counts/s target for 1500 ms, after a five-second observation pause. The encoder changed from 0 to 126 (about one third of a motor revolution); gyro changed only from -145° to -146°. Both motors were stopped at completion. The small gyro response relative to encoder motion needs comparison with observed chassis motion; it does not establish successful traction or correct gyro mounting. No geometry or sign was inferred from it.

These results establish basic motor/encoder response and a gyro response during wheel-driven movement. They do **not** establish wheel travel direction relative to the front caster, gyro CCW sign or angular accuracy, wheel dimensions, straight-line accuracy, slip, repeatability, or navigation readiness. Motor forward signs and gyro sign remain unset pending observed direction. The existing physical navigation runner/watchdog is still unfinished; this bounded kernel-timed diagnostic does not validate that future runner.

## Subsequent observed direction tests

The user requested sustained slow motion to inspect the drivetrain. Motor A ran at a positive target of 90 counts/s with a 60-second kernel time limit. The user observed the left wheel driving backward, away from the front caster, and requested a stop. An explicit stop was issued to both motors; subsequent independent reads confirmed empty running states and zero speed on A and B. The last streamed A sample before interruption was at 23.263 seconds, encoder 2093, speed 89 counts/s, gyro -444°. This is not the exact stopping time or final position.

Motor B was then tested alone at +90 counts/s with a five-second kernel time limit. Streamed samples at 1.050/2.115/3.181/4.245 seconds reported encoder positions 91/187/284/380, speeds 91/96/91/93 counts/s and gyro angles -446/-427/-406/-387°. The diagnostic finished with both motor states empty. The user likewise observed the right wheel driving backward, away from the caster.

These observations supersede the pending-direction status above: **LEFT_FORWARD_SIGN = -1 and RIGHT_FORWARD_SIGN = -1** are now saved in `src/config.py`. Gyro CCW sign, dimensions and overall calibration remain unset. These tests establish wheel direction, not measured travel distance or turn accuracy. No further movement was started after the right-wheel check.

## Both-wheel forward checks

The user then authorized continuation, followed by a request for a five-second run. Both motors received -90 counts/s targets with individual kernel time limits and explicit final stop commands. The already-submitted two-second run completed first; a separate five-second run followed after it stopped. The gyro stayed in `GYRO-ANG`; neither diagnostic reset encoders or gyro.

| Timed run | A encoder start/end | B encoder start/end | Raw gyro start/end | Final motor speeds |
| --- | --- | --- | --- | --- |
| 2 seconds | 0 / -161 | 0 / -178 | -371° / -374° | Both 0 |
| 5 seconds | 0 / -444 | 0 / -454 | -374° / -375° | Both 0 |

Both runs finished with empty motor states and no observed stall/overload flags during polling. The five-second run produced approximately 1.23 and 1.26 motor revolutions, with a net raw gyro change of -1°. This is a short forward-response check, not a measured straightness or distance calibration: no floor distance, lateral deviation, full heading history, or wheel slip was measured. User observation of chassis motion is still pending. Gyro sign remains unset and `CALIBRATED` remains false.
