# Fire Alarm Robot: Implementation Brief

CSE 4360 / 5364 Project 2 (Behavior-based Robot Control). Demo and report due November 23, 2026, 2:30 pm.

This brief is written for the agent implementing the control software. It describes the sensors, the algorithm, the code structure, and what must be verified or measured on the real robot before the numbers here can be trusted.

## 0. Read this first

- **Nothing in this document has been run on hardware.** The design was worked out on paper. Every numeric value is a starting point for tuning.
- **The physical robot was built before this design was written and may not match it.** Section 3 lists what to confirm with the team. Section 4 lists every measurement to redo. Do both before writing behavior code.
- **The software stack is not confirmed.** Ask the team which one the course requires (ev3dev C, ev3dev Python, Pybricks MicroPython, or other). All logic below is stack neutral. Put every hardware call behind the small interface in section 6.1 so the stack choice touches one file.
- **All geometry must come from one config file.** Do not hardcode distances or angles in behavior code. Several parameters are derived from measured ones (section 5.2); compute them, do not copy the example values.
- When this brief and the real robot disagree, the robot wins. Report the mismatch to the team and adjust the config.

## 1. Task requirements (from the project handout)

- Environment: an indoor "house" on a tile floor. Walls are about 15 cm high and lie along tile grid lines. No openings to the outside. Start position and fire position are unknown.
- Fire: a burning candle in a glass holder, standing on a differently colored floor area about half a tile in size.
- Required behaviors: **wander** (move through free space to find a wall or the fire), **wall following** (one direction is enough), **goal finding** (detect the fire), **extinguish**.
- Required: an explicit **behavior coordination mechanism** (subsumption, weighted averaging, or similar).
- On finding the fire: **raise an alarm**, then **attempt to extinguish** (fan on the third motor).
- The report must contain a description of the control system and the actual code. Keep the code readable and keep logs from test runs.

## 2. Design summary

**Core idea: follow walls by touch, and point the ultrasonic sensor sideways across the room ("side scan").**

- A spring feeler on the right side plus one touch sensor does right hand wall following.
- The ultrasonic sensor looks left, perpendicular to travel. Because all walls lie on the tile grid, the beam meets the opposite wall square on, which gives clean readings. A free standing candle holder appears as a **narrow dip** in range as the robot drives past.
- Odometry converts the dip into a floor coordinate. The robot leaves the wall, drives to that point, and checks it with the color sensor and bumper. If it is not the fire, it backs up to where it left the wall and carries on.
- A downward color sensor confirms the fire by detecting the colored pad.
- Coverage argument: a candle near a wall is hit directly by the color sensor or bumper during wall following. A candle away from walls is seen as a dip from at least one followed wall. Wander crossings are the fallback.

**Robot layout (as last described by the team):** rear wheel drive, two large motors at the back, ball caster at front center. Full width front bumper. Color sensor between caster and bumper. Ultrasonic on the left side near the rear axle line. Feeler at the front right corner. Fan on a mast above the front, tilted down toward a point just ahead of the bumper.

### 2.1 Port map (intended; confirm)

| Port | Device | Role |
|---|---|---|
| S1 | Touch sensor | Front bumper (one sensor for the full width) |
| S2 | Touch sensor | Right side wall feeler |
| S3 | Color sensor | Floor pad detection, pointing down |
| S4 | Ultrasonic sensor | Side scan, pointing left |
| A | Medium motor | Fan |
| B | Large motor | Left drive wheel |
| C | Large motor | Right drive wheel |

The gyro is intentionally unused. The brick has four sensor ports, and heading drift is handled by the heading snap in section 7.2.

### 2.2 Coordinate conventions

- Robot frame origin: **midpoint of the rear (drive) axle**. This is the pivot point.
- x forward, y left, heading θ counterclockwise positive, in radians internally.
- Sensor offsets are given in this frame. A sensor on the right side has negative y.
- With right hand wall following inside a closed room the robot circulates counterclockwise, so one lap accumulates about +360° of heading. Circling a free standing wall cluster (an island) accumulates about −360°.

### 2.3 How the fire is found: three cues, one decision

The ultrasonic sensor and the color sensor work together, with the bumper as a third cue. They have different jobs and only one of them is allowed to declare a fire.

