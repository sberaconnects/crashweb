#!/usr/bin/env python3
import socket
import threading
import logging
import datetime
import mariadb
import sys
import gzip
import subprocess
import os
import time
import http.server
import urllib.request
import urllib.parse
import json
import re

# Dedup: track core IDs currently being recovered to avoid parallel duplicates
_recovering_cores: set = set()
_recovering_lock = threading.Lock()

# Disk-space safety: evict oldest cores when usage crosses this threshold.
# Override with env var CORE_DISK_HIGH_WATER_PCT (0-99).
_DISK_HIGH_WATER_PCT = int(os.environ.get("CORE_DISK_HIGH_WATER_PCT", "85"))
_COREDUMP_SPACE = "/space/coredumps"
# Serialize the check-evict-write sequence across concurrent connections.
_disk_guard_lock = threading.Lock()

from bt_utils import _bt_signature, _sdk_build
from elftools.elf.elffile import ELFFile
from elftools.elf.segments import NoteSegment
from sys import argv


def _disk_usage_pct(path):
    """Return the percentage of used space on the filesystem containing *path*.

    Returns 0.0 if the path does not exist yet (e.g. fresh deploy before any
    core has been written), so the guard is a no-op until the directory is
    created.
    """
    try:
        st = os.statvfs(path)
    except OSError:
        return 0.0
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    return 100.0 * (total - free) / total if total > 0 else 0.0


