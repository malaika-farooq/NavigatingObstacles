#!/usr/bin/env python3
"""Restore EV3 USB networking and the `ev3` SSH alias on this laptop.

This brick accepts credential-free SSH as robot on its USB link. The helper
verifies a fresh login and updates the laptop aliases without creating keys.
"""
import argparse
from pathlib import Path
import re
import subprocess
import time

BEGIN = "# BEGIN NavigatingObstacles EV3\n"
END = "# END NavigatingObstacles EV3\n"
NO_CREDENTIALS = ["-o", "BatchMode=yes", "-o", "PubkeyAuthentication=no",
                  "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
                  "-o", "GSSAPIAuthentication=no", "-o", "HostbasedAuthentication=no"]


def run(*arguments, **kwargs):
    return subprocess.run(arguments, check=True, **kwargs)


def usb_host():
    interfaces = []
    for interface in Path("/sys/class/net").iterdir():
        device = (interface / "device").resolve()
        for parent in [device] + list(device.parents):
            vendor = parent / "idVendor"
            product = parent / "idProduct"
            if vendor.exists() and product.exists():
                if vendor.read_text().strip() == "0694" and product.read_text().strip() == "0005":
                    interfaces.append(interface.name)
                    break
    if len(interfaces) != 1:
        raise SystemExit("Expected one booted EV3 USB network interface; found " + str(interfaces))
    interface = interfaces[0]
    profiles = subprocess.check_output(["nmcli", "-g", "NAME", "connection", "show"], text=True).splitlines()
    if "ev3-usb" not in profiles:
        run("nmcli", "connection", "add", "type", "ethernet", "ifname", interface,
            "con-name", "ev3-usb", "ipv4.method", "disabled", "ipv6.method", "link-local")
    run("nmcli", "connection", "modify", "ev3-usb", "connection.interface-name", interface,
        "connection.autoconnect", "yes", "connection.autoconnect-priority", "100",
        "ipv4.method", "disabled", "ipv6.method", "link-local")
    active = subprocess.check_output(["nmcli", "-g", "GENERAL.CONNECTION", "device", "show", interface], text=True).strip()
    if active != "ev3-usb":
        run("nmcli", "--wait", "10", "connection", "up", "ev3-usb")
    for attempt in range(15):
        addresses = subprocess.check_output(["ip", "-6", "address", "show", "dev", interface], text=True)
        if "scope link" in addresses and "tentative" not in addresses:
            break
        time.sleep(0.2)
    # Some EV3 images ignore multicast echo. Probe the previously verified brick
    # address too, using the current USB interface scope, to populate neighbors.
    settings = subprocess.check_output(["ssh", "-G", "ev3"], text=True, stderr=subprocess.DEVNULL)
    previous = next((line.split()[1] for line in settings.splitlines()
                     if line.startswith("hostname fe80:")), None)
    if previous:
        subprocess.run(["ping", "-6", "-c", "1", "-W", "2", previous.split("%")[0] + "%" + interface],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ping", "-6", "-c", "2", "-W", "2", "ff02::1%" + interface],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    neighbors = subprocess.check_output(["ip", "-6", "neigh", "show", "dev", interface], text=True)
    hosts = [line.split()[0] for line in neighbors.splitlines()
             if "lladdr" in line and not any(state in line for state in ("FAILED", "INCOMPLETE"))]
    if len(hosts) != 1:
        raise SystemExit("Could not identify one USB peer; wait for boot and retry, or pass --host")
    return hosts[0] + "%" + interface


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="Override USB discovery with brick IP/hostname")
    args = parser.parse_args()
    host = args.host or usb_host()
    if not re.fullmatch(r"[A-Za-z0-9_.:%-]+", host) or host.startswith("-"):
        parser.error("Invalid host")
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    options = NO_CREDENTIALS + ["-o", "ControlPath=none", "-o", "ConnectTimeout=10",
                                "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR"]
    result = subprocess.run(["ssh"] + options + ["robot@" + host, "true"])
    if result.returncode:
        raise SystemExit("Could not log in without credentials; check the brick's USB SSH settings.")
    path = ssh_dir / "config"
    original = path.read_text() if path.exists() else ""
    original = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", original, flags=re.S)
    block = BEGIN + """Host ev3 ev3dev.local
    HostName {host}
    User robot
    PubkeyAuthentication no
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    GSSAPIAuthentication no
    HostbasedAuthentication no
    BatchMode yes
    ConnectTimeout 10
    StrictHostKeyChecking accept-new
    ControlMaster auto
    ControlPersist 600
    ControlPath ~/.ssh/ev3-%C
    ServerAliveInterval 10
    ServerAliveCountMax 3
    LogLevel ERROR
""".format(host=host.replace("%", "%%")) + END + "\n"
    path.write_text(block + original)
    path.chmod(0o600)
    run("ssh", "-o", "ControlPath=none", "ev3", "echo 'EV3 USB login verified'")
    print("Ready: ssh ev3")


if __name__ == "__main__":
    main()
