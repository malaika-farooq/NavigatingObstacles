"""Our ev3dev sysfs adapter. Built-in modules only; no pybricks/ev3dev2 imports.

Discovery and snapshots do not write to devices. Device numbers are dynamic:
identify motors/sensors by address, never by motor0 or sensor0.
"""
import os

MOTOR_ROOT = "/sys/class/tacho-motor"
SENSOR_ROOT = "/sys/class/lego-sensor"


def read(path, attribute):
    with open(path + "/" + attribute, "r") as stream:
        return stream.read().strip()


def write(path, attribute, value):
    with open(path + "/" + attribute, "w") as stream:
        stream.write(str(value))


def discover(root):
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    devices = []
    for name in names:
        path = root + "/" + name
        devices.append({"path": path, "address": read(path, "address"),
                        "driver": read(path, "driver_name")})
    return devices


def find(root, address_suffix, expected_driver):
    matches = [d for d in discover(root)
               if d["address"].split(":")[-1] == address_suffix]
    if len(matches) != 1:
        raise ValueError("Expected one device at " + address_suffix)
    device = matches[0]
    if device["driver"] != expected_driver:
        raise ValueError("Unexpected driver at " + address_suffix + ": " + device["driver"])
    return device["path"]


def _motor_snapshot(device):
    path = device["path"]
    device["position"] = read(path, "position")
    device["speed"] = read(path, "speed")
    device["state"] = read(path, "state")
    return device


def _sensor_snapshot(device):
    path = device["path"]
    device["mode"] = read(path, "mode")
    device["decimals"] = read(path, "decimals")
    device["units"] = read(path, "units")
    value_count = int(read(path, "num_values"))
    device["values"] = []
    for value_index in range(value_count):
        attribute_name = "value" + str(value_index)
        device["values"].append(read(path, attribute_name))
    return device


def snapshot():
    readings = []
    for device in discover(MOTOR_ROOT):
        readings.append(_motor_snapshot(device))
    for device in discover(SENSOR_ROOT):
        readings.append(_sensor_snapshot(device))
    return readings


class Motor:
    """Explicit raw-duty output for future calibration/control code.

    Construction reads only. enable() and set_duty() are deliberate writes.
    run-direct bypasses the kernel's speed/position PID. A controller using it
    must call stop() in finally and provide an independent stop/watchdog path.
    """
    def __init__(self, port, forward_sign, max_duty=25):
        if port not in ("A", "B", "C", "D") or forward_sign not in (-1, 1):
            raise ValueError("Confirm motor port and forward sign")
        if max_duty <= 0 or max_duty > 100:
            raise ValueError("Invalid duty limit")
        self.path = find(MOTOR_ROOT, "out" + port, "lego-ev3-l-motor")
        self.sign = forward_sign
        self.max_duty = max_duty
        self.counts_per_rotation = int(read(self.path, "count_per_rot"))
        if self.counts_per_rotation <= 0:
            raise ValueError("Invalid encoder scale")
        if "run-direct" not in read(self.path, "commands").split():
            raise ValueError("Motor does not support raw-duty control")
        self.enabled = False

    def angle_degrees(self):
        encoder_counts = int(read(self.path, "position"))
        motor_rotations = encoder_counts / self.counts_per_rotation
        return self.sign * motor_rotations * 360.0

    def speed_degrees_s(self):
        encoder_counts_per_s = int(read(self.path, "speed"))
        motor_rotations_per_s = encoder_counts_per_s / self.counts_per_rotation
        return self.sign * motor_rotations_per_s * 360.0

    def enable(self):
        self.stop()
        write(self.path, "duty_cycle_sp", 0)
        write(self.path, "command", "run-direct")
        self.enabled = True

    def set_duty(self, duty):
        if not self.enabled:
            raise ValueError("Motor output is not enabled")
        if not (-self.max_duty <= duty <= self.max_duty):
            raise ValueError("Requested motor duty exceeds configured limit")
        raw_duty_percent = int(round(self.sign * duty))
        write(self.path, "duty_cycle_sp", raw_duty_percent)

    def stop(self):
        try:
            write(self.path, "stop_action", "brake")
        finally:
            try:
                write(self.path, "command", "stop")
            finally:
                self.enabled = False


class Sensor:
    def __init__(self, port, expected_driver):
        if str(port) not in ("1", "2", "3", "4"):
            raise ValueError("Sensor input must be 1..4")
        self.path = find(SENSOR_ROOT, "in" + str(port), expected_driver)

    def select_mode(self, mode):
        if mode not in read(self.path, "modes").split():
            raise ValueError("Unsupported sensor mode: " + mode)
        if read(self.path, "mode") != mode:
            write(self.path, "mode", mode)

    def value(self, expected_mode):
        if read(self.path, "mode") != expected_mode:
            raise ValueError("Sensor mode changed; reinitialize before continuing")
        raw_value = int(read(self.path, "value0"))
        decimal_places = int(read(self.path, "decimals"))
        unit_scale = 10.0 ** decimal_places
        return raw_value / unit_scale


class Gyro(Sensor):
    def __init__(self, port, ccw_sign):
        if ccw_sign not in (-1, 1):
            raise ValueError("Confirm gyro direction")
        Sensor.__init__(self, port, "lego-ev3-gyro")
        self.sign = ccw_sign

    def initialize(self):
        # Keep robot motionless. Caller must wait and measure startup drift.
        self.select_mode("GYRO-ANG")

    def angle_degrees(self):
        # Do not switch between angle and rate modes during a run.
        return self.sign * self.value("GYRO-ANG")


class ColorSensor(Sensor):
    def __init__(self, port):
        Sensor.__init__(self, port, "lego-ev3-color")

    def initialize(self):
        self.select_mode("COL-REFLECT")

    def reflection(self):
        return self.value("COL-REFLECT")
