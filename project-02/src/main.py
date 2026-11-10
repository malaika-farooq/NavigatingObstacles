"""Nonmoving project 2 diagnostics. No fan self-test or drive commands."""
import json
import sys
import time
import config
from hardware import (color_device, read, require_stationary,
                      select_color_mode, snapshot)


def emit(record):
    print(json.dumps(record))


def elapsed_ms(start):
    if hasattr(time, "ticks_ms"):
        return time.ticks_diff(time.ticks_ms(), start)
    return int((time.monotonic() - start) * 1000)


def clock_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return time.monotonic()


def monitor(count, interval_s, requested_mode):
    if not 1 <= count <= 6000 or not 0.02 <= interval_s <= 5 or count * interval_s > 600:
        raise ValueError("Use 1..6000 samples, 0.02..5 s interval, at most 600 seconds")
    if requested_mode not in ("current", "rgb", "reflect", "color"):
        raise ValueError("Mode must be current, rgb, reflect, or color")
    before = snapshot()
    require_stationary(before["motors"])
    color = color_device(config.COLOR_PORT)
    original_mode = read(color["path"], "mode")
    mode = {"rgb": "RGB-RAW", "reflect": "COL-REFLECT", "color": "COL-COLOR"}.get(requested_mode)
    if mode and original_mode not in ("RGB-RAW", "COL-REFLECT", "COL-COLOR", "COL-AMBIENT", "REF-RAW"):
        raise ValueError("Cannot safely restore original color mode: " + original_mode)
    emit({"event": "start", "color_port": config.COLOR_PORT,
          "fan_port": config.FAN_PORT, "fan_enabled": config.FAN_ENABLED,
          "count": count, "interval_s": interval_s,
          "original_color_mode": original_mode, "requested_mode": requested_mode,
          "devices": before})
    stats = {}
    start = clock_ms()
    try:
        if mode and mode != original_mode:
            select_color_mode(color, mode)
            time.sleep(0.2)
        start = clock_ms()
        for index in range(count):
            sample_start = clock_ms()
            sample = snapshot()
            sample.update({"event": "sample", "index": index, "elapsed_ms": elapsed_ms(start)})
            emit(sample)
            require_stationary(sample["motors"])
            for sensor in sample["sensors"]:
                key = sensor["address"]
                values = sensor["values"]
                if key not in stats:
                    stats[key] = {"mode": sensor["mode"], "units": sensor["units"],
                                  "min": values[:], "max": values[:], "transitions": 0,
                                  "previous": values[:]}
                stat = stats[key]
                if stat["mode"] != sensor["mode"] or len(values) != len(stat["min"]):
                    raise RuntimeError("Sensor mode changed during sampling: " + key)
                stat["min"] = [min(a, b) for a, b in zip(stat["min"], values)]
                stat["max"] = [max(a, b) for a, b in zip(stat["max"], values)]
                if values != stat["previous"]:
                    stat["transitions"] += 1
                stat["previous"] = values[:]
            if index + 1 < count:
                remaining = interval_s - elapsed_ms(sample_start) / 1000.0
                if remaining > 0:
                    time.sleep(remaining)
    finally:
        # Also restore mode on Ctrl-C/exception during a test.
        if mode and mode != original_mode:
            select_color_mode(color, original_mode)
            time.sleep(0.2)
        emit({"event": "finish", "color_mode": read(color["path"], "mode"),
              "elapsed_ms": elapsed_ms(start), "devices": snapshot()})
    emit({"event": "summary", "samples": count, "sensors": stats})


def main(arguments):
    command = arguments[0] if arguments else "inspect"
    if command == "inspect":
        emit({"event": "inspect", "runtime": str(sys.implementation),
              "color_port": config.COLOR_PORT, "fan_port": config.FAN_PORT,
              "bumper_port": config.BUMPER_PORT,
              "ultrasonic_port": config.ULTRASONIC_PORT,
              "white_tabletop_reference": {"reflection_pct": config.COLOR_WHITE_REFLECTION_PCT,
                                          "rgb": config.COLOR_WHITE_RGB},
              "fan_enabled": config.FAN_ENABLED, "devices": snapshot()})
    elif command == "monitor":
        monitor(int(arguments[1]) if len(arguments) > 1 else config.SAMPLE_COUNT,
                float(arguments[2]) if len(arguments) > 2 else config.SAMPLE_INTERVAL_S,
                arguments[3] if len(arguments) > 3 else "current")
    else:
        raise ValueError("Commands: inspect, monitor [samples interval_s current|rgb|reflect|color]")


if __name__ == "__main__":
    main(sys.argv[1:])
