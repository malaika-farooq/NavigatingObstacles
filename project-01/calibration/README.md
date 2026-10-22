# Calibration records

Keep measured results here, with the Git revision, date, floor, battery condition, payload, trial failures, and method. Copy validated parameters into `src/config.py` and set a unique `CALIBRATION_ID`.

Record motor forward signs, gyro CCW sign, effective wheel diameters, track width, footprint radius, starting-placement error, and (if fitted) the color lens's forward/left offsets. The builder confirmed left motor A, right motor B, gyro input 1 and color input 4. Sensor discovery and motor rotation signs still need checking.

Begin with raised-wheel direction checks, stationary gyro drift, repeated straight/turn trials, and full-route clearance/error trials. Physical tests are a later step; the starter CLI does not move the robot. Do not mark `CALIBRATED = True` until measurements and control-loop validation support it. A controller also needs an independent watchdog/abort path before raw motor outputs are used.

Seam correction is outside the current implementation. Refer to `../build-plan/ev3-build-plan.pdf` for the test worksheet; its sketches are conceptual and may show a different caster arrangement. This robot's caster is at the front and drive wheels are at the rear.
