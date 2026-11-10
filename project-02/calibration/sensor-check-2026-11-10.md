# Project 2 sensor bring-up — November 10, 2026

The user confirmed the fan motor on D, the downward-facing color sensor on 1,
and the front bumper touch sensor on 4. The fan is explicitly held disabled until
the user says otherwise. The diagnostic code has no motor command API. The
implementation brief's proposed wiring is superseded by these confirmations.

## Discovered hardware and software

- Input 1: `lego-ev3-color`, initially `COL-REFLECT`.
- Input 4: `lego-ev3-touch`, mode `TOUCH`; front bumper role confirmed by user.
- Outputs A and B: `lego-ev3-l-motor`; current left/right mapping unconfirmed.
- Output D: `lego-ev3-m-motor`; fan, held disabled.
- No second touch sensor, ultrasonic sensor or gyro discovered during these checks.
- Actual runtime: Pybricks MicroPython 2.0.0, underlying MicroPython v1.11,
  build date 2020-05-06. Built-in modules and ev3dev sysfs only.

## Completed samples

Logs are stored locally in the ignored `project-02/logs/` directory. File timestamps
are laptop UTC times; the robot clock is not the test date source. The material
beneath the color sensor was not identified or changed in the observed records.

| Log (UTC) | Samples | Color mode | Observed range | Touch values |
| --- | --- | --- | --- | --- |
| `20261110T221141.274801Z-monitor.jsonl` | 60 | RGB-RAW | R 283–286, G 201–204, B 180–182 | 0 throughout |
| `20261110T221247.721727Z-monitor.jsonl` | 100 | RGB-RAW | R 282–286, G 198–203, B 178–182 | 0 throughout |
| `20261110T221421.908567Z-monitor.jsonl` | 10 | COL-REFLECT | 63–64% | 0 throughout |

Every recorded motor speed in these completed runs was zero, with empty motor
states. In the 100-sample run, all motor encoders also stayed at zero. These are
diagnostic reads, not motor polarity or drivetrain tests. The RGB tests restored
`COL-REFLECT` at completion. No fire/pad detector or threshold has been calibrated.

An earlier attempt stopped after 12 accepted samples when output D reported a
non-idle state; D then disappeared from discovery and reappeared with a new kernel
device number. The diagnostic issued no motor commands and restored the color
mode before exiting. The cause of the transient was not established. Discovery
uses port addresses rather than kernel motor/sensor numbers.

`brickrun` forwards program output on stderr on this system. The laptop logger
now merges stdout/stderr and saves JSON lines, including diagnostic messages.
The first two completed RGB logs were recovered from the captured terminal
output after finding that behavior; the reflection log was captured directly
with the corrected logger. The earlier aborted run has no complete saved log.

## Connection improvements verified

At the user's request, the initial login key setup was replaced with open SSH
access for the `robot` account on the brick's USB link-local address. A fresh
connection with key, password and keyboard-interactive authentication disabled
logged in using SSH's `none` method. The dedicated login key was removed from
the laptop and the brick. A fresh USB SCP transfer succeeded after key removal;
a login to the brick's loopback address was rejected. Host-key checking remains
enabled.

The server's `/etc/ssh/sshd_config` matches `robot` on the `usb0` IPv6 link-local
address (including the form with an interface scope). It disables public-key
login and permits the empty authentication request on that address. A matching
deny rule rejects `robot` at all other addresses. `/etc/pam.d/sshd` admits the
`robot` SSH account once those rules allow it; console and sudo passwords were
not changed. The original server and PAM files are backed up on the brick in
`/root/ev3-usb-ssh-backup-20200412T025325Z` (brick clock).

The persistent laptop NetworkManager profile `ev3-usb` is bound to the EV3 USB
interface, with IPv4 disabled, IPv6 link-local enabled and automatic connection.
The USB interface/address can be rediscovered by `scripts/setup_connection.py`.
Taking down only the EV3 USB profile and running that helper successfully
restored the connection. The updated helper verifies the open USB login and
does not generate or install a key. Other laptop networks were not changed.

## Next physical checks

1. Press/release the front bumper while sampling: require both 0 and 1, including
   presses at the left edge, center and right edge. Only the released state has
   been observed so far.
2. Log labeled bare-floor, seam and fire-pad RGB samples at the actual mount
   height, then select detection thresholds. The user described a rigid,
   downward-facing mount close to the floor near the front caster; the exact
   height and offsets remain unmeasured.
3. Confirm/connect the remaining sensors and current drive motor assignments
   before implementing motion behaviors. The paper-design numbers remain
   assumptions. The verbose diagnostic loop does not validate a 20 ms controller.
4. Wait for explicit user instruction before enabling or testing the fan on D.

Local validation covers rejection of motor mode writes, restoration of color
mode on a sampling exception, rejection of non-idle motors at startup, and capture
of brickrun stderr into structured logs. Four tests pass.

Final deployed release: `20261110T221651Z-342b7b06e8d0`, with all source SHA-256
checks verified before activation. Final inspection log
`20261110T221658.519406Z-inspect.jsonl` confirmed color 1, bumper 4, fan D disabled,
reflection 65%, bumper released, and all three motors at zero speed with empty
states. No continuous program was left running.

## White tabletop reference

The user placed the robot on a white tabletop. Twenty samples per mode were
taken at the existing sensor height with the robot stationary. The color
sensor on input 1 averaged **50.8% reflectance** (range 50–51%) and raw RGB
**(224.25, 216.45, 144.25)** (ranges R 224–226, G 215–217, B 143–145).
The monitor restored `COL-REFLECT` after RGB sampling.

`src/config.py` stores the white reference and `inspect` reports it. A
pad-detection threshold requires measurements on the arena floor and pad.
The sample logs are `20261110T230038.153477Z-monitor.jsonl` for reflectance
and `20261110T230054.166893Z-monitor.jsonl` for RGB.

## Ultrasonic and fan tests

The ultrasonic sensor on input 3 reported 6.7–32.6 cm across six samples in
`US-DIST-CM` mode. These samples verify distance reporting. Sensor placement
and obstacle detection thresholds still need calibration in the arena.

Three manual 10-second runs on fan port D used the maximum setpoint of
260 RPM. The motor encoder measured peaks of 203.0, 203.8 and 209.8 RPM.
Each timed run stopped automatically and the final encoder speed was zero.
The tests measured motor speed. Airflow and extinguishing performance remain
unmeasured.
