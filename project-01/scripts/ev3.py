#!/usr/bin/env python3
"""Laptop CLI: deploy our source and run nonmoving checks using SSH/SCP.

No pip packages, credentials in files, or firmware tools required.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
REMOTE = "/home/robot/navigating-obstacles/project-01"


def git_revision():
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT,
                            text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def source_digest(files):
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("EV3_HOST", "ev3dev.local"))
    parser.add_argument("--user", default=os.environ.get("EV3_USER", "robot"))
    parser.add_argument("--known-hosts", default=os.environ.get("EV3_KNOWN_HOSTS"))
    parser.add_argument("command", choices=("deploy", "runtime", "inspect", "selftest",
                                          "plan-demo", "plan", "monitor", "fetch-logs"))
    parser.add_argument("--samples", type=int, default=20)
    args = parser.parse_args()
    if not args.host or args.host.startswith("-") or any(c.isspace() for c in args.host):
        parser.error("Invalid host")
    if not args.user or not all(c.isalnum() or c in "_-" for c in args.user):
        parser.error("Invalid user")
    options = ["-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new"]
    if args.known_hosts:
        options.extend(["-o", "UserKnownHostsFile=" + args.known_hosts])
    target = args.user + "@" + args.host
    scp_target = args.user + "@" + ("[" + args.host + "]" if ":" in args.host else args.host)

    def ssh(command):
        subprocess.run(["ssh"] + options + [target, command], check=True)

    def copy(paths, destination):
        subprocess.run(["scp", "-O"] + options + list(map(str, paths)) + [destination], check=True)

    if args.command == "deploy":
        files = sorted((PROJECT / "src").glob("*.py"))
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        digest = source_digest(files)
        release = timestamp + "-" + digest[:12]
        directory = REMOTE + "/releases/" + release
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                cwd=PROJECT, text=True, capture_output=True)
        manifest = {"git_commit": git_revision(), "working_tree_dirty": bool(status.stdout.strip()),
                    "source_sha256": digest, "deployed_utc": timestamp,
                    "runtime": "pybricks-micropython 2.0.0", "robot_packages": [],
                    "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        ssh("mkdir -p " + shlex.quote(directory) + " " + shlex.quote(REMOTE + "/logs"))
        with tempfile.TemporaryDirectory(prefix="ev3-deploy-") as temporary:
            meta = Path(temporary) / "deployment.json"
            meta.write_text(json.dumps(manifest, indent=2) + "\n")
            copy(files + [meta], scp_target + ":" + directory + "/")
        # Verify every uploaded byte before changing the current release link.
        verifier = ("import hashlib,json; from pathlib import Path; "
                    "p=Path(" + repr(directory) + "); "
                    "m=json.loads((p/'deployment.json').read_text()); "
                    "assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h "
                    "for n,h in m['files'].items()), 'upload checksum mismatch'")
        ssh("python3 -c " + shlex.quote(verifier))
        ssh("cd " + shlex.quote(REMOTE) + " && ln -sfn " + shlex.quote("releases/" + release) +
            " current.next && mv -Tf current.next current")
        print("Deployed", release, "(no program started)")
    elif args.command == "runtime":
        check = ('import sys, os, time, math; print(sys.implementation); '
                 'print("sysfs", os.listdir("/sys/class/tacho-motor")); '
                 'print("timing", hasattr(time,"ticks_ms"), hasattr(time,"ticks_diff"))')
        ssh("hostname; uname -r; cat /etc/os-release; "
            "brickrun -r -- pybricks-micropython -c " + shlex.quote(check))
    elif args.command == "fetch-logs":
        destination = PROJECT / "logs" / datetime.datetime.now().strftime("download-%Y%m%dT%H%M%S")
        destination.mkdir(parents=True)
        subprocess.run(["scp", "-O", "-r"] + options +
                       [scp_target + ":" + REMOTE + "/logs/.", str(destination)], check=True)
        print("Saved logs to", destination)
    else:
        command = "cd " + shlex.quote(REMOTE + "/current") + " && "
        if args.command == "monitor":
            if not 1 <= args.samples <= 600:
                parser.error("--samples must be between 1 and 600")
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            remote_log = REMOTE + "/logs/monitor-" + stamp + ".txt"
            # Logs are diagnostic snapshots, not a fixed-rate control-loop log.
            command += ("brickrun -r -- pybricks-micropython main.py monitor " + str(args.samples) +
                        " > " + shlex.quote(remote_log) + "; result=$?; cat " +
                        shlex.quote(remote_log) + "; exit $result")
        else:
            command += "brickrun -r -- pybricks-micropython main.py " + shlex.quote(args.command)
        ssh(command)


if __name__ == "__main__":
    main()
