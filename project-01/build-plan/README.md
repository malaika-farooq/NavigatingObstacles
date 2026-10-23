# EV3 build companion

See [CURRENT_PLAN.md](../CURRENT_PLAN.md) for the actual build's completed checks and remaining measurements. Both motor forward signs and gyro CCW sign are confirmed -1; kit wheels are nominally 56 mm diameter. The remounted color sensor uses the user-accepted 29% black threshold. Wheel spacing remains deferred; the original printable guide is a build reference, not the current calibration record.

Current builder-confirmed wiring: **left motor A, right motor B, gyro input 1, color input 4**. The PDF/SVG diagrams retain earlier proposed wiring and conceptual layouts; use `../src/config.py` and the actual front-caster build for current assignments.

Open [the printable, 12-page build plan](ev3-build-plan.pdf). Start with page 1 and keep the linked official LEGO manuals open for exact part, pin, hole, and axle placement. Read the [adversarial review](adversarial-review.md) for the design's unresolved risks and the reasons behind revision 2.

The original vector diagrams are also available separately:

- [Top layout and turning envelope](01-top-layout.svg)
- [Side and front mounting views](02-side-front.svg)
- [Recommended wiring](03-wiring.svg)

The guide covers parts gathering, assembly checkpoints, sensor mounting, cable routing, geometry measurement, odometry equations, calibration trials, software milestones, and a printable bench worksheet.

These diagrams describe a proposed functional arrangement. They are not dimensioned LEGO CAD, and the combined gyro/color mounting arrangement and spare-parts budget have not been physically validated. Follow the official modules first, then check compatibility on the actual kit. All suggested speeds, sensor gaps, and error allowances require testing on the course floor.

The recommended first build is the stock driving base plus gyro, secured cables, and repeatable starting alignment. Color sensing is optional; seam correction starts disabled. Make task-specific changes only when measurements show a need: shorten a protruding sensor mount, brace an observed loose joint, or fix a caster clearance problem. A different chassis is not justified yet.

## Official assembly references

- [Driving Base](https://assets.education.lego.com/v3/assets/blt293eea581807678a/bltc8481dd2666822ff/5f8801e3f4f4cf0fa39d2fef/ev3-rem-driving-base.pdf)
- [Color Sensor Down](https://assets.education.lego.com/v3/assets/blt293eea581807678a/blt8b300493e30608e9/5f8801dfb8b59a77a945d13c/ev3-rem-color-sensor-down-driving-base.pdf)
- [Gyro Sensor](https://assets.education.lego.com/v3/assets/blt293eea581807678a/bltc961107e6587a579/5f8801dd3b19d21d4a6085bf/ev3-gyro-sensor-driving-base.pdf)

The official manuals are linked, not copied into the repository. Original diagrams and the PDF can be regenerated with Python and matplotlib:

```bash
python project-01/build-plan/generate_build_plan.py
```

No robot code or additional runtime robotics dependencies are introduced by this documentation.
