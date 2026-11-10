"""Sensor bring-up via ev3dev sysfs; deliberately has no motor output API.

Uses built-in modules on Pybricks MicroPython 2 and CPython. Sensors are
identified by port, since kernel device numbers change on reconnect.
"""
import os

SENSOR_ROOT = "/sys/class/lego-sensor"
MOTOR_ROOT = "/sys/class/tacho-motor"


def read(path, attribute):
    with open(path + "/" + attribute, "r") as stream:
        return stream.read().strip()


def discover(root):
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    return [{"path": root + "/" + name,
             "address": read(root + "/" + name, "address"),
             "driver": read(root + "/" + name, "driver_name")}
            for name in names]


def color_device(port):
    devices = [device for device in discover(SENSOR_ROOT)
               if device["address"].split(":")[-1] == "in" + str(port)]
    if len(devices) != 1 or devices[0]["driver"] != "lego-ev3-color":
        raise ValueError("Expected LEGO color sensor on input " + str(port))
    return devices[0]


def select_color_mode(device, mode):
    # This is the only device write in the bring-up code. Never accepts a motor.
    if device not in discover(SENSOR_ROOT) or device["driver"] != "lego-ev3-color":
        raise ValueError("Mode changes are restricted to the color sensor")
    if mode not in ("RGB-RAW", "COL-REFLECT", "COL-COLOR", "COL-AMBIENT", "REF-RAW"):
        raise ValueError("Unsupported diagnostic color mode")
    if mode not in read(device["path"], "modes").split():
        raise ValueError("Color sensor does not support " + mode)
    with open(device["path"] + "/mode", "w") as stream:
        stream.write(mode)


def snapshot():
    sensors = []
    for device in discover(SENSOR_ROOT):
        path = device["path"]
        device["mode"] = read(path, "mode")
        device["units"] = read(path, "units")
        decimals = int(read(path, "decimals"))
        device["decimals"] = decimals
        device["raw"] = [int(read(path, "value" + str(index)))
                         for index in range(int(read(path, "num_values")))]
        device["values"] = [value / (10 ** decimals) if decimals else value
                            for value in device["raw"]]
        sensors.append(device)
    motors = []
    for device in discover(MOTOR_ROOT):
        path = device["path"]
        device["position"] = int(read(path, "position"))
        device["speed"] = int(read(path, "speed"))
        device["state"] = read(path, "state")
        motors.append(device)
    return {"sensors": sensors, "motors": motors}


def require_stationary(motors):
    for motor in motors:
        if motor["speed"] != 0 or motor["state"]:
            raise RuntimeError("Motor is not idle at " + motor["address"] +
                               "; ending sensor test without motor commands")