| Sensor | Range | Job | Can it declare "fire"? |
|---|---|---|---|
| Ultrasonic (left side, opposite the wall feeler) | Up to `SONAR_MAX` | Proposes a candidate: "something free standing is over there" | No. It only triggers Investigate |
| Color sensor (floor) | Contact only | Confirms the colored pad under the candle | **Yes. This is the only cue that sets `fire_confirmed`** |
| Front bumper | Contact only | Flags an object in the path (triggers a color sniff), then gives exact alignment for the fan | No |

- The usual sequence for a mid room candle: sonar dip → Investigate drives there → color sensor crosses the pad → confirmed → dock on the bumper → fan.
- The sequence for a candle near the followed wall: no sonar step at all. The color sensor crosses the pad during wall following, or the bumper touches the holder and the sniff finds the pad.
- The color detector runs on every tick in every behavior. The sonar detector runs only while driving straight.
- If the sonar turns out to be unreliable on glass, the color sensor and bumper still find the fire; the search just takes longer (section 13).

### 2.4 Front bumper: design requirements

These are mechanical requirements for the team. The agent should check them in section 12, step 5 and report any that fail.

- **Type: a hinged flap, not a sliding bar.** Hang one rigid, full width bar from a horizontal axle that runs across the front of the robot, so the bar swings backward like a pendulum when hit. A hit anywhere along the width rotates the whole bar, so a single touch sensor behind the center trips for center and end hits alike. A bar on sliding guides tends to bind when hit off center.
- **Width:** at least the full rigid width of the front, so nothing else can touch a wall first. The one exception is the feeler tip on the right, which must reach a side wall before the bumper corner does.
- **Contact height:** the face should cover roughly 1.5 cm to 6 cm above the floor. Low enough to meet the candle holder near its base (it slides instead of tipping, and short holders are still hit), with at least 1 cm of floor clearance for tile seams.
- **Face shape:** flat and vertical across the middle, so the docked distance to the holder is the same every time. Add short wings angled back about 45° at each end so glancing contact with a wall still pushes the bar and does not snag.
- **Light trigger:** the bar should rest just touching the sensor button so 2 to 3 mm of travel trips it. Use gravity and the sensor's own spring for return; avoid rubber bands, which raise the force. The goal is that the switch trips before the holder starts to slide.
- **Hard stop:** a fixed beam should take the load once the switch has tripped, so the sensor is not what stops the robot.
- **Stiffness:** double the bar if a push at one end flexes it instead of tripping the switch.
- **Clearances:** the swing must not strike the color sensor (just behind the bar, on the centerline) or the caster. The fan's airflow passes over the top of the bar.
- **Nothing ahead of the face:** no cable, sensor, or fan part may protrude in front of the bumper.

### 2.5 Ultrasonic mounting

- **Side:** left, opposite the feeler, facing exactly 90° to the direction of travel.
- **Fore-aft:** as close to the rear axle line as the build allows, which in practice means just ahead of the left wheel. Near the pivot, heading ripple barely moves the sensor and a detected object is almost directly to the robot's left. This is a preference, not a requirement: anywhere from the axle line to mid body works, because the code uses the measured offset `US_X`. Measure it wherever it ends up.
- **Height:** sensor center about 4 to 5 cm above the floor, roughly level with the upper half of the drive wheel. It must sit below the rim of the candle holder or the beam passes over it. Do not mount it on top of the wheel if that puts it higher than the holder.
- **Attitude:** level, not tilted up or down, with the two "eyes" side by side.
- **Clear view:** flush with the left side or slightly inboard, with no wheel, beam, or cable inside the cone in front of it. Keep it at least a few cm clear of the rated 3 cm minimum range from anything fixed.

## 3. Verify with the team before coding

Ask these and record the answers in the config file or a README.

1. Which software stack and language does the course require? Is there a required program structure for the report?
2. Actual port assignments for all four sensors and three motors.
3. Motor polarity: does a positive speed command drive each wheel forward? Does a positive fan command push air forward and down?
4. Is the feeler on the right side? If it was built on the left, mirror everything (follow the left wall, sonar looks right, turn signs flip).
5. Does the feeler press its touch sensor when near the wall, or release it? The code assumes pressed = wall close.
6. Is the front bumper one touch sensor across the full width? If the build used both touch sensors on the bumper (left and right), there is no feeler and the wall follower in section 9.5 does not apply as written. Stop and report.
7. Where exactly are the color sensor and ultrasonic sensor mounted? (Feeds section 4.)
8. Fan gearing and whether it has been tested on a real candle in the real glass holder.
9. Demo rules: May the robot be calibrated on the pad color before the run? How is the run started (button press)? Is touching the candle holder with the bumper acceptable? Is there a time limit?
10. Arena facts: tile size, narrowest doorway or corridor, wall thickness, whether walls can shift when pushed, pad size and color, holder diameter and height, any other markings or tape on the floor.

