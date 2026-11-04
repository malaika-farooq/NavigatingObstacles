# Project 1: Navigating an obstacle course with a LEGO EV3

CSE 4360/5364 Autonomous Robots. Team: Malaika Farooq, Nick Truong, Riya Dsouza.

An EV3 robot drives from a known start to a goal circle (radius 0.305 m) through a known
obstacle course, using only its wheel encoders and a gyro (dead reckoning). The robot code uses
only built-in MicroPython modules. 
## How it works

1. `course.py` holds the start, goal and obstacles in the assignment's header format.
2. `planner.py` grows each obstacle by the robot radius plus a safety allowance, runs a wavefront
   (Manhattan distance) search on a half-tile grid, and returns a route of axis-aligned legs, so
   every turn is 90 degrees.
3. `navigation.py` follows the route: turn in place with the gyro, drive the leg with wheel speed
   control and heading correction, stop and settle.

The robot has two rear drive wheels and a front caster. It uses a gyro on input 1. The left motor is
on port B and the right motor is on port A. Measured values and calibration are in `src/config.py`.

## Layout

```text
src/
  course.py       Start, goal and obstacles (edit this for a new course)
  config.py       Ports, measured robot dimensions, calibration values
  planner.py      Obstacle growing, wavefront search, route validation
  geometry.py     Collision and angle helpers
  control.py      Heading and wheel speed control calculations
  motion.py       Waypoint-to-motion calculations
  odometry.py     Dead reckoning from the encoders and gyro
  navigation.py   Turn / drive / settle controller with fault handling
  hardware.py     Direct ev3dev motor and sensor access
  runner.py       Run loop with safety stops and logging
  main.py         Command entry point
scripts/ev3.py    Laptop tool: deploys the code to the robot over SSH
REPORT.docx       Project report (includes the code listing)
```

## Run a course

1. Put the start, goal and obstacles in `src/course.py` (units are meters, origin at the
   lower-left corner of the workspace).
2. Preview the route on the laptop, no robot needed:

   ```bash
   python3 src/main.py plan
   ```

3. Copy the code to the robot (needs the EV3 connected by USB, ssh access to `robot@ev3dev.local`):

   ```bash
   python scripts/ev3.py deploy
   ```

4. Place the robot with the **wheel midpoint on the start mark** and the front pointing along the
   tile seam toward the top wall. Check the alignment with a straightedge; a start heading that is a
   few degrees off turns into tens of centimeters of error at the goal.
5. Start the run:

   ```bash
   python scripts/ev3.py run
   ```

   The robot waits 3 seconds and then drives. The program runs on the brick, so it keeps going if the
   cable drops. **Ctrl-C** stops it and switches the motors off.

## Commands

On the laptop, `python scripts/ev3.py <command>`:

| Command | What it does |
|---|---|
| `deploy` | Copy the code to the robot (does not start it) |
| `run` | Plan and drive the course |
| `stop` | Switch both motors off |
| `plan` | Print the route (no motion) |
| `inspect` | Read-only check that the motors and gyro are found |
| `fetch-logs` | Download the run logs from the brick |
| `clean` | Delete old uploaded releases on the brick |
| `launcher` | Create `run_course.py` on the brick for starting from its File Browser |

Each run writes a log (position, heading, motor power, wheel and gyro readings) to the brick's
`logs` folder.

## Safety

Every way the program can end stops both motors. The run also aborts on a timing gap, a stalled
wheel, a gyro and encoder disagreement, or a clearance violation. `touch /tmp/ev3-abort` on the
brick or the `stop` command also stops it.

# Team 10 | Malaika, Nick & Riya
