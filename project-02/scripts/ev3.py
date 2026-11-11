#!/usr/bin/env python3
"""Laptop helper: verified deployment and logged sensor tests over USB SSH."""
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
REMOTE = "/home/robot/navigating-obstacles/project-02"
OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           "-o", "StrictHostKeyChecking=accept-new"]


def ssh(host, command):
    return subprocess.run(["ssh"] + OPTIONS + [host, command], check=True)


def deploy(host):
    files = sorted((PROJECT / "src").glob("*.py")) + [PROJECT / "audio" / "fire_alert.wav"]
    checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip()
    manifest = {"files": checksums, "deployed_utc": timestamp, "git_commit": revision,
                "note": "File checksums identify deployed source, including uncommitted edits.",
                "fan_enabled": False}
    digest = hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest()[:12]
    release = timestamp + "-" + digest
    directory = REMOTE + "/releases/" + release
    ssh(host, "mkdir -p " + shlex.quote(directory))
    with tempfile.TemporaryDirectory(prefix="ev3-project2-") as temporary:
        path = Path(temporary) / "deployment.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        subprocess.run(["scp", "-O"] + OPTIONS + [str(p) for p in files + [path]] +
                       [host + ":" + directory + "/"], check=True)
    verifier = ("import hashlib,json; from pathlib import Path; p=Path(" + repr(directory) + "); "
                "m=json.loads((p/'deployment.json').read_text()); "
                "assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h "
                "for n,h in m['files'].items()), 'upload checksum mismatch'")
    ssh(host, "python3 -c " + shlex.quote(verifier))
    ssh(host, "cd " + shlex.quote(REMOTE) + " && ln -sfn " +
        shlex.quote("releases/" + release) + " current.next && mv -Tf current.next current")
    print("Deployed and verified:", release, "(no program started)")


def run_logged(host, command, arguments):
    directory = PROJECT / "logs"
    directory.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    log = directory / (timestamp + "-" + command + ".jsonl")
    remote = ("cd " + shlex.quote(REMOTE + "/current") +
              " && brickrun -r -- pybricks-micropython main.py " +
              " ".join(shlex.quote(arg) for arg in [command] + arguments))
    print("Log:", log, flush=True)
    with log.open("w") as stream:
        # brickrun can forward program output to stderr. Merge both channels so
        # the saved log includes actual sensor records, not an empty stdout.
        process = subprocess.Popen(["ssh"] + OPTIONS + [host, remote], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True)
        try:
            for line in process.stdout:
                try:
                    record = json.loads(line)
                except ValueError:
                    record = {"event": "diagnostic", "message": line.rstrip()}
                stream.write(json.dumps(record) + "\n")
                stream.flush()
                print(line, end="", flush=True)
            result = process.wait()
        except BaseException:
            process.terminate()
            process.wait()
            raise
    if result:
        raise subprocess.CalledProcessError(result, remote)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("deploy", "inspect", "monitor"))
    parser.add_argument("--host", default=os.environ.get("EV3_HOST", "ev3"),
                        help="SSH host alias (default: ev3; see scripts/setup_connection.py)")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--mode", choices=("current", "rgb", "reflect", "color"), default="current")
    args = parser.parse_args()
    if not args.host or args.host.startswith("-") or any(c.isspace() for c in args.host):
        parser.error("Invalid SSH host")
    if not 1 <= args.samples <= 6000 or not 0.02 <= args.interval <= 5 or args.samples * args.interval > 600:
        parser.error("Use 1..6000 samples, 0.02..5 second interval, at most 600 seconds")
    if args.command == "deploy":
        deploy(args.host)
    else:
        arguments = [str(args.samples), str(args.interval), args.mode] if args.command == "monitor" else []
        run_logged(args.host, args.command, arguments)


if __name__ == "__main__":
    main()