## 4. Measurements to redo on the real robot

The "assumed" column is what the paper design used. Replace every value.

### 4.1 Robot geometry

| Symbol | Meaning | Assumed | How to measure |
|---|---|---|---|
| `WHEEL_DIAM` | Drive wheel diameter | 5.6 cm | Calibrate by driving (section 12, step 2) |
| `TRACK_WIDTH` | Effective distance between drive wheel contact points | 12 cm | Calibrate by spinning (section 12, step 2) |
| `BUMPER_X` | Axle to front face of bumper | 15 cm | Ruler |
| `ROBOT_W` | Overall rigid width | 16 cm | Ruler |
| `REAR_X` | Axle to rearmost rigid point (positive number) | 4 cm | Ruler |
| `FEELER_X`, `FEELER_Y` | Feeler tip position at the instant the switch trips | (14, −12) cm | Slide a flat board toward the right side until the sensor trips, then measure |
| `FEELER_GAP` | Gap between robot's right side and the wall at the trip point | 4 cm | Same test |
| `COLOR_X`, `COLOR_Y` | Color sensor lens center | (13.5, 0) cm | Ruler |
| `COLOR_HEIGHT` | Lens height above floor | 0.5 to 1.0 cm | Ruler |
| `US_X`, `US_Y` | Ultrasonic sensor face center | (4, +8) cm | Ruler. Any fore-aft position is usable if measured (section 2.5) |
| `US_HEIGHT` | Ultrasonic center height above floor | 4 to 5 cm | Ruler. Must be below the holder rim |
| `BUMPER_LOW`, `BUMPER_HIGH` | Bottom and top of the bumper contact face above the floor | 1.5 cm, 6 cm | Ruler. Compare with holder height |
| Bumper trip travel | How far the face moves before the switch trips | 2 to 3 mm | Push slowly against a ruler. Measure `BUMPER_X` at the tripped position |
| `FAN_AIM_X` | Where the fan axis meets holder height, ahead of the axle | `BUMPER_X` + 3 cm | Sight along the fan axis |

### 4.2 Environment

| Symbol | Meaning | Assumed | Note |
|---|---|---|---|
| `TILE` | Floor tile side | 30.5 cm | Measure |
| `MIN_GAP` | Narrowest doorway or corridor | one tile | Ask or measure |
| `PAD_MIN` | Shortest side of the colored pad | 15 cm | Worst case assumption |
| `HOLDER_RADIUS` | Candle holder radius | 3.5 cm | Measure |
| Holder height | | below 10 cm | Decides sonar height and fan angle |
| Floor seams | Dark grout lines between tiles | present | The color detector must ignore them |

### 4.3 Sensor behavior (measure with logging scripts, section 12)

- **Loop period actually achieved** with all sensors read every tick. Target 20 ms or better. If it is slower than about 40 ms, lower `V_CRUISE`.
- **Ultrasonic update rate**, and what it returns when nothing is in range (often 255) and when an object is closer than its minimum range (rated minimum is 3 cm).
- **Ultrasonic detection of the real glass holder** at 10, 30, 50, 70, 90 cm side distance while driving past at cruise speed. This sets `SONAR_MAX`. This is the single most important test; see section 13.
- **Color sensor raw RGB** over bare floor, over tile seams, close to walls, and over the pad. This sets the color thresholds.
- **Maximum reliable wheel speed** and whether the wheels slip during pivots (compare commanded and actual rotation over 10 turns).

## 5. Configuration

### 5.1 Tunable parameters (starting values)

