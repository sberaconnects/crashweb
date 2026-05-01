#!/usr/bin/env python3
"""
collect-all.py — Collect coredumps from multiple devices in parallel.

Usage:
    # Run once across all devices
    python3 collect-all.py --devices 192.168.1.100 192.168.1.101 192.168.1.102

    # Poll every 5 minutes for 2 hours
    python3 collect-all.py --devices 192.168.1.100 192.168.1.101 --duration 7200 --interval 300

    # Load device list from a file (one IP per line, optional: IP sw-version)
    python3 collect-all.py --devices-file devices.txt --duration 3600

    # devices.txt format (lines starting with # are ignored):
    #   192.168.1.100
    #   192.168.1.101 1.2.3-build.45
    #   192.168.1.102

    # Custom SSH user and CCS server
    python3 collect-all.py --devices 192.168.1.100 --ssh-user admin --server 10.0.0.1
"""
import argparse
import datetime
import os
import subprocess
import sys
import threading
import time

SCRIPT = os.path.join(os.path.dirname(__file__), "collect.py")
PYTHON = sys.executable

_print_lock = threading.Lock()


def log(device: str, msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with _print_lock:
        print(f"[{ts}] [{device}] {msg}", flush=True)


def collect_device(device: str, version: str | None, extra_args: list[str]):
    cmd = [PYTHON, "-u", SCRIPT, "--device", device] + extra_args
    if version:
        cmd += ["--version", version]
    log(device, "Starting collection...")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            log(device, line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            log(device, f"[warn] exited with code {proc.returncode}")
        else:
            log(device, "Done.")
    except Exception as e:
        log(device, f"[error] {e}")


def run_round(devices: list[tuple[str, str | None]], extra_args: list[str]):
    """Run one collection pass across all devices in parallel threads."""
    threads = []
    for ip, ver in devices:
        t = threading.Thread(target=collect_device, args=(ip, ver, extra_args), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def parse_devices_file(path: str) -> list[tuple[str, str | None]]:
    devices = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            ip = parts[0]
            ver = parts[1] if len(parts) > 1 else None
            devices.append((ip, ver))
    return devices


def main():
    parser = argparse.ArgumentParser(
        description="Collect coredumps from multiple devices in parallel"
    )
    dev_group = parser.add_mutually_exclusive_group(required=True)
    dev_group.add_argument("--devices", nargs="+", metavar="IP",
                           help="One or more device IPs to collect from")
    dev_group.add_argument("--devices-file", metavar="FILE",
                           help="File with one IP per line (optional: IP version)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Total run duration in seconds (0 = run once, default: 0)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Seconds between collection rounds (default: 60)")

    # CCS server
    parser.add_argument("--server", default="127.0.0.1",
                        help="CCS server IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5555,
                        help="CCS server port (default: 5555)")
    parser.add_argument("--web-port", type=int, default=8080,
                        help="Web UI port for result URL hint (default: 8080)")

    # SSH
    parser.add_argument("--ssh-user", default="root",
                        help="SSH username (default: root)")
    parser.add_argument("--ssh-port", type=int, default=22,
                        help="SSH port (default: 22)")
    parser.add_argument("--ssh-key", default=None,
                        help="Path to SSH private key")
    parser.add_argument("--ssh-pass", default=None,
                        help="SSH password (prefer key-based auth)")

    # Device DB registration
    parser.add_argument("--name", default="device",
                        help="Device name in DB (default: device)")
    parser.add_argument("--label", default="",
                        help="Device label in DB (default: empty)")
    parser.add_argument("--device-type", type=int, default=0,
                        help="Device type integer in DB (default: 0)")
    parser.add_argument("--container", default="crashweb-mariadb-1",
                        help="MariaDB Docker container name (default: crashweb-mariadb-1)")
    parser.add_argument("--version-key", default=None,
                        help="Specific /etc/os-release key for version detection")

    args = parser.parse_args()

    if args.devices_file:
        devices = parse_devices_file(args.devices_file)
    else:
        devices = [(ip, None) for ip in args.devices]

    if not devices:
        print("ERROR: No devices specified.")
        sys.exit(1)

    extra_args = [
        "--server", args.server,
        "--port", str(args.port),
        "--web-port", str(args.web_port),
        "--ssh-user", args.ssh_user,
        "--ssh-port", str(args.ssh_port),
        "--name", args.name,
        "--label", args.label,
        "--device-type", str(args.device_type),
        "--container", args.container,
    ]
    if args.ssh_key:
        extra_args += ["--ssh-key", args.ssh_key]
    if args.ssh_pass:
        extra_args += ["--ssh-pass", args.ssh_pass]
    if args.version_key:
        extra_args += ["--version-key", args.version_key]

    print(f"Devices ({len(devices)}): {[ip for ip, _ in devices]}")
    print(f"CCS server: {args.server}:{args.port}  Container: {args.container}")
    if args.duration:
        print(f"Running for {args.duration}s, polling every {args.interval}s. Press Ctrl+C to stop.")
    else:
        print("Running once.")

    deadline = time.monotonic() + args.duration if args.duration else None
    round_num = 0
    try:
        while True:
            round_num += 1
            if deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    print("Duration reached, stopping.")
                    break
                print(f"\n--- Round {round_num} (remaining: {int(remaining)}s) ---")
            else:
                print(f"\n--- Round {round_num} ---")
            run_round(devices, extra_args)
            if not deadline:
                break
            sleep_for = min(args.interval, deadline - time.monotonic())
            if sleep_for > 0:
                print(f"Waiting {int(sleep_for)}s until next round...")
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    print(f"\nAll done. Open http://{args.server}:{args.web_port}/")


if __name__ == "__main__":
    main()