def _evict_oldest_core(cur):
    """Evict the physical .gz file of the oldest core to reclaim disk space.

    The DB record (cla_core, cla_backtrace, cla_journal) is preserved as an
    audit trail.  clc_core_file is set to NULL to signal the file is gone.
    Returns the path that was deleted, or None if no evictable core exists.
    """
    cur.execute(
        "SELECT clc_id, clc_core_file FROM cla_core "
        "WHERE clc_core_file IS NOT NULL ORDER BY clc_date ASC LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return None
    core_id, core_file = row
    fpath = f"/space/{core_file}"
    try:
        os.unlink(fpath)
    except OSError as e:
        logging.warning(f"Eviction: could not delete {fpath}: {e}")
    cur.execute("UPDATE cla_core SET clc_core_file = NULL WHERE clc_id = ?", [core_id])
    return core_file


class ClientThread(threading.Thread):

    def __init__(self, ip, port, sock):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock

    def getCoreBinary(self, head):
        with gzip.open(head,'rb') as stream:
            elffile = ELFFile(stream)
            for seg in elffile.iter_segments():
                if not isinstance(seg, NoteSegment):
                    continue
                for note in seg.iter_notes():
                    if note["n_type"] == "NT_FILE":
                        execfile = note["n_desc"]["filename"][0].decode("utf8")
                        return execfile

        return "bin"

    def updateCoreBinary(self, core_id, execfile):
        self.cur.execute("UPDATE cla_core SET clc_core_binary = ? WHERE clc_id = ?", [execfile, core_id])

    @staticmethod
    def _run_backtrace(core_id, execfile, corefile, build):
        """Extract and store GDB backtrace. Assumes SDK is present."""
        sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
        # Use thread-id in temp filename to avoid collisions between concurrent runs
        tmp = f"core_{core_id}_{threading.get_ident()}"
        with gzip.open(corefile, 'rb') as stream:
            with open(tmp, "wb") as file:
                while True:
                    content = stream.read(1048576)
                    if not content:
                        break
                    file.write(content)
        try:
            cwd = os.getcwd()
            gdb_timed_out = False
            proc = subprocess.Popen(
                ["gdb-multiarch", "-batch", "-iex", f"set sysroot {sdk}", f"{sdk}/{execfile}", f"{cwd}/{tmp}", "-ex", "bt"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            try:
                stdout, stderr = proc.communicate(timeout=120)
                bt = stdout + stderr
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                logging.error(f"GDB timed out after 120s for core {core_id} — marking as failed")
                gdb_timed_out = True
                bt = ""
            i = 1
            all_frames = []
            conn = mariadb.connect(user="ccs", host="mariadb", port=3306, database="coredumps")
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("DELETE FROM cla_backtrace WHERE cle_core = ?", [core_id])
            if gdb_timed_out:
                cur.execute("INSERT INTO cla_backtrace (cle_core, cle_line_no, cle_line) VALUES(?, ?, ?)",
                            [core_id, 0, "[No backtrace: GDB timed out — core file may be corrupt or too large]"])
            else:
                for btl in bt.split('\n'):
                    if btl.startswith('#'):
                        cur.execute("INSERT INTO cla_backtrace (cle_core, cle_line_no, cle_line) VALUES(?, ?, ?)", [core_id, i, btl[0:511]])
                        all_frames.append(btl)
                        i = i + 1
            cur.execute("UPDATE cla_core SET clc_bt_csum = ? WHERE clc_id = ?", [_bt_signature(all_frames), core_id])
            conn.commit()
            conn.close()
            if gdb_timed_out:
                logging.warning(f"Core {core_id} marked as GDB timeout (0 frames)")
            else:
                logging.info(f"Backtrace generated for core {core_id} ({i-1} frames)")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    @staticmethod
    @staticmethod
    def _wait_and_retry_backtrace(core_id, execfile, corefile, build):
        """Background thread: wait for SDK to be installed, then generate backtrace."""
        sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
        deadline = time.time() + 86400  # wait up to 24 hours
        interval = 30
        while time.time() < deadline:
            if os.path.isdir(sdk):
                # Dedup: skip if another thread (recovery or API) is already processing this core
                with _recovering_lock:
                    if core_id in _recovering_cores:
                        logging.info(f"Core {core_id} already being processed by another thread — skipping retry")
                        return
                    _recovering_cores.add(core_id)
                try:
                    logging.info(f"SDK v{build} is now available — generating backtrace for core {core_id}")
                    ClientThread._run_backtrace(core_id, execfile, corefile, build)
                except Exception as e:
                    logging.error(f"Backtrace retry failed for core {core_id}: {e}")
                finally:
                    with _recovering_lock:
                        _recovering_cores.discard(core_id)
                return
            time.sleep(interval)
        logging.warning(f"SDK v{build} never appeared — giving up on backtrace for core {core_id}")

    def generateBacktrace(self, core_id, execfile, corefile, build):
        sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
        if not os.path.isdir(sdk):
            logging.warning(f"SDK v{build} not found — queuing backtrace retry for core {core_id} (install SDK manually via dashboard)")
            self.cur.execute("INSERT INTO cla_backtrace (cle_core, cle_line_no, cle_line) VALUES(?, ?, ?)",
                             [core_id, 0, f"[Pending: SDK v{build} not yet installed — open this core to install]"])
            t = threading.Thread(target=ClientThread._wait_and_retry_backtrace, args=(core_id, execfile, corefile, build), daemon=True)
            t.start()
            return
        ClientThread._run_backtrace(core_id, execfile, corefile, build)

    def connectDB(self):
        try:
            conn = mariadb.connect(
                    user="ccs",
                    host="mariadb",
                    port=3306,
                    database="coredumps"
                    )
            conn.autocommit = True
            self.conn = conn
            self.cur = conn.cursor()
        except mariadb.Error as e:
            self.conn = None
            self.cur = None
            print(e)

    def getSwRevKey(self, build):
        b = "v" + build.strip()
        self.cur.execute("SELECT clb_id FROM cla_sw_rev WHERE clb_rev = ? AND clb_type = ?", [b, self.device_type])
        for row in self.cur:
            return row[0]
        self.cur.execute("INSERT INTO cla_sw_rev (clb_rev, clb_type) VALUES(?, ?)", [b, self.device_type])
        return self.cur.lastrowid

    def getDeviceInfo(self, ip):
        self.cur.execute("SELECT cla_id, cla_eqm_type FROM cla_devices WHERE cla_ip_addr = ?", [ip])
        for row in self.cur:
            self.device_id = row[0]
            self.device_type = row[1]
            return
        self.cur.execute("INSERT INTO cla_devices (cla_ip_addr, cla_eqm_name, cla_eqm_label, cla_eqm_type) VALUES(?, 'Delta Transport', 'Delta Transport', 0)", [ip])
        self.device_id = self.cur.lastrowid
        self.device_type = 0

    def disectName(self, head):
        # New format: coredumps/core-{exe}-{octet3.octet4}-manual-{pid}-{signal}
        # Old format: coredumps/core-{exe}-{something}-{pid}-{signal}
        pos = head.rfind('-')
        csignal = int(head[pos+1:len(head)])
        pos = head.rfind('-', 0, pos)  # skip pid
        if '-manual-' in head:
            pos = head.rfind('-', 0, pos)  # skip 'manual'
            pos = head.rfind('-', 0, pos)  # skip octet3.octet4 device suffix
        else:
            pos = head.rfind('-', 0, pos)  # skip legacy extra field
        start = head.find('/')
        cname = head[start+1:pos]
        return (csignal, cname)

    def createCoreDB(self, head, build, device_ip):
        (csignal, cname) = self.disectName(head)
        self.getDeviceInfo(device_ip)
        self.cur.execute("INSERT INTO cla_core (clc_sw_rev, clc_device, clc_date, clc_core_name, clc_core_binary, clc_core_signal, clc_core_file) VALUES(?, ?, NOW(), ?, ?, ?, ?)", (self.getSwRevKey(build), self.device_id, cname, "bin", csignal, f"{head}.gz"))
        return self.cur.lastrowid

    def recv_loop(self, MSGLEN):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 512))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)


    def insertIntoJournalDB(self, core_id, lineno, message, date):
        self.cur.execute("INSERT INTO cla_journal (cld_core, cld_line_no, cld_line, cld_date) VALUES(?, ?, ?, ?)", (core_id, lineno, message, date))
        pass

    def read_journal(self, core_id):
        for i in range(0, 100):
            timestamp = int.from_bytes(self.recv_loop(8), byteorder='little')
            bin_msg = self.recv_loop(512)
            if (timestamp == 0):
                continue
            message = bin_msg.decode("utf8").replace("\0", "")
            timestr = datetime.datetime.utcfromtimestamp(timestamp/1000000).strftime('%Y-%m-%d %H:%M:%S')
            self.insertIntoJournalDB(core_id, i, message, timestr)

    def run(self):
        head = self.sock.recv(512)
        head = head.decode("utf8").replace("\0", "").replace(" ", "_")
        build = self.sock.recv(512)
        build = build.decode("utf8").replace("\0", "").replace(" ", "_")
        # build field may be "version|device_ip" — split if present
        if "|" in build:
            build_ver, device_ip = build.split("|", 1)
        else:
            build_ver, device_ip = build, self.ip
        logging.info(f"Got connection from {self.ip}:{self.port} for {head} ...")

        self.connectDB()

        # Disk-space guard: hold lock so concurrent connections don't race.
        # createCoreDB is intentionally deferred until after we have space.
        with _disk_guard_lock:
            pct = _disk_usage_pct(_COREDUMP_SPACE)
            if pct >= _DISK_HIGH_WATER_PCT:
                logging.warning(
                    f"Disk usage {pct:.1f}% >= {_DISK_HIGH_WATER_PCT}% — evicting oldest cores to make room"
                )
                # Open a temporary cursor for evictions (no pending createCoreDB row yet).
                evict_conn = mariadb.connect(user="ccs", host="mariadb", port=3306, database="coredumps")
                evict_conn.autocommit = True
                evict_cur = evict_conn.cursor()
                while pct >= _DISK_HIGH_WATER_PCT:
                    evicted = _evict_oldest_core(evict_cur)
                    if evicted is None:
                        logging.error(
                            "No more cores to evict but disk is still full — "
                            "dropping incoming core to protect the server"
                        )
                        evict_conn.close()
                        self.conn.close()
                        self.sock.close()
                        return
                    logging.warning(f"Evicted core file {evicted} to reclaim disk space")
                    pct = _disk_usage_pct(_COREDUMP_SPACE)
                evict_conn.close()
                logging.info(f"Disk usage now {pct:.1f}% — proceeding with new core")

        core_id = self.createCoreDB(head, build_ver, device_ip)
        self.read_journal(core_id)

        with open(f"/space/{head}.gz", "wb") as out:
            while True:
                data = self.sock.recv(1048576)
                if len(data) > 0:
                    out.write(data)
                else:
                    break

        self.sock.close()

        execfile = self.getCoreBinary(f"/space/{head}.gz")
        self.updateCoreBinary(core_id, execfile)
        self.generateBacktrace(core_id, execfile, f"/space/{head}.gz", _sdk_build(build_ver))

        self.conn.commit()
        self.conn.close()
        logging.info(f"Closed connection to {self.ip}:{self.port} ...")