| Name | Start | Meaning |
|---|---|---|
| `DT` | 0.02 s | Target loop period |
| `V_CRUISE` | 18 cm/s | Wander and wall follow speed |
| `V_APPROACH` | 12 cm/s | Investigate approach speed |
| `V_DOCK` | 4 cm/s | Final creep toward the candle |
| `V_REVERSE` | 10 cm/s | Backing up |
| `W_PIVOT` | 90 °/s | In place turn rate |
| `ACCEL_LIMIT` | 40 cm/s² | Ramp on linear speed commands |
| `TRACK_RADIUS` | 60 cm | Arc radius for the bang-bang wall follower |
| `LOST_DIST` | 3 cm | Feeler released this far, after contact, means the wall ended |
| `SEEK_MAX` | 30 cm | Max straight travel while seeking the wall after a corner |
| `CORNER_PIVOT` | 78° | Left pivot at an inside corner (less than 90° so the nose angles toward the new wall) |
| `WRAP_MAX` | 270° | Give up wrapping a wall end after this much turn |
| `SNIFF_ANGLE` | 25° | Color sweep pivot after an unexplained bump |
| `SNAP_WINDOW` | 15 cm | Travel window for the heading snap |
| `SNAP_MAX_ERR` | 20° | Largest correction the snap may apply |
| `DIP_DEPTH` | 6 cm | Range drop that starts a sonar dip |
| `BASE_WIN` | 8 cm | Travel window for the sonar baseline median |
| `DIP_W0`, `DIP_WK` | 12 cm, 0.5 | Max dip width = `DIP_W0` + `DIP_WK` × range |
| `DIP_MIN_N` | 3 | Min samples inside a dip |
| `SONAR_MIN`, `SONAR_MAX` | 6 cm, 70 cm | Accepted dip range. Set `SONAR_MAX` from the bench test |
| `SONAR_FAR` | 200 cm | Value substituted for "no echo" readings |
| `CHECKED_RADIUS` | 25 cm | Skip dips this close to an already investigated point |
| `ANOM_DIST` | 1.5 cm | Color anomaly must persist over this much sensor travel |
| `T_INT`, `T_CHROMA` | 0.35, 0.08 | Color anomaly thresholds (relative intensity, chromaticity distance) |
| `DOCK_MAX` | 12 cm | Max creep distance in the dock step |
| `FAN_TIME`, `FAN_REPEATS` | 8 s, 2 | Fan run time and repeats |
| `FAN_SWEEP` | 15° | Pivot sweep each side while blowing |
| `CLOSE_RADIUS` | 30 cm | Loop closure position tolerance |
| `CLOSE_MIN_PATH` | 100 cm | Min path before loop closure is tested |
| `BORED_PATH` | 2500 cm | Wall following path length that forces a wander crossing |
| `STUCK_TIME` | 3 s | No progress timeout |

### 5.2 Derived parameters (compute from measurements)

| Name | Formula | Example |
|---|---|---|
| `SWEEP_RADIUS` | hypot(`BUMPER_X`, `ROBOT_W`/2) | 17.0 cm |
| `ESC_BACK` | `SWEEP_RADIUS` − `BUMPER_X` + 1 cm | 3.0 cm |
| `WRAP_RADIUS` | `ROBOT_W`/2 + `FEELER_GAP` | 12 cm |
| `WALL_END_ADVANCE` | `FEELER_X` + 1 cm | 15 cm |
| `W_TRACK` | `V_CRUISE` / `TRACK_RADIUS` | 0.30 rad/s |

If 2 × `SWEEP_RADIUS` is larger than `MIN_GAP` minus wall thickness, the robot cannot spin in place in the narrowest corridor. That is expected for the rear drive build. The "bump during pivot" rule in section 9.4 handles it. Tell the team the computed value.

## 6. Software architecture

One cooperative loop. No blocking calls anywhere in behavior code: no sleeps, no "turn N degrees and wait" library calls. Every maneuver is a small state machine that compares odometry against a target on each tick.

```
every DT:
    raw = hal.read_all()            # encoders, 2 touch, rgb, sonar, clock
    odom.update(raw)                # pose, path length, unwrapped heading
    percepts.update(raw, odom)      # bump edges, feeler, color anomaly, sonar dips, stuck
    for b in behaviors:             # fixed order, highest priority first
        b.update(percepts, odom)    # advance own state machine, set b.command or None
    cmd = arbiter.select(behaviors) # first non-None wins; others are told they are suppressed
    hal.drive(cmd.v, cmd.w)         # converts to wheel speeds
    hal.fan(cmd.fan), hal.alarm(cmd.alarm)
    log.write(...)
```

### 6.1 Hardware interface (the only stack specific file)

