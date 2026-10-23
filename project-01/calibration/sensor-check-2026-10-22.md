# Initial sensor checks — October 22, 2026

Tested on the connected EV3 using `brickrun -r -- pybricks-micropython` and built-in filesystem/time/GC functions. No external robotics libraries or motor commands were used. These checks do not constitute motion or complete sensor calibration.

## Device discovery

- Input 1: `lego-ev3-gyro`, mode `GYRO-ANG`.
- Input 4: `lego-ev3-color`, mode `COL-REFLECT`, units `pct`, decimals `0`.
- Runtime: Pybricks MicroPython 2.0.0, upstream tag `v1.11`, build date `2020-05-06`.

## Stationary readings

After the user finished installation and confirmed that the robot was still, 101 samples were recorded over 11.73 seconds:

| Measurement | Observed value |
| --- | --- |
| Gyro starting / ending angle | -48 degrees / -48 degrees |
| Gyro minimum / maximum | -48 degrees / -48 degrees |
| Net observed gyro change | 0 degrees |
| Color reflection over white table, lens more than 1 cm away | 5% throughout |
| Motor A raw encoder before / after | 22 / 22 |
| Motor B raw encoder before / after | 508 / 508 |

There was no observable gyro change at the sensor's output resolution during this short stationary interval. This is not proof of zero long-term drift or correct orientation/sign. The accumulated angle offset is not itself an error.

The CSV was saved on the brick at `/home/robot/navigating-obstacles/project-01/logs/sensor-check-1586549137.csv` and downloaded to `project-01/logs/sensor-check-2026-10-22.csv` on the laptop. The brick's clock is not synchronized; the numeric filename timestamp must not be treated as the actual test date. Raw laptop logs are ignored by Git.

## Close white-paper check

The user brought white paper close beneath the downward-facing sensing face. Twenty readings at approximately 0.1-second intervals measured:

- Minimum reflection: **83%**.
- Maximum reflection: **85%**.
- Mean reflection: **83.85%**.

This confirms a strong response to nearby white material. The earlier 5% reading over a more distant white table is not an appropriate white calibration point for a near-floor mount. Adjust the mounting height to obtain useful contrast on the actual floor, then compare floor and black material at that same fixed height. Different surface materials also affect the comparison; no black threshold has been selected.

## Garbage collector verified on the actual runtime

- Importing built-in `gc` and calling `gc.collect()` succeeded.
- `gc.mem_free()` reported 8,177,984 bytes before the sample loop and 8,177,632 bytes after the final collection.
- These are two free-heap readings from this diagnostic program, not a memory-leak test or a measurement of the navigation loop's GC pause duration.

## Still pending

- Manual known-angle rotation to verify gyro sensing orientation, turn direction/sign and angle response.
- Longer stationary drift tests representative of a full run.
- Fixed-height color readings over the actual floor and black cardboard/goal material.
- Actual controller imports/self-test, physical motion, motor direction checks and geometry calibration. The earlier full-code deployment is still not activated by these direct sensor diagnostics.

## Subsequent manual gyro direction check

After the floor motor checks, the user manually rotated the robot counterclockwise as viewed from above. The initial turn was not exactly 90 degrees, and its immediate starting reading was not captured; it is not an angular-accuracy calibration. After that turn, 16 reads were steady at -483 degrees in `GYRO-ANG` mode.

Using that stationary -483-degree baseline, the user made a second counterclockwise hand turn. Five subsequent reads at approximately 0.2-second intervals were all -548 degrees, a raw change of -65 degrees. Both motor states were empty and both speeds zero during the checks; no motor commands or gyro mode changes were issued. This confirms **GYRO_CCW_SIGN = -1**, now saved in `src/config.py`. The actual physical angle was not measured, so scale accuracy and measured-angle repeatability remain unverified.

Motor directions have also since been confirmed and a five-second forward check completed; see [motor-check record](motor-check-2026-10-22.md). These later results supersede the corresponding pending items above. Geometry, longer-term drift, actual floor/black color contrast and full controller verification remain pending; overall `CALIBRATED` is still false.

## White tabletop after color-sensor remount

The user remounted the color sensor and returned the robot to a white tabletop. Thirty direct sysfs reads from input 4 in `COL-REFLECT` mode, separated by nominal 0.1-second sleeps, were all **57%** (minimum, maximum and mean 57%). The sensor reported units `pct`, decimals 0. Both motor states were empty and both speeds zero before sampling; this read-only diagnostic issued no motor commands or sensor-mode changes.

This is the new white-tabletop reference for the remounted sensor. The mount height was not measured, and black material and actual course-floor readings at this mounting height remain pending. Do not combine this result with earlier close-paper readings to select a black threshold.

## Black bubble-wrap comparison after remount

The user then placed black bubble wrap beneath the sensor. Thirty direct sysfs reads from input 4 in `COL-REFLECT` mode, separated by nominal 0.1-second sleeps, were all **1%** (minimum, maximum and mean 1%). Both motor states were empty and both speeds zero before sampling; no motor commands or mode changes were issued.

This gives strong observed contrast against the 57% white-tabletop reading at the current mount. It is a stationary comparison with bubble wrap, not calibration against the assignment's flat black cardboard and actual course floor. Bubble-wrap surface height and texture differ from those materials. No production threshold has been configured; repeat on the course materials before selecting one.

## Accepted current color calibration

The user explicitly accepted the remounted-sensor white tabletop (57%) and black bubble wrap (1%) readings as the calibration to use now, superseding the pending-threshold recommendations above. The midpoint is `(57 + 1) / 2 = 29%`. `src/config.py` stores both references and `COLOR_BLACK_THRESHOLD_PERCENT = 29`. Reflection **at or below 29% is black**; above 29% is nonblack. No additional course-material sampling is required before using this selected setting. Actual-course detection performance has not been measured.

`hardware.ColorSensor.is_black(threshold_percent)` reads and classifies one reflection sample. The nonmoving `color-check` command applies the configured threshold to one read and prints the value and decision. Both reject unexpected sensor modes rather than changing modes. Classification is separate from location-gated goal confirmation, which remains a future navigation integration step.
