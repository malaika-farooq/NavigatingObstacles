# Adversarial build and odometry review

Reviewed 22 October 2026 against the assignment and version 1 of this build companion. Revision 2 addresses the documentation and design decisions below. No physical robot, kit inventory, motor code, or course trials were available; mechanical fit and navigation performance remain unproven.

## Verdict

The official driving base is a sensible starting point. The original companion was too easy to interpret as a validated custom build and gave too much attention to optional seam localization before proving basic motion. It was a planning and calibration guide, not a verified custom LEGO assembly specification.

Use a **task-specific adaptation of the stock base**, with the stock drivetrain, wheel supports, and caster preserved. Add the official gyro module, secure cables, and establish repeatable starting alignment. Add the color module only after the baseline works and its mounting and clearance are checked. Make individual mechanical changes in response to observed failures. There is insufficient evidence to justify a replacement chassis.

The architecture is plausible for this assignment's tolerance for occasional dead-reckoning failures. It does not establish reliable navigation through arbitrary permitted configurations. That conclusion needs measured footprint, route clearance, and repeated full-route error measurements.

## Findings, highest priority first

| Priority | Failure being challenged | Consequence | Revision / remaining evidence |
| --- | --- | --- | --- |
| High | No measured relationship between turning radius, course clearance, and navigation error | A compact-looking robot can still cross obstacles after an otherwise small heading error | Added a clearance calculation and intermediate-checkpoint trials. Actual radius and errors remain to be measured. |
| High | Color and gyro modules are individually official, but their combined fit and parts budget are unverified | The builder reaches an occupied mounting point or runs out of parts and improvises a flexible mount | Baseline now needs only the stock base and gyro. Color is an optional later integration. Combined fit remains unresolved. |
| High | Gyro feedback is mistaken for complete position correction | Wheel slip and distance-scale error can accumulate while heading looks correct | Explicitly limits the claim to finite-run dead reckoning. Landmark correction is disabled until independently validated. |
| High | Motion aborts stop the motors but leave an unreliable pose estimate | Resuming from the old estimate can immediately invalidate the planned clearance | Added stop, mark pose uncertain, and physically realign/restart unless independent localization recovers pose. |
| High | Perfectly reset starting placement hides real deployment error | Calibration trials look better than demonstration runs | Require independent start placement each trial and include start error in the route budget. |
| Medium | A different chassis is assumed to be more robust | New alignment, rigidity, traction, and parts issues increase development time | Retain official geometry. Modify only a measured weakness and change one thing at a time. |
| Medium | Optional seam sensing becomes a core dependency | Lighting, grout variation, ambiguous seams, and black objects produce incorrect pose corrections | Seam correction starts disabled. If used, match expected seams in a bounded pose window and account for lens offsets. |
| Medium | Adding a forward sensor increases turning radius more than it helps | The additional localization aid consumes the passage clearance it was meant to protect | Compare radius before and after fitting; shorten or omit the module if it dominates the envelope. Custom mount details need physical verification. |
| Medium | “Slower is better” is applied without testing duration | A very long run accumulates more bias exposure and repeated turn/settle overhead | Compare smooth low and moderate speeds on complete routes. Retain controlled acceleration and endpoint slowdown. |
| Medium | Only final square closure is checked | Opposing errors cancel at the endpoint while intermediate turns cut into obstacles | Require physical measurements at corridor entrances, tight turns, and intermediate checkpoints. |
| Medium | Relative turns and nominal segment lengths are executed without considering actual estimated pose | Turn and segment errors propagate through an otherwise valid planned route | Use absolute map headings and recompute motion from estimated pose; check any corrective path for clearance. |
| Medium | Conservative circle or coarse grid rejects a feasible configuration | The implementation fails the arbitrary-configuration objective even though a physical route exists | Distinguish conservative-model or discretization failure from actual geometric impossibility. Refine the grid or footprint model when needed; never weaken collision checks silently. |
| Medium | Bracing, payload relocation, or a long sensor mount is added automatically | A working base gains twist, drag, or vibration | No default custom bracing or brick relocation. Reseat pins first; brace only observed movement. |
| Low | Too many software concerns are introduced before signs and stopping work | Debugging hardware, control, localization, and planning simultaneously becomes slow | Keep the hardware adapter small. Complete sign, stop, straight, and turn tests before planning or landmarks. |

## A concrete clearance challenge