```
read_all() -> { t, encL_deg, encR_deg, bumper: bool, feeler: bool, rgb: (r,g,b), sonar_cm }
drive(v_cm_s, w_rad_s)      # vL = v − w·B/2, vR = v + w·B/2, then cm/s → deg/s = v / (π·D) · 360
stop(brake: bool)
fan(power)                  # −100..100, 0 = off
alarm(on: bool)             # short beep pattern + red LEDs; must not block longer than one tick
button_pressed() -> bool
```

Use speed regulated motor commands. Apply `ACCEL_LIMIT` in `drive`. Put the color sensor in raw RGB mode and the ultrasonic in continuous distance mode once at startup; do not switch modes during the run.

### 6.2 Suggested files

- `config` (all of sections 4 and 5)
- `hal` (section 6.1)
- `odometry` (section 7)
- `percepts` (section 8)
- `behaviors` (section 9, one unit per behavior)
- `arbiter` and `main`
- `calib_*` scripts (section 12)
- `log` (CSV: time, pose, raw sensors, percept flags, active behavior, substate, command)

## 7. Odometry

### 7.1 Update

```
dL = (encL − encL_prev) · π · WHEEL_DIAM / 360
dR = (encR − encR_prev) · π · WHEEL_DIAM / 360
ds = (dL + dR) / 2
dθ = (dR − dL) / TRACK_WIDTH
x += ds · cos(θ + dθ/2)
y += ds · sin(θ + dθ/2)
θ += dθ                      # keep θ unwrapped; wrap only when comparing angles
path += |ds|
```

Helper: `sensor_pos(ox, oy) = (x + ox·cosθ − oy·sinθ, y + ox·sinθ + oy·cosθ)`.

### 7.2 Heading snap (replaces the gyro)

Walls are axis aligned, so while tracking a straight wall the mean heading equals the wall direction.

- Keep a rolling record of heading over the last `SNAP_WINDOW` of travel, only while WallFollow is in its TRACK substate.
- The window qualifies if the feeler changed state at least twice in it (proof of real contact) and max heading minus min heading is under 10°.
- **First qualifying window of the run:** this defines the grid frame. Let m = mean heading. Rotate the current pose and every stored point by −m about the origin, then set θ so the mean is exactly 0.
- **Later windows:** err = nearest multiple of 90° − m. If |err| < `SNAP_MAX_ERR`, add err to θ. Do not move x, y.
- Log every snap with its correction. Corrections that are regularly larger than a few degrees mean `TRACK_WIDTH` is wrong or the wheels are slipping.

### 7.3 What odometry is used for

1. Measured maneuvers (every pivot, back up, advance).
2. Locating sonar dips on the floor and driving to them.
3. Loop closure and the island test (section 9.6).
4. The list of already investigated points.
5. Sensor travel distance for the color detector.
6. Stuck detection.

## 8. Perception

### 8.1 Bumper and feeler

- Debounce both over 2 consecutive ticks.
- Expose `bump_edge` (rising edge) and `bumper` (level).
- Feeler: expose level, `dist_since_pressed` (path length since it was last pressed), and `ever_pressed_this_wall`.

### 8.2 Floor color anomaly detector

Goal: detect "not the normal floor" for an unknown pad color, while ignoring tile seams.

- **Startup baseline:** robot stationary on bare floor. Take 50 RGB samples. Compute mean intensity I0 = R+G+B and mean chromaticity c0 = (R/I, G/I). Also compute the standard deviations.
- **Per tick:** I = R+G+B, c = (R/I, G/I).
  - `score_int` = |I − I0| / I0 / `T_INT`
  - `score_chroma` = distance(c, c0) / `T_CHROMA`
  - anomalous if max(score_int, score_chroma) > 1
- Raise each threshold to at least 4 standard deviations of the startup samples (speckled tiles are noisy).
- **Persistence:** accumulate sensor travel while anomalous, where sensor travel per tick = |ds| + `COLOR_X` × |dθ| (so it also works during pivots). Reset to zero on any normal sample. `pad_detected` becomes true when the accumulated travel reaches `ANOM_DIST`.
- **Optional, if the demo rules allow:** record the pad's RGB signature beforehand and require the sample to be closer to the pad signature than to the floor baseline. This cuts false positives from tape or stains.
- If I is near zero (sensor lifted or over a gap), treat as normal, not anomalous.

### 8.3 Sonar dip detector

