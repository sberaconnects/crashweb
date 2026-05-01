#!/usr/bin/env python3
"""
collect.py — Pull coredumps from a device and upload to a local CrashWeb stack.

Usage:
    # Version auto-detected from /etc/os-release on the device
    python3 collect.py --device 192.168.1.100

    # Specify version explicitly
    python3 collect.py --device 192.168.1.100 --version 1.2.3-build.45

    # Custom SSH user and CCS server
    python3 collect.py --device 192.168.1.100 --ssh-user admin --server 10.0.0.1

    # Load SSH key from a specific path
    python3 collect.py --device 192.168.1.100 --ssh-key ~/.ssh/id_device

Requirements:
    pip install paramiko
"""
import argparse
import datetime
import gzip
import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile

try:
    import paramiko
except ImportError:
    print("ERROR: paramiko not installed. Run: pip install paramiko")
    sys.exit(1)

# --- Defaults ---
DEFAULT_SERVER = "127.0.0.1"
DEFAULT_PORT = 5555
DEFAULT_SSH_USER = "root"
DEFAULT_SSH_PORT = 22
DEFAULT_CONTAINER = "crashweb-mariadb-1"
SEEN_FILE = os.path.join(os.path.dirname(__file__), ".seen_coredumps.json")

# Ordered list of /etc/os-release keys to try for SW version detection
VERSION_KEYS = [
    "BUILD_VERSION",
    "IMAGE_VERSION",
    "OS_VERSION",
    "VERSION_ID",
    "VERSION",
]

SIGNAL_NUMBERS = {
    "SIGHUP": 1, "SIGINT": 2, "SIGQUIT": 3, "SIGILL": 4, "SIGTRAP": 5,
    "SIGABRT": 6, "SIGBUS": 7, "SIGFPE": 8, "SIGKILL": 9, "SIGUSR1": 10,
    "SIGSEGV": 11, "SIGUSR2": 12, "SIGPIPE": 13, "SIGALRM": 14, "SIGTERM": 15,
    "SIGXCPU": 24, "SIGXFSZ": 25,
}


def load_seen() -> set:
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, ValueError):
        return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)


def signal_number(sig: str) -> str:
    if sig.lstrip("-").isdigit():
        return sig
    return str(SIGNAL_NUMBERS.get(sig.upper(), sig))


def pad512(s: str) -> bytes:
    b = s.encode("utf-8")[:511]
    return b.ljust(512, b"\x00")


def connect_ssh(device_ip: str, user: str, port: int,
                password: str | None, key_path: str | None) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = dict(
        hostname=device_ip,
        port=port,
        username=user,
        timeout=10,
    )
    if key_path:
        connect_kwargs["key_filename"] = os.path.expanduser(key_path)
        connect_kwargs["look_for_keys"] = False
        connect_kwargs["allow_agent"] = False
    elif password is not None:
        connect_kwargs["password"] = password
        connect_kwargs["look_for_keys"] = False
        connect_kwargs["allow_agent"] = False
    else:
        # Key-based: let paramiko try default key locations and agent
        connect_kwargs["password"] = ""
        connect_kwargs["look_for_keys"] = True
        connect_kwargs["allow_agent"] = True

    client.connect(**connect_kwargs)
    return client


def run_ssh(client: paramiko.SSHClient, cmd: str, timeout: int = 30) -> str:
    _, stdout, _ = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode(errors="replace").strip()


def detect_version(client: paramiko.SSHClient) -> str:
    """Read SW version from /etc/os-release, trying multiple common keys."""
    out = run_ssh(client, "cat /etc/os-release 2>/dev/null || true")
    for key in VERSION_KEYS:
        m = re.search(rf'^{key}=["\']?([^"\'\n]+)["\']?', out, re.MULTILINE)
        if m:
            v = m.group(1).strip()
            print(f"  [version] Detected from {key}: {v}")
            return v
    raise RuntimeError(
        f"Could not detect SW version from /etc/os-release. "
        f"Tried: {VERSION_KEYS}. Use --version to specify manually."
    )


def list_coredumps(client: paramiko.SSHClient) -> list[dict]:
    """Return list of coredumps via coredumpctl on the device."""
    out = run_ssh(client, "coredumpctl list --no-pager --no-legend -q 2>/dev/null || echo ''")
    entries = []
    for line in out.splitlines():
        parts = line.split()
        # Format: DOW DATE TIME TZ PID UID GID SIG COREFILE EXE [SIZE ...]
        if len(parts) < 10:
            continue
        try:
            pid = parts[4]
            signal = parts[7]
            exe = os.path.basename(parts[9]) if parts[9] != "-" else "unknown"
            crash_time = f"{parts[1]} {parts[2]}"
            if not pid.isdigit():
                continue
            entries.append({"pid": pid, "signal": signal, "exe": exe, "time": crash_time})
        except (IndexError, ValueError):
            continue
    return entries


