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


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("EV3_HOST", "ev3dev.local"))
    parser.add_argument("--user", default=os.environ.get("EV3_USER", "robot"))
    parser.add_argument("--known-hosts", default=os.environ.get("EV3_KNOWN_HOSTS"))
    parser.add_argument("command", choices=("deploy", "runtime", "inspect", "selftest", "color-check",
                                          "plan-demo", "plan", "monitor", "fetch-logs"))
    parser.add_argument("--samples", type=int, default=20)
    arguments = parser.parse_args()
    invalid_host = not arguments.host or arguments.host.startswith("-")
    if invalid_host or any(character.isspace() for character in arguments.host):
        parser.error("Invalid host")
    valid_user = arguments.user and all(character.isalnum() or character in "_-" for character in arguments.user)
    if not valid_user:
        parser.error("Invalid user")
    if not 1 <= arguments.samples <= 600:
        parser.error("--samples must be between 1 and 600")
    return arguments


class Connection:
    def __init__(self, arguments):
        self.options = ["-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new"]
        if arguments.known_hosts:
            self.options.extend(["-o", "UserKnownHostsFile=" + arguments.known_hosts])
        self.target = arguments.user + "@" + arguments.host
        scp_host = "[" + arguments.host + "]" if ":" in arguments.host else arguments.host
        self.scp_target = arguments.user + "@" + scp_host

    def run(self, remote_command):
        command = ["ssh"] + self.options + [self.target, remote_command]
        subprocess.run(command, check=True)

    def upload(self, paths, directory):
        destination = self.scp_target + ":" + directory + "/"
        command = ["scp", "-O"] + self.options + list(map(str, paths)) + [destination]
        subprocess.run(command, check=True)

    def download_logs(self, destination):
        remote_logs = self.scp_target + ":" + REMOTE + "/logs/."
        command = ["scp", "-O", "-r"] + self.options + [remote_logs, str(destination)]
        subprocess.run(command, check=True)


def deployment_manifest(files, timestamp):
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                            cwd=PROJECT, text=True, capture_output=True)
    file_checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    return {"git_commit": git_revision(), "working_tree_dirty": bool(status.stdout.strip()),
            "source_sha256": source_digest(files), "deployed_utc": timestamp,
            "runtime": "pybricks-micropython 2.0.0", "robot_packages": [], "files": file_checksums}


def upload_release(connection, files, manifest, directory):
    connection.run("mkdir -p " + shlex.quote(directory) + " " + shlex.quote(REMOTE + "/logs"))
    with tempfile.TemporaryDirectory(prefix="ev3-deploy-") as temporary:
        manifest_path = Path(temporary) / "deployment.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        connection.upload(files + [manifest_path], directory)


def verify_release(connection, directory):
    verifier = ("import hashlib,json; from pathlib import Path; "
                "p=Path(" + repr(directory) + "); "
                "m=json.loads((p/'deployment.json').read_text()); "
                "assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h "
                "for n,h in m['files'].items()), 'upload checksum mismatch'")
    connection.run("python3 -c " + shlex.quote(verifier))


def publish_release(connection, release):
    release_target = shlex.quote("releases/" + release)
    publish_command = ("cd " + shlex.quote(REMOTE) + " && ln -sfn " + release_target +
                       " current.next && mv -Tf current.next current")
    connection.run(publish_command)


def deploy(connection):
    files = sorted((PROJECT / "src").glob("*.py"))
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = deployment_manifest(files, timestamp)
    release = timestamp + "-" + manifest["source_sha256"][:12]
    directory = REMOTE + "/releases/" + release
    upload_release(connection, files, manifest, directory)
    verify_release(connection, directory)
    publish_release(connection, release)
    print("Deployed", release, "(no program started)")


def inspect_runtime(connection):
    check = ('import sys, os, time, math, gc; print(sys.implementation); '
             'print("sysfs", os.listdir("/sys/class/tacho-motor")); '
             'print("timing", hasattr(time,"ticks_ms"), hasattr(time,"ticks_diff")); '
             'print("gc.collect", hasattr(gc,"collect")); '
             'print("heap_free", gc.mem_free() if hasattr(gc,"mem_free") else "unavailable")')
    command = ("hostname; uname -r; cat /etc/os-release; "
               "brickrun -r -- pybricks-micropython -c " + shlex.quote(check))
    connection.run(command)


def fetch_logs(connection):
    timestamp = datetime.datetime.now().strftime("download-%Y%m%dT%H%M%S")
    destination = PROJECT / "logs" / timestamp
    destination.mkdir(parents=True)
    connection.download_logs(destination)
    print("Saved logs to", destination)


def monitor_command(sample_count):
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = REMOTE + "/logs/monitor-" + timestamp + ".txt"
    quoted_log = shlex.quote(log_path)
    return ("brickrun -r -- pybricks-micropython main.py monitor " + str(sample_count) +
            " > " + quoted_log + "; result=$?; cat " + quoted_log + "; exit $result")


def run_project_command(connection, arguments):
    if arguments.command == "monitor":
        program_command = monitor_command(arguments.samples)
    else:
        program_command = "brickrun -r -- pybricks-micropython main.py " + shlex.quote(arguments.command)
    remote_command = "cd " + shlex.quote(REMOTE + "/current") + " && " + program_command
    connection.run(remote_command)


def main():
    arguments = parse_arguments()
    connection = Connection(arguments)
    if arguments.command == "deploy":
        deploy(connection)
    elif arguments.command == "runtime":
        inspect_runtime(connection)
    elif arguments.command == "fetch-logs":
        fetch_logs(connection)
    else:
        run_project_command(connection, arguments)


if __name__ == "__main__":
    main()