Runs only while driving straight: WallFollow in TRACK or Wander in CRUISE, and heading within 8° of its recent mean. Reset fully whenever those conditions stop holding.

- Replace any reading at or above the sensor's "no echo" value with `SONAR_FAR`.
- Keep a buffer of (path, range, pose) samples covering the last `BASE_WIN` of travel. `baseline` = median range in the buffer. Samples taken during a dip do not enter the buffer.
- **IDLE:** if range < baseline − `DIP_DEPTH`, start a dip. Store start path s0, base0 = baseline, r_min = range, n = 1, and start recording poses.
- **IN_DIP:** update r_min and n each tick.
  - If range > base0 − `DIP_DEPTH`/2, the dip has ended at path s1. Evaluate it.
  - If (path − s0) exceeds `DIP_W0` + `DIP_WK` × r_min, this is a step (a wall or wall segment), not a dip. Abandon it, clear the buffer so the baseline re-forms at the new level, return to IDLE.
- **Accept** if n ≥ `DIP_MIN_N` and `SONAR_MIN` ≤ r_min ≤ `SONAR_MAX`.
- **Target point:** take the pose recorded nearest the dip midpoint (s0+s1)/2. From it compute the sensor position with (`US_X`, `US_Y`). Target = sensor position + (r_min + `HOLDER_RADIUS`) × unit vector pointing left of that pose's heading.
- Discard the target if it is within `CHECKED_RADIUS` of any point in the checked list.
- Otherwise publish a `blip` event with the target.

Known false positive: the thin end of a wall pointing at the robot looks like a narrow object. That is acceptable. Investigate rejects it once and remembers it.

### 8.4 Stuck detector

If a behavior has commanded motion for `STUCK_TIME` and the pose has moved less than 2 cm and turned less than 20°, set `stuck`. Also set `stuck` if any single behavior substate lasts longer than 15 s (except Extinguish).

## 9. Behaviors

Priority, highest first. Each returns a command or None.

| # | Behavior | Becomes active when |
|---|---|---|
| 1 | Extinguish | `fire_confirmed` (latched for the rest of the run) |
| 2 | Identify | `pad_detected`, or `bump_edge` that has not been explained |
| 3 | Investigate | `blip` event, until its trip is finished |
| 4 | Escape | Unexplained bump while in WallFollow or Wander, or `stuck` |
| 5 | WallFollow | `have_wall` is true |
| 6 | Wander | Always (default) |

Shared flags: `have_wall`, `fire_confirmed`, `bump_unresolved`.

### 9.1 Extinguish (latched)

1. **ALARM:** stop. Turn the alarm on. It stays on through all later steps.
2. **DOCK:** creep forward at `V_DOCK` until the bumper presses (touching the holder), or `DOCK_MAX` is traveled, or the color anomaly ends (driving off the pad). If the bumper pressed, back up 1 cm.
3. **BLOW:** fan at full power. Pivot slowly between +`FAN_SWEEP` and −`FAN_SWEEP` around the docked heading for `FAN_TIME`.
4. Fan off for 1 s. Repeat BLOW until `FAN_REPEATS` is reached.
5. **DONE:** stop, alarm stays on until a button press.

There is no flame sensor, so the robot cannot confirm the flame is out. That is acceptable per the handout ("attempt to extinguish").

### 9.2 Identify (goal identification)

- If `pad_detected`: set `fire_confirmed`. Done.
- On an unexplained `bump_edge`:
  - If `have_wall` and the feeler was pressed within the last 5 cm of travel, the wall is on the right and Escape's left pivot will sweep the color sensor leftward anyway. Skip the sniff: set `bump_unresolved` and yield.
  - Otherwise **SNIFF:** back up 1 cm, pivot right by `SNIFF_ANGLE`, pivot back to the original heading. The color detector runs throughout. If `pad_detected` occurs, set `fire_confirmed`. If not, set `bump_unresolved` and yield.
- The color detector stays live in every other behavior too, so a pad crossed at any time triggers Identify.

### 9.3 Investigate (goal finding)

On a `blip` with target T:

1. **SAVE:** record the current pose P0. Stop.
2. **AIM:** pivot in place to face T.
3. **APPROACH:** drive straight at `V_APPROACH`. Stop when the distance driven reaches dist(P0, T) − `BUMPER_X` + 5 cm, or on `bump_edge`, or on `pad_detected`.
   - `pad_detected` hands control to Identify and then Extinguish.
   - A bump goes through Identify's sniff first. If it comes back `bump_unresolved`, Investigate handles it itself (go to RETURN). Escape must not take it.
