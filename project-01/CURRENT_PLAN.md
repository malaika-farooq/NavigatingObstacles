# Project 01 current plan

Updated October 22, 2026. This status supersedes historical pending items in the handoff and offline-development notes.

## Completed

- Retain Pybricks MicroPython 2.0.0 on the existing SD card. No external robotics libraries; built-in modules and our own code only.
- Front caster / rear drive-wheel build: A left, B right, gyro input 1, color input 4. Devices discovered on the brick.
- Observed wheel direction: both forward signs are -1. Gyro CCW sign is -1, verified with a hand turn from raw -483° to -548°.
- Two-wheel five-second slow forward test: user confirmed travel toward the caster with no visible veering. Encoder changes were A -444°, B -454°; net raw gyro change -1°. Both motors stopped afterward.
- Short stationary gyro check: no observable change over 11.73 seconds. Built-in garbage collection and free-heap inspection work on the brick.
- Remounted color sensor: 30 samples on white tabletop all 57%; 30 on black bubble wrap all 1%. User accepted these as the current calibration. **Black is reflection <= 29%; above 29% is nonblack.** This is a binary reflection classifier, not full color recognition.
- Standard kit tires: nominal diameter 56 mm and width 28 mm, documented by LEGO. Both diameter settings are 0.056 m; effective rolling diameters have not been measured.
- Known-map planner, sampled controller, offline simulations, and local behavioral tests are implemented. Source changes belong on GitHub main after review/tests; repository updates do not imply robot deployment.

Validation for this update: **41 local behavioral tests pass**, including threshold equality, invalid reflection/threshold rejection, and mode-preserving sensor classification. The local compatibility/logic self-test also passes. These are laptop results; on-brick execution of the updated source remains pending.

## Next steps

1. Deploy the latest source and run `selftest`, `inspect`, and `color-check` on the EV3, with motors off. Full updated controller compatibility has not yet been verified on the brick. `color-check` reads the current `COL-REFLECT` mode and applies the configured threshold without changing modes or commanding motors.
2. When a ruler is available, measure wheel center spacing, footprint radius, and color-lens offsets. For matching 28 mm tires, center spacing is outside-to-outside tire width minus 28 mm. Wheel spacing measurement is explicitly deferred by the user.
3. Implement and validate the hardware control loop, independent motor watchdog, operator abort, and stop-on-failure behavior. Timed diagnostic pulses already used kernel stop timers; this does not validate a future raw-duty navigation runner.
4. Measure straight distance and known-angle turns, tune gains and fault limits, check longer gyro drift, and establish a position-error allowance. Fill remaining geometry and enable overall motion calibration only when supported by these results.
5. Confirm workspace dimensions, starting heading, assigned obstacle/start/goal coordinates and arrival criterion. Plan using the measured footprint plus error allowance; validate clearance and repeat complete routes for the report/demo.
6. Integrate black detection as goal confirmation near the mapped goal, accounting for the sensor offset. Black detected elsewhere must not declare arrival. The sampled navigator currently uses positional arrival and has no color input; this integration remains pending.

The 29% threshold is the selected working setting; further material sampling is not a prerequisite requested by the user. Its evidence is the tabletop/bubble-wrap comparison, not an actual-course material test. `CALIBRATED` remains false because motion calibration and geometry are incomplete. No motor run is part of these code/documentation updates.

Records: [sensor measurements](calibration/sensor-check-2026-10-22.md), [motor tests](calibration/motor-check-2026-10-22.md), [configuration](src/config.py).

Nominal tire source: [LEGO Element Survey 45544, page 4](https://assets.education.lego.com/v3/assets/blt293eea581807678a/blt91044a33a75ac6c1/5ec7f33ae806087c31d740d5/ev3-design-engineering-element-survey.pdf?locale=en-us), tire element 6035364, 56 x 28 mm. Nominal circumference is approximately 0.176 m per wheel revolution; motor revolutions equal wheel revolutions only for a 1:1 drivetrain.
