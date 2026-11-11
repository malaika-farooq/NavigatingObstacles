# Project 2: Fire alarm robot

Start with [the implementation brief](docs/implementation-brief.md) and the
[assignment PDF](proj2.pdf). The current code provides stationary sensor tests.
The behavior controller is still to be implemented after the build is confirmed.
Runtime: the existing Pybricks MicroPython 2.0.0 SD card, using built-in modules
and ev3dev sysfs. Nothing needs to be installed on the robot.

The fan on D passed manual timed tests. `src/config.py` keeps automatic fan
control disabled with `FAN_ENABLED = False`. See the [bench test results](calibration/sensor-check-2026-11-10.md).

## Wiring confirmed November 10, 2026

| Port | Device | Status |
| --- | --- | --- |
| Input 1 | Color sensor | User confirmed; discovered on brick |
| Input 3 | Ultrasonic distance sensor | User confirmed; reports centimeters |
| Input 4 | Front bumper touch sensor | User confirmed; discovered on brick |
| D | Medium motor / fan | Confirmed in manual timed tests |
| A, B | Large motors | Discovered; current left/right roles unconfirmed |

The current build has one touch sensor. Geometry, polarity,
pad classification and navigation remain uncalibrated for project 2. Project 1's
29% black threshold is not a project 2 fire detector.

## Connect and run

On this laptop, `ssh ev3` logs in as `robot` over USB without a password or login
key. Anyone connected to the brick's USB network can use that account. The
aliases `ev3` and `ev3dev.local` reuse connections for ten minutes.

After reconnecting USB, or if the interface/address changes, run:

```bash
python3 project-02/scripts/setup_connection.py
```

This discovers the EV3 USB network interface, configures the persistent
`ev3-usb` NetworkManager profile with IPv6 link-local networking, discovers the
brick, and refreshes the `ev3` / `ev3dev.local` SSH aliases. It changes only the
EV3 USB profile and verifies login with all client credentials disabled.
`--host ADDRESS` skips USB network setup and uses a known address instead.
The brick itself must already allow USB login; see the
[connection notes](calibration/sensor-check-2026-11-10.md#connection-improvements-verified).

From the repository root:

```bash
python3 project-02/scripts/ev3.py deploy
python3 project-02/scripts/ev3.py inspect
python3 project-02/scripts/ev3.py monitor --samples 60 --interval 0.5 --mode rgb
python3 project-02/scripts/ev3.py monitor --samples 30 --mode reflect
```

Deployment uploads a new release, verifies every source file's SHA-256, and
activates it without starting a program. Project 1's deployment stays separate.
`EV3_HOST` or `--host` can override the default SSH alias.

The release also includes `fire_alert.wav`, a 40-second robot alarm. Its opening
data-like bursts are simulated, followed by an eight-second attention tone and
a female announcement; the alarm resumes after the announcement. The voice is
the community-created CRS Mara approximation, not the original NOAA Donna.
The behavior controller does not yet trigger the audio.

The monitor captures all discovered sensors and motor telemetry as JSON lines
under `project-02/logs/` on the laptop. `--mode current` leaves sensor modes alone;
`rgb`, `reflect`, and `color` temporarily change only input 1's color mode and
restore it on normal completion or a handled exception. Sensor unplugging, power
loss, or forced termination may prevent restoration; inspect before retesting.
Tests reject non-idle motors and log their state without sending motor commands.
The interval is a requested minimum period: verbose sysfs diagnostics may be
slower and do not establish the future controller's loop performance.

During a test, press/release the touch switch and move known floor/pad samples
under the fixed-height color lens. A stationary reading alone does not establish
switch response or pad discrimination. Record the material and mount height
alongside the log before selecting thresholds.

Local failure-path checks:

```bash
python3 -m unittest discover -s project-02/tests -v
```