4. **RETURN:** reverse straight by the exact distance driven in APPROACH. Pivot back to P0's heading. Add T to the checked list. Clear `bump_unresolved`. Finish.

After Investigate finishes, WallFollow resumes in its SEEK substate.

### 9.4 Escape

Triggered by `bump_unresolved` (from WallFollow or Wander) or `stuck`.

- **Normal (bump):** reverse `ESC_BACK`. Pivot left by `CORNER_PIVOT`. Then set `have_wall` = true and put WallFollow in SEEK. The wall that was hit is now on the right.
- **Bump during the pivot** (expected in tight spaces because the nose swings wide): reverse 2 cm and continue pivoting to the same target heading. Allow up to 5 of these, then treat as stuck.
- **Stuck:** reverse 5 cm, pivot left by a pseudo-random angle between 90° and 180°, set `have_wall` = false.

### 9.5 WallFollow (right hand, by touch)

Active while `have_wall`. Substates:

- **SEEK** (entered after Escape or Investigate): drive straight at `V_CRUISE`.
  - Feeler pressed: go to TRACK.
  - `SEEK_MAX` traveled with no contact: go to WRAP.
- **TRACK:**
  - Feeler pressed: command (`V_CRUISE`, +`W_TRACK`), a gentle arc left, away from the wall.
  - Feeler released: command (`V_CRUISE`, −`W_TRACK`), a gentle arc right, toward the wall.
  - If the feeler has been pressed at least once in this TRACK episode and `dist_since_pressed` > `LOST_DIST`: the wall has ended. Go to ADVANCE.
- **ADVANCE:** drive straight until the total distance since the feeler was last pressed reaches `WALL_END_ADVANCE`. This brings the axle level with the wall end. If the feeler presses again on the way, return to TRACK.
- **WRAP:** arc right with radius `WRAP_RADIUS`, i.e. command (`V_CRUISE`·k, −`V_CRUISE`·k / `WRAP_RADIUS`) with k around 0.6.
  - Feeler pressed: go to TRACK.
  - Turned more than `WRAP_MAX` with no contact: set `have_wall` = false (Wander takes over).
- A front bump in any substate is handled by Identify and then Escape (inside corner).

Notes:

- The result should look like a single sensor line follower: a small ripple along the wall. If the ripple is large, increase `TRACK_RADIUS` or shorten the loop period.
- Optional refinement: low-pass the feeler state over about 0.2 s and steer in proportion to (duty − 0.5). Only do this if plain bang-bang is too rough.

### 9.6 Wander, loop closure, and islands

- **CRUISE:** drive straight at `V_CRUISE`. The sonar dip detector is active. A bump leads through Identify and Escape, which sets `have_wall`.
- **On acquiring a wall** (`have_wall` goes true): record the acquisition pose, path length, and unwrapped heading.
- **Loop closure test**, each tick while wall following: path since acquisition > `CLOSE_MIN_PATH`, position within `CLOSE_RADIUS` of the acquisition position, and heading within 30° of the acquisition heading modulo 360°. When it fires, look at net turn = unwrapped heading now − unwrapped heading at acquisition:
  - near −360°: the robot circled an **island**. Start a crossing.
  - near +360°: the robot completed a **lap** of an enclosing boundary without finding the fire. Start a crossing.
- **Boredom:** if path since acquisition exceeds `BORED_PATH` (odometry drift can make closure fail on a long lap), start a crossing.
- **CROSSING:** pivot left by the crossing angle (90° the first time, then pseudo-random between 45° and 135°), set `have_wall` = false, go to CRUISE.

Use both the position check and the turn sign together. Net turn alone can reach −360° on a non-island boundary with many wall ends.

## 10. Arbitration

Fixed priority suppression (subsumption style). On each tick the highest priority behavior with a command wins the actuators. A behavior that was running and loses control is told so, and must reset to a safe substate when it regains control (WallFollow re-enters via SEEK). Extinguish never releases once active. Log the winning behavior and its substate every tick; the report can use this trace to show the coordination mechanism working.

## 11. Startup sequence

1. Initialize sensors and modes. Zero the encoders and pose.
2. Wait for a button press with the robot stationary on bare floor.
3. Take the color baseline (section 8.2).
4. Brief fan spin (0.3 s) as a self test, then off.
5. Enter the main loop with `have_wall` = false (Wander).