For a centered straight through a 0.61 m corridor, centerline-to-obstacle clearance is 0.305 m. With a conservative circular footprint of measured radius `R`, the available position-error allowance is:

```text
A = 0.305 - R
```

For illustration only, `R = 0.18 m` leaves `A = 0.125 m`. Over a 2 m straight, a constant 3° heading error creates approximately `2 sin(3°) = 0.105 m` lateral error. With 0.02 m start-position error in the same direction, almost the entire allowance is gone. This does not include additional slip or stopping error.

A hypothetical 1% distance-scale error contributes 5 cm over 5 m of straight travel. A gyro cannot correct that distance scale. These are sensitivity calculations, not measured EV3 error predictions. LEGO documents gyro tolerance, startup stillness, motor slack, and turn overshoot in its [turning lesson](https://education.lego.com/en-us/lessons/ev3-space/turn-using-sensor/); sensor accuracy alone is insufficient to establish route accuracy.

For an actual route use `A = c_min - R`, where `c_min` includes every segment, turn, exact start/goal connection, and workspace edge. Use repeated route measurements plus reserve to select an error allowance. A fixed-radius model is deliberately conservative and can reject routes that a more accurate oriented footprint could traverse.

## Simplest recommended configuration

1. Build the official Driving Base without changing the drivetrain or wheel supports.
2. Add the official gyro mount and secure the three cables inside the footprint.
3. Mark the wheel-midpoint reference and forward direction on the robot without adding protrusions. Use a removable alignment aid during setup if permitted.
4. Verify signs, startup drift, straight travel, both turn directions, and real tile-seam crossings.
5. Measure the footprint and evaluate representative full routes before adding features.
6. Add one downward color sensor only when its goal confirmation or proven seam information is worth the extra mounting, clearance, and code. Recalibrate after fitting it.

Do not initially add a scanner, second color sensor, tracks, extra gear train, new chassis, or complex fusion algorithm. The flat obstacle material makes forward ranging an unsuitable primary avoidance strategy. The assignment does not require an independent goal sensor; it requires reaching the goal without crossing obstacles or leaving the workspace.

## Changes worth making only when tests justify them

| Observation | Smallest useful mechanical response | What to retest |
| --- | --- | --- |
| A frame joint visibly moves | Reseat its pins; if necessary brace that joint without changing wheel spacing | Wheel contact, rubbing, straight runs, turns |
| Sensor boom dominates radius | Shorten and rigidly support it using confirmed kit attachment points | Lens height, offsets, sensor readings, radius, full routes |
| Caster catches a seam or unloads a tire | Inspect caster assembly, clearance, frame twist, and weight distribution | Seam crossings in both directions and turns |
| Tire travel differs consistently | Check tire seating, rubbing, alignment, and load before tuning wheel scale | Straight travel and independent distance measurements |
| Stock geometry cannot meet clearance after these fixes | Consider a shorter chassis or a more accurate footprint planner | New design needs a parts list, verified mounts, and complete recalibration |

The drawings remain conceptual. A buildable custom chassis would need actual part selection, hole-by-hole connections, axle support verification, simultaneous sensor mounting, and physical fit testing. Renaming a schematic a custom build would not resolve those tasks.

## Acceptance before calling it robust

- Confirm the actual workspace dimensions; the supplied PDF contains overlaid conflicting dimensions. Confirm the goal-arrival criterion and the separately stated library rule before implementation depends on them.
- Measure `R`, wheel scale, sensor offsets if fitted, and repeatable start-placement error.
- Run stationary gyro tests for the expected route duration and check physical turning error independently.
- Perform initial repeated straight and turn trials, retaining all failures in the reliability record. Exclude slipping runs only from wheel-scale fitting, not from success-rate reporting.
- Use full routes containing the narrowest intended passage, longest straight, many turns in both directions, real seams, and realistic battery conditions. Measure intermediate deviations and endpoint error.
- As an initial project acceptance screen, require ten consecutive unassisted full-route successes without crossing obstacles or boundaries, while checkpoint errors remain below the available allowance with chosen reserve. This is a proposed engineering screen, not a rubric or a reliability guarantee.
- On failure, fix the observed source; repeat affected calibration and route checks. Do not hide failures by snapping pose to a waypoint, accepting an ambiguous seam, or shrinking the clearance allowance.

The build is ready to assemble and evaluate as an official-base adaptation. It is **not yet validated as robust**; that status depends on the physical evidence above.