def fetch_core_gz(client: paramiko.SSHClient, pid: str, tmp_dir: str) -> str | None:
    """Export core from device via coredumpctl, compress it locally, return gz path."""
    remote_path = f"/tmp/core_{pid}.raw"
    local_raw = os.path.join(tmp_dir, f"core_{pid}.raw")
    local_gz = local_raw + ".gz"

    rc = run_ssh(client, f"coredumpctl dump {pid} -o {remote_path} 2>/dev/null; echo $?", timeout=120)
    if rc.strip().splitlines()[-1] != "0":
        return None

    sftp = client.open_sftp()
    try:
        sftp.get(remote_path, local_raw)
    except Exception as e:
        print(f"  [warn] Could not fetch core for PID {pid}: {e}")
        return None
    finally:
        sftp.close()
        run_ssh(client, f"rm -f {remote_path}")

    with open(local_raw, "rb") as f_in, gzip.open(local_gz, "wb") as f_out:
        while chunk := f_in.read(1024 * 1024):
            f_out.write(chunk)
    os.unlink(local_raw)
    return local_gz


def fetch_journal(client: paramiko.SSHClient, pid: str, exe: str,
                  crash_time: str = "", max_lines: int = 100) -> list[tuple]:
    """Pull journal lines around the crash timestamp for the crashed executable."""
    unit = exe.replace("_", "-")
    if crash_time:
        try:
            ct = datetime.datetime.strptime(crash_time, "%Y-%m-%d %H:%M:%S")
            since = (ct - datetime.timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
            until = (ct + datetime.timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
            time_args = f"--since '{since}' --until '{until}'"
        except ValueError:
            time_args = f"-n {max_lines}"
    else:
        time_args = f"-n {max_lines}"

    def _by_unit(args: str) -> str:
        return run_ssh(client,
            f"journalctl -u '{unit}*' {args} --no-pager -q 2>/dev/null || true"
        )

    def _by_pid(args: str) -> str:
        return run_ssh(client,
            f"journalctl _PID={pid} {args} --no-pager -q 2>/dev/null || true"
        )

    def _parse(out: str) -> list[tuple]:
        result = []
        year = datetime.datetime.now().year
        for raw in out.splitlines():
            ts_us = 0
            m = re.match(r"(\w{3}\s+\d+\s+\d+:\d+:\d+)", raw)
            if m:
                try:
                    dt = datetime.datetime.strptime(f"{year} {m.group(1)}", "%Y %b %d %H:%M:%S")
                    ts_us = int(dt.timestamp() * 1_000_000)
                except ValueError:
                    pass
            result.append((ts_us, raw[:511]))
            if len(result) >= max_lines:
                break
        return result

    lines = _parse(_by_unit(time_args))
    if not lines:
        lines = _parse(_by_pid(time_args))
        if lines:
            print(f"  [journal] {len(lines)} line(s) for {unit} via _PID={pid}")
        elif time_args != f"-n {max_lines}":
            lines = _parse(_by_unit(f"-n {max_lines}"))
            if not lines:
                lines = _parse(_by_pid(f"-n {max_lines}"))
                if lines:
                    print(f"  [journal] Time window empty; {len(lines)} recent line(s) via _PID={pid}")
                else:
                    print(f"  [journal] No journal found for {unit} (PID {pid})")
            else:
                print(f"  [journal] Time window empty for {unit}; using {len(lines)} recent line(s)")
        else:
            print(f"  [journal] No journal found for {unit} (PID {pid})")
    else:
        print(f"  [journal] {len(lines)} line(s) for {unit} ({time_args})")
    return lines


def upload(server: str, port: int, device_ip: str, version: str,
           core_name: str, journal_lines: list, core_gz: str):
    with socket.create_connection((server, port), timeout=60) as sock:
        sock.sendall(pad512(core_name))
        sock.sendall(pad512(f"{version}|{device_ip}"))
        for i in range(100):
            ts_us, line = journal_lines[i] if i < len(journal_lines) else (0, "")
            sock.sendall(struct.pack("<Q", ts_us))
            sock.sendall(pad512(line))
        with open(core_gz, "rb") as f:
            while chunk := f.read(1024 * 1024):
                sock.sendall(chunk)


def ensure_device_registered(device_ip: str, version: str,
                              name: str, label: str,
                              device_type: int, container: str):
    """Insert device and SW revision into the CrashWeb MariaDB if missing."""
    v = version if version.startswith("v") else f"v{version}"
    cmds = [
        f"mysql -u ccs coredumps -e \""
        f"INSERT IGNORE INTO cla_devices "
        f"(cla_eqm_name, cla_eqm_label, cla_ip_addr, cla_eqm_type) "
        f"VALUES ('{name}', '{label}', '{device_ip}', {device_type});\"",

        f"mysql -u ccs coredumps -e \""
        f"INSERT IGNORE INTO cla_sw_rev (clb_rev, clb_type) "
        f"VALUES ('{v}', 1);\"",
    ]
    for cmd in cmds:
        result = subprocess.run(
            ["docker", "exec", container, "bash", "-c", cmd],
            capture_output=True,
        )
        if result.returncode != 0:
            err = result.stderr.decode().strip()
            if err:
                print(f"  [db] Warning: {err}")


def main():
    parser = argparse.ArgumentParser(
        description="Collect coredumps from a device and upload to CrashWeb"
    )
    parser.add_argument("--device", required=True,
                        help="Device IP address, e.g. 192.168.1.100")
    parser.add_argument("--version", default=None,
                        help="SW version string (auto-detected from /etc/os-release if omitted)")
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help=f"CCS server IP (default: {DEFAULT_SERVER})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"CCS server port (default: {DEFAULT_PORT})")
    parser.add_argument("--web-port", type=int, default=8080,
                        help="Web UI port for result URL hint (default: 8080)")
    parser.add_argument("--ssh-user", default=DEFAULT_SSH_USER,
                        help=f"SSH username (default: {DEFAULT_SSH_USER})")
    parser.add_argument("--ssh-port", type=int, default=DEFAULT_SSH_PORT,
                        help=f"SSH port (default: {DEFAULT_SSH_PORT})")
    parser.add_argument("--ssh-key", default=None,
                        help="Path to SSH private key (default: use agent/default keys)")
    parser.add_argument("--ssh-pass", default=None,
                        help="SSH password (prefer key-based auth)")
    parser.add_argument("--name", default="device",
                        help="Device name in DB (default: device)")
    parser.add_argument("--label", default="",
                        help="Device label in DB (default: empty)")
    parser.add_argument("--device-type", type=int, default=0,
                        help="Device type integer in DB (default: 0)")
    parser.add_argument("--container", default=DEFAULT_CONTAINER,
                        help=f"MariaDB Docker container name (default: {DEFAULT_CONTAINER})")
    parser.add_argument("--version-key", default=None,
                        help=f"Specific /etc/os-release key for version (default: tries {VERSION_KEYS})")
    args = parser.parse_args()

    if args.version_key:
        VERSION_KEYS.insert(0, args.version_key)

    print(f"Connecting to {args.device} (user: {args.ssh_user}, port: {args.ssh_port}) ...")
    try:
        client = connect_ssh(
            args.device, args.ssh_user, args.ssh_port,
            args.ssh_pass, args.ssh_key,
        )
    except Exception as e:
        print(f"ERROR: SSH failed: {e}")
        sys.exit(1)

    version = args.version
    if not version:
        try:
            version = detect_version(client)
        except Exception as e:
            print(f"ERROR: {e}")
            client.close()
            sys.exit(1)
    else:
        print(f"Using version: {version}")

    ensure_device_registered(
        args.device, version,
        name=args.name, label=args.label,
        device_type=args.device_type,
        container=args.container,
    )

    seen = load_seen()
    entries = list_coredumps(client)
    if not entries:
        print("No coredumps found on device.")
        client.close()
        return

    new_entries = [e for e in entries if f"{args.device}:{e['pid']}" not in seen]
    skip_count = len(entries) - len(new_entries)
    print(f"  {len(entries)} coredump(s) on device: {len(new_entries)} new, {skip_count} already uploaded")

    new_count = 0
    with tempfile.TemporaryDirectory() as tmp:
        for idx, entry in enumerate(new_entries, 1):
            pid = entry["pid"]
            key = f"{args.device}:{pid}"

            core_gz = fetch_core_gz(client, pid, tmp)
            if not core_gz:
                print(f"  [warn] [{idx}/{len(new_entries)}] PID {pid} ({entry['exe']}): could not dump core, skipping")
                continue

            journal = fetch_journal(client, pid, entry["exe"], entry.get("time", ""))
            device_octet = ".".join(args.device.split(".")[-2:])
            sig_num = signal_number(entry["signal"])
            core_name = f"coredumps/core-{entry['exe']}-{device_octet}-manual-{pid}-{sig_num}"

            try:
                upload(args.server, args.port, args.device, version,
                       core_name, journal, core_gz)
                seen.add(key)
                new_count += 1
                print(f"  [{idx}/{len(new_entries)}] {entry['exe']} ({entry['signal']}) PID {pid} — uploaded")
            except Exception as e:
                print(f"  [error] [{idx}/{len(new_entries)}] PID {pid}: {e}")

    save_seen(seen)
    client.close()
    print(f"\nDone. Uploaded {new_count} new coredump(s). Open http://{args.server}:{args.web_port}/")


if __name__ == "__main__":
    main()