## 12. Calibration and logging scripts to write first

1. **Port and polarity check:** print every sensor live; jog each motor forward briefly.
2. **Odometry calibration:**
   - Drive straight by a commanded 200 cm. Measure the true distance. Scale `WHEEL_DIAM`.
   - Spin in place by a commanded 10 full turns. Measure the true angle. Scale `TRACK_WIDTH`.
   - Repeat until the straight error is under 1% and the spin error is under 1°.
3. **Color logger:** log raw RGB while pushing the robot by hand over floor, seams, near walls, and the pad. Choose `T_INT` and `T_CHROMA` so the pad scores well above 1 and everything else stays under about 0.5.
4. **Sonar logger:** drive straight past the real candle holder at several side distances and log path against range. Also log a pass along a plain wall and a pass by a wall end. Tune the dip parameters against these logs offline.
5. **Feeler and bumper check:**
   - Feeler: measure the trip gap; confirm it trips and releases cleanly without sticking.
   - Bumper: press with one finger at the left end, the center, and the right end. All three must trip and release.
   - Bumper against the real holder: drive into it at `V_APPROACH` and at `V_DOCK`. The switch must trip before the holder slides more than about 1 cm. If it slides first, the trigger is too stiff (section 2.4) or the speed is too high.
   - Bumper against a wall at a 45° angle from each side: must trip, must not snag.
6. **Fan test:** real candle, real holder, robot docked by hand. Record whether and how fast the flame goes out. If it does not, this is a mechanical problem (gearing, tilt, aim) to return to the team.

## 13. Bring up order and pass criteria

Do these in order. Do not move on until each passes.

| Step | Test | Pass |
|---|---|---|
| 1 | Sonar bench test with the real holder (script 4) | Clear dip at 30 cm or more. Record the max reliable distance as `SONAR_MAX` |
| 2 | Odometry calibration (script 2) | Errors as in section 12 |
| 3 | WallFollow along a straight wall, then an inside corner, then a wall end, then a one tile dead end | 10 clean passes of each |
| 4 | Heading snap | Corrections stay small over a 5 m follow |
| 5 | Color detector across pad, seams, and near walls | Pad always detected, zero false triggers over a full lap |
| 6 | Extinguish from a hand placed start | Docks, alarms, blows out the candle |
| 7 | Dip detector and Investigate | Finds a mid room candle; rejects a wall end and resumes at the same wall |
| 8 | Loop closure and island handling | Correct sign on a room lap and on a free standing wall |
| 9 | Full runs from random starts | Record time to find and any failures |

**If step 1 fails** (the glass holder is not detected beyond about 30 cm): keep the robot as built, disable Investigate and the dip detector, lower `BORED_PATH` to about 300 cm so wander crossings happen often, and tell the team. Everything else is unchanged.

## 14. Known risks and edge cases

- **Sonar on glass** is the main unknown (step 1).
- **Wide nose swing:** pivots will touch walls in tight spaces. The multi-point rule in 9.4 covers it; confirm in the dead end test.
- **Pushing the candle:** the bumper may slide a light holder before the switch trips. Keep approach and dock speeds low. If it slides, lower `V_APPROACH` and rely more on color detection before contact.
- **Candle close to a wall or in a corner:** the sonar dip merges with the wall step and is rejected. Wall following should then cross the pad directly. Test this placement explicitly.
- **Feeler snagging** on wall ends or board joints. Check during step 3.
- **Sonar minimum range:** objects closer than a few cm to the left side give invalid readings. Ignore ranges below `SONAR_MIN`.
- **Wheel slip** during pivots if too much weight sits on the front caster. Shows up as large heading snap corrections.
- **False color triggers** from tape, stains, or the sensor passing over a wall base. Use the pad signature option if allowed.
- **Two robots or other ultrasonic sources** in the lab can corrupt sonar readings.

## 15. What to hand back to the team

- Source code, organized as in section 6.2, with the config file holding every measured and tuned value.
- The calibration scripts and the logs they produced.
- A short list of every place the real robot differed from this brief and what was changed.
- A one page description of the behaviors and the arbitration scheme for the report, plus one logged run showing behavior switching over time.
- Any open mechanical issues (fan strength, feeler, weight balance) that software cannot fix.
