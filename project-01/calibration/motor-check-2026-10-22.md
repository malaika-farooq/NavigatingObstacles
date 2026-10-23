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

These results establish basic motor/encoder response and a gyro response during wheel-driven movement. They do **not** establish wheel travel direction relative to the front caster, gyro CCW sign or angular accuracy, wheel dimensions, straight-line accuracy, slip, repeatability, or navigation readiness. Motor forward signs and gyro sign remain unset pending observed direction. The existing physical navigation runner/watchdog is still unfinished; this bounded kernel-timed diagnostic does not validate that future runner.