host = ""
port = 5555

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Limit concurrent GDB processes during bulk recovery
_recovery_sem = threading.Semaphore(4)

def _recover_one(core_id, execfile, corefile_path, build):
    """Run backtrace for a single core under the recovery semaphore."""
    sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
    try:
        with _recovery_sem:
            if os.path.isdir(sdk):
                try:
                    ClientThread._run_backtrace(core_id, execfile, corefile_path, build)
                except Exception as e:
                    logging.error(f"Recovery backtrace failed for core {core_id}: {e}")
            else:
                # Update placeholder to [Pending:] and wait for SDK
                try:
                    conn = mariadb.connect(user="ccs", host="mariadb", port=3306, database="coredumps")
                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute("UPDATE cla_backtrace SET cle_line = ? WHERE cle_core = ?",
                                [f"[Pending: SDK v{build} not yet installed — open this core to install]", core_id])
                    conn.close()
                except Exception as e:
                    logging.warning(f"Could not update placeholder for core {core_id}: {e}")
                ClientThread._wait_and_retry_backtrace(core_id, execfile, corefile_path, build)
    finally:
        with _recovering_lock:
            _recovering_cores.discard(core_id)

def recover_pending_backtraces():
    """On startup, re-spawn retry threads for [Pending:] and [No backtrace:] entries."""
    deadline = time.time() + 60
    conn = None
    while time.time() < deadline:
        try:
            conn = mariadb.connect(user="ccs", host="mariadb", port=3306, database="coredumps")
            conn.autocommit = True
            break
        except mariadb.Error as e:
            logging.info(f"Waiting for MariaDB ({e}) ...")
            time.sleep(3)
    if not conn:
        logging.warning("MariaDB not ready — skipping startup recovery of pending backtraces")
        return
    cur = conn.cursor()
    cur.execute(
        "SELECT b.cle_core, c.clc_core_binary, c.clc_core_file, r.clb_rev "
        "FROM cla_backtrace b "
        "JOIN cla_core c ON b.cle_core = c.clc_id "
        "JOIN cla_sw_rev r ON c.clc_sw_rev = r.clb_id "
        "WHERE b.cle_line LIKE '[Pending:%' OR b.cle_line LIKE '[No backtrace: SDK%'"
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        logging.info("No pending/failed backtraces to recover")
        return
    logging.info(f"Recovering {len(rows)} backtrace(s) ...")
    for (core_id, execfile, corefile, sw_rev) in rows:
        build = _sdk_build(sw_rev)
        corefile_path = f"/space/{corefile}"
        if not os.path.isfile(corefile_path):
            logging.warning(f"Core file {corefile_path} missing — cannot recover core {core_id}")
            continue
        with _recovering_lock:
            if core_id in _recovering_cores:
                continue
            _recovering_cores.add(core_id)
        sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
        t = threading.Thread(
            target=_recover_one,
            args=(core_id, execfile, corefile_path, build),
            daemon=True
        )
        t.start()

class _CCSApiHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP API for on-demand backtrace reprocessing."""
    def log_message(self, format, *args):
        pass  # suppress default access log

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        content_len = int(self.headers.get('Content-Length', 0))
        if content_len:
            self.rfile.read(content_len)
        if parsed.path != '/reprocess':
            self._send(404, {'error': 'Not found'})
            return
        core_id_str = params.get('core_id', [None])[0]
        if not core_id_str or not core_id_str.isdigit():
            self._send(400, {'error': 'Missing or invalid core_id'})
            return
        core_id = int(core_id_str)
        try:
            conn = mariadb.connect(user="ccs", host="mariadb", port=3306, database="coredumps")
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(
                "SELECT c.clc_core_binary, c.clc_core_file, r.clb_rev "
                "FROM cla_core c JOIN cla_sw_rev r ON c.clc_sw_rev = r.clb_id "
                "WHERE c.clc_id = ?", [core_id]
            )
            row = cur.fetchone()
            conn.close()
        except Exception as e:
            logging.error(f"[ccs-api] DB error for core {core_id}: {e}")
            self._send(500, {'error': 'Database error'})
            return
        if not row:
            self._send(404, {'error': 'Core not found'})
            return
        execfile, corefile, sw_rev = row
        if not corefile:
            self._send(409, {'error': 'Core file has been evicted'})
            return
        build = _sdk_build(sw_rev)
        sdk = f"/space/sdks/v{build}/sysroots/cortexa53-crypto-mgl-linux"
        if not os.path.isdir(sdk):
            self._send(409, {'error': f'SDK v{build} not installed'})
            return
        corefile_path = f"/space/{corefile}"
        if not os.path.isfile(corefile_path):
            self._send(409, {'error': 'Core file missing on disk'})
            return
        with _recovering_lock:
            if core_id in _recovering_cores:
                self._send(200, {'status': 'already_processing'})
                return
            _recovering_cores.add(core_id)
        t = threading.Thread(
            target=_recover_one,
            args=(core_id, execfile, corefile_path, build),
            daemon=True
        )
        t.start()
        logging.info(f"[ccs-api] On-demand reprocess triggered for core {core_id}")
        self._send(200, {'status': 'started'})

    def _send(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def _start_ccs_api():
    server = http.server.HTTPServer(('', 5556), _CCSApiHandler)
    logging.info('[ccs-api] HTTP API listening on :5556')
    server.serve_forever()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((host, port))
sock.listen(5)

def _periodic_recovery():
    """Re-run recovery every 10 min to catch pending backtraces whose SDK became available."""
    while True:
        time.sleep(600)
        recover_pending_backtraces()

threading.Thread(target=_start_ccs_api, daemon=True).start()
threading.Thread(target=_periodic_recovery, daemon=True).start()
recover_pending_backtraces()
logging.info(f"Listening for coredumps at {host}:{port} ...")

try:
    while True:
        (clientsock, (ip, port)) = sock.accept()
        clientsock.settimeout(10)
        client_thread = ClientThread(ip, port, clientsock)
        client_thread.daemon = True
        client_thread.start()
except KeyboardInterrupt:
    logging.info("Stopping ...")
    exit(0)

