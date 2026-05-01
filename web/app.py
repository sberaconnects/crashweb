import base64
import hashlib
import logging
import signal
import struct
import json as _json
import os
import re
import shlex
import subprocess
import urllib.request
import zlib

from flask import Flask, jsonify, render_template, request, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sdk_space import evict_sdks_for_space


app = Flask(__name__)
app.config.from_pyfile('config.py')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
app.logger.setLevel(logging.INFO)

db = SQLAlchemy(app)

SIGNAL_NAMES = {
    1: "SIGHUP", 2: "SIGINT", 3: "SIGQUIT", 4: "SIGILL",
    5: "SIGTRAP", 6: "SIGABRT", 7: "SIGBUS", 8: "SIGFPE",
    9: "SIGKILL", 10: "SIGUSR1", 11: "SIGSEGV", 12: "SIGUSR2",
    13: "SIGPIPE", 14: "SIGALRM", 15: "SIGTERM", 16: "SIGSTKFLT",
    17: "SIGCHLD", 18: "SIGCONT", 19: "SIGSTOP", 20: "SIGTSTP",
    21: "SIGTTIN", 22: "SIGTTOU", 23: "SIGURG", 24: "SIGXCPU",
    25: "SIGXFSZ", 26: "SIGVTALRM", 27: "SIGPROF", 28: "SIGWINCH",
    29: "SIGIO", 30: "SIGPWR", 31: "SIGSYS",
}

app.jinja_env.globals['signal_name'] = lambda sig: SIGNAL_NAMES.get(sig, f"SIG?({sig})")

SIGXCPU = 24

# ── Badge helpers ───────────────────────────────────────────────────────────────────────
_BADGE_PALETTE = [
    '#0d6efd', '#198754', '#6f42c1', '#fd7e14',
    '#20c997', '#d63384', '#0a58ca', '#e65100',
    '#00796b', '#c0392b', '#1565c0', '#6d4c41',
    '#00838f', '#558b2f', '#ad1457', '#4527a0',
    '#f57f17', '#37474f', '#2e7d32', '#4a148c',
    '#bf360c', '#006064', '#1a237e', '#33691e',
    '#7b1fa2', '#1976d2', '#388e3c', '#f57c00',
    '#0097a7', '#c62828', '#283593', '#827717',
    '#4e342e', '#00695c', '#6a1b9a', '#0288d1',
    '#e64a19',
]


def badge_color(s):
    h = hashlib.sha1(s.encode()).digest()
    val = 0
    for i in range(0, 20, 4):
        val ^= struct.unpack('>I', h[i:i+4])[0]
    return _BADGE_PALETTE[val % len(_BADGE_PALETTE)]


app.jinja_env.globals['badge_color'] = badge_color

def ip_badge(ip):
    """Return colored badge HTML for an IP address, consistent per IP."""
    if not ip:
        return ''
    bg = badge_color(ip)
    return f'<span class="badge fw-normal font-monospace" style="background:{bg};color:#fff">{ip}</span>'

app.jinja_env.globals['ip_badge'] = ip_badge

def rev_badge(rev):
    """Return colored badge HTML for a SW revision, consistent per revision string."""
    if not rev:
        return ''
    bg = badge_color(rev)
    return f'<span class="badge fw-normal" style="background:{bg};color:#fff">{rev}</span>'

app.jinja_env.globals['rev_badge'] = rev_badge

# ── Crash classification ──────────────────────────────────────────────────────
_CRASH_PATTERNS = [
    (re.compile(r'watchdog timeout', re.I),                      'Watchdog Timeout', '#fd7e14'),
    (re.compile(r'Failed with result .watchdog', re.I),          'Watchdog Timeout', '#fd7e14'),
    (re.compile(r'out of memory|oom.kill|killed process', re.I), 'OOM Kill',         '#dc3545'),
    (re.compile(r'stack smashing', re.I),                        'Stack Smash',      '#6f42c1'),
    (re.compile(r'Bus error', re.I),                             'Bus Error',        '#6f42c1'),
    (re.compile(r'segfault', re.I),                              'Segfault',         '#b02a37'),
]
_MEM_PEAK_RE = re.compile(r'(\d+[\.,]?\d*\s*[KMG]?\s*memory peak)', re.I)


def _classify_crash(journal_lines):
    """Return {'label': str, 'color': str, 'detail': str} from journal lines."""
    detail = ''
    for line in journal_lines:
        m = _MEM_PEAK_RE.search(line)
        if m:
            detail = m.group(1).strip()
        for pat, lbl, clr in _CRASH_PATTERNS:
            if pat.search(line):
                return {'label': lbl, 'color': clr, 'detail': detail}
    return {'label': '', 'color': '', 'detail': detail}


@app.route('/')
def index():
    """Dashboard: recent coredumps + summary stats."""
    try:
        # Summary counts
        total_cores = db.session.execute(text("SELECT COUNT(*) FROM cla_core")).scalar()
        total_devices = db.session.execute(text("SELECT COUNT(*) FROM cla_devices")).scalar()
        total_revisions = db.session.execute(text("SELECT COUNT(DISTINCT clb_rev) FROM cla_sw_rev")).scalar()

        # Find the newest SW revision (highest clb_id)
        newest_rev = db.session.execute(text(
            "SELECT clb_rev FROM cla_sw_rev ORDER BY clb_id DESC LIMIT 1"
        )).scalar()

        # Top crashing binaries (all revisions) with latest core id for journal
        top_binaries_raw = db.session.execute(text(
            "SELECT c.clc_core_binary, COUNT(*) as cnt, MAX(c.clc_id) as latest_id "
            "FROM cla_core c "
            "GROUP BY c.clc_core_binary ORDER BY cnt DESC LIMIT 10"
        )).fetchall()

        # Batch fetch journal for latest core of each binary
        latest_ids = [r[2] for r in top_binaries_raw if r[2]]
        journal_by_core = {}
        if latest_ids:
            placeholders = ','.join(str(int(i)) for i in latest_ids)
            jn_rows = db.session.execute(text(
                f"SELECT cld_core, cld_line FROM cla_journal "
                f"WHERE cld_core IN ({placeholders}) ORDER BY cld_core, cld_line_no"
            )).fetchall()
            for jrow in jn_rows:
                journal_by_core.setdefault(jrow[0], []).append(jrow[1])

        # Binaries with same bt_csum seen on >1 device (systematic bugs)
        systematic_rows = db.session.execute(text(
            "SELECT DISTINCT clc_core_binary FROM cla_core "
            "WHERE clc_bt_csum IS NOT NULL "
            "GROUP BY clc_core_binary, clc_bt_csum "
            "HAVING COUNT(DISTINCT clc_device) > 1"
        )).fetchall()
        systematic_set = {r[0] for r in systematic_rows}

        top_binaries = []
        for r in top_binaries_raw:
            jlines = journal_by_core.get(r[2], [])
            top_binaries.append({
                'binary': r[0],
                'cnt': r[1],
                'cause': _classify_crash(jlines),
                'systematic': r[0] in systematic_set,
            })

        # Recent coredumps
        recent = db.session.execute(text(
            "SELECT c.clc_id, c.clc_core_name, c.clc_core_binary, c.clc_core_signal, "
            "c.clc_date, d.cla_eqm_name, d.cla_ip_addr, s.clb_rev, c.clc_bt_csum "
            "FROM cla_core c "
            "LEFT JOIN cla_devices d ON c.clc_device = d.cla_id "
            "LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
            "ORDER BY c.clc_id DESC LIMIT 20"
        )).fetchall()

        # Crashes per device (all revisions)
        per_device = db.session.execute(text(
            "SELECT d.cla_eqm_name, d.cla_id, COUNT(*) as cnt, d.cla_ip_addr FROM cla_core c "
            "JOIN cla_devices d ON c.clc_device = d.cla_id "
            "GROUP BY d.cla_id, d.cla_eqm_name, d.cla_ip_addr ORDER BY cnt DESC"
        )).fetchall()

    except Exception as e:
        app.logger.exception('Error in index()')
        return render_template('error.html', error='Failed to load dashboard. Check server logs.')

    return render_template('dashboard.html',
        total_cores=total_cores, total_devices=total_devices,
        total_revisions=total_revisions, top_binaries=top_binaries,
        recent=recent, per_device=per_device, newest_rev=newest_rev,
        tickets=_fetch_tickets())


@app.route('/cores')
def cores():
    """Paginated coredump list with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 500)
    offset = (page - 1) * per_page

    # Filters
    device_id = request.args.get('device', '', type=str)
    sw_rev = request.args.get('sw_rev', '', type=str)
    binary = request.args.get('binary', '', type=str)
    signal = request.args.get('signal', '', type=str)
    process = request.args.get('process', '', type=str)
    bt_csum = request.args.get('bt_csum', '', type=str)
    bt_sig = request.args.get('bt_sig', '', type=str)

    try:
        where = []
        params = {"limit": per_page, "offset": offset}

        if device_id:
            where.append("c.clc_device = :device_id")
            params["device_id"] = int(device_id)
        if sw_rev:
            where.append("s.clb_rev = :sw_rev")
            params["sw_rev"] = sw_rev
        if binary:
            where.append("c.clc_core_binary = :binary")
            params["binary"] = binary
        if signal:
            where.append("c.clc_core_signal = :signal")
            params["signal"] = int(signal)
        if process:
            where.append("c.clc_core_name = :process")
            params["process"] = process
        if bt_csum:
            where.append("c.clc_bt_csum = :bt_csum")
            params["bt_csum"] = bt_csum

        # Resolve bt_sig to matching bt_csum values
        if bt_sig and sw_rev:
            sig_groups = db.session.execute(text(
                "SELECT c.clc_bt_csum, MIN(c.clc_id) as sample_id "
                "FROM cla_core c "
                "LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
                "WHERE s.clb_rev = :sw_rev AND c.clc_bt_csum IS NOT NULL "
                "GROUP BY c.clc_bt_csum"
            ), {"sw_rev": sw_rev}).fetchall()

            sample_ids = [g[1] for g in sig_groups]
            raw_bt = {}
            if sample_ids:
                placeholders = ",".join(str(int(sid)) for sid in sample_ids)
                bt_rows = db.session.execute(text(
                    f"SELECT cle_core, cle_line_no, cle_line FROM cla_backtrace "
                    f"WHERE cle_core IN ({placeholders}) ORDER BY cle_core, cle_line_no"
                )).fetchall()
                for row in bt_rows:
                    if row[0] not in raw_bt:
                        raw_bt[row[0]] = []
                    raw_bt[row[0]].append(row[2])

            matching_csums = []
            for csum, sample_id in sig_groups:
                bt_lines = raw_bt.get(sample_id, [])
                sig = _bt_signature(bt_lines) if bt_lines else (csum or 'no-bt')
                if sig == bt_sig:
                    matching_csums.append(csum)

            if matching_csums:
                csum_placeholders = ",".join(f":sig_csum_{i}" for i in range(len(matching_csums)))
                where.append(f"c.clc_bt_csum IN ({csum_placeholders})")
                for i, cs in enumerate(matching_csums):
                    params[f"sig_csum_{i}"] = cs
            else:
                # No matches found — return empty result
                where.append("1 = 0")

        where_clause = ("WHERE " + " AND ".join(where)) if where else ""

        count_sql = (
            f"SELECT COUNT(*) FROM cla_core c "
            f"LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
            f"{where_clause}"
        )
        total_rows = db.session.execute(text(count_sql), params).scalar()

        rows_sql = (
            f"SELECT c.clc_id, c.clc_core_name, c.clc_core_binary, c.clc_core_signal, "
            f"c.clc_date, c.clc_bt_csum, d.cla_eqm_name, d.cla_ip_addr, s.clb_rev "
            f"FROM cla_core c "
            f"LEFT JOIN cla_devices d ON c.clc_device = d.cla_id "
            f"LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
            f"{where_clause} "
            f"ORDER BY c.clc_id DESC LIMIT :limit OFFSET :offset"
        )
        rows = db.session.execute(text(rows_sql), params).fetchall()

        total_pages = max(1, (total_rows + per_page - 1) // per_page)

        # For filter dropdowns
        devices = db.session.execute(text(
            "SELECT cla_id, cla_eqm_name, cla_ip_addr FROM cla_devices ORDER BY cla_eqm_name"
        )).fetchall()
        sw_revs = db.session.execute(text(
            "SELECT DISTINCT clb_rev FROM cla_sw_rev ORDER BY clb_id DESC"
        )).fetchall()
        signals = db.session.execute(text(
            "SELECT DISTINCT clc_core_signal FROM cla_core WHERE clc_core_signal IS NOT NULL ORDER BY clc_core_signal"
        )).fetchall()
        binaries = db.session.execute(text(
            "SELECT DISTINCT clc_core_binary FROM cla_core WHERE clc_core_binary IS NOT NULL ORDER BY clc_core_binary"
        )).fetchall()

    except Exception as e:
        app.logger.exception('Error in cores()')
        return render_template('error.html', error='Failed to load coredumps. Check server logs.')

    return render_template('cores.html',
        rows=rows, page=page, per_page=per_page,
        total_rows=total_rows, total_pages=total_pages,
        devices=devices, sw_revs=sw_revs, signals=signals, binaries=binaries,
        f_device=device_id, f_sw_rev=sw_rev, f_binary=binary, f_signal=signal,
        f_process=process, f_bt_csum=bt_csum, f_bt_sig=bt_sig,
        tickets=_fetch_tickets())


COREDUMPS_DIR = app.config['COREDUMP_DIR']

@app.route('/coredumps/<path:filepath>')
def download_coredump(filepath):
    """Serve coredump files from the coredumps directory."""
    # Use normpath (not realpath) so symlinks inside the directory are followed,
    # not resolved away — realpath would break files that are symlinks to another partition.
    norm = os.path.normpath(filepath)
    if norm.startswith('..') or os.path.isabs(norm):
        abort(403)
    full_path = os.path.join(COREDUMPS_DIR, norm)
    if not os.path.isfile(full_path):
        abort(404)
    return send_file(full_path, as_attachment=True)

@app.route('/core/<int:core_id>')
def core_detail(core_id):
    """Show coredump detail with backtrace and journal."""
    try:
        core = db.session.execute(text(
            "SELECT c.*, d.cla_eqm_name, d.cla_ip_addr, d.cla_eqm_label, s.clb_rev "
            "FROM cla_core c "
            "LEFT JOIN cla_devices d ON c.clc_device = d.cla_id "
            "LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
            "WHERE c.clc_id = :id"
        ), {"id": core_id}).fetchone()

        if not core:
            return render_template('error.html', error=f"Core dump #{core_id} not found")

        backtrace = db.session.execute(text(
            "SELECT cle_line_no, cle_line FROM cla_backtrace "
            "WHERE cle_core = :id ORDER BY cle_line_no"
        ), {"id": core_id}).fetchall()

        journal = db.session.execute(text(
            "SELECT cld_line_no, cld_line, cld_date FROM cla_journal "
            "WHERE cld_core = :id ORDER BY cld_line_no"
        ), {"id": core_id}).fetchall()

        # Find other cores with same crash signature (name + binary + signal + bt_csum)
        related = []
        related_total = 0
        if core.clc_bt_csum:
            related = db.session.execute(text(
                "SELECT c.clc_id, c.clc_core_name, c.clc_date, d.cla_eqm_name, s.clb_rev "
                "FROM cla_core c "
                "LEFT JOIN cla_devices d ON c.clc_device = d.cla_id "
                "LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
                "WHERE c.clc_core_name = :name AND c.clc_core_binary = :binary "
                "AND c.clc_core_signal = :signal AND c.clc_bt_csum = :csum AND c.clc_id != :id "
                "ORDER BY c.clc_id DESC LIMIT 20"
            ), {"name": core.clc_core_name, "binary": core.clc_core_binary,
                "signal": core.clc_core_signal, "csum": core.clc_bt_csum, "id": core_id}).fetchall()

            # Get total count for this crash signature
            related_total = db.session.execute(text(
                "SELECT COUNT(*) FROM cla_core c "
                "WHERE c.clc_core_name = :name AND c.clc_core_binary = :binary "
                "AND c.clc_core_signal = :signal AND c.clc_bt_csum = :csum AND c.clc_id != :id"
            ), {"name": core.clc_core_name, "binary": core.clc_core_binary,
                "signal": core.clc_core_signal, "csum": core.clc_bt_csum, "id": core_id}).scalar()

    except Exception as e:
        app.logger.exception('Error in core_detail(core_id=%s)', core_id)
        return render_template('error.html', error='Failed to load core detail. Check server logs.')
    bt_lines_plain = [row[1] for row in backtrace]
    no_sdk = len(bt_lines_plain) == 1 and bt_lines_plain[0].startswith('[No backtrace:')
    sdk_pending = len(bt_lines_plain) == 1 and bt_lines_plain[0].startswith('[Pending:')
    sdk_ver = None
    if core.clb_rev:
        m = re.search(r'(\d+\.\d+\.\d+)', core.clb_rev)
        if m:
            sdk_ver = 'v' + m.group(1)
    # Check if SDK install is actively in progress (lock file present)
    _sdk_lock = sdk_ver and os.path.exists(os.path.join(_SDK_DIR, sdk_ver, '.installing'))
    if _SDK_SYSROOT_SUBPATH:
        _sdk_installed_path = os.path.join(_SDK_DIR, sdk_ver, _SDK_SYSROOT_SUBPATH)
    else:
        _sdk_installed_path = os.path.join(_SDK_DIR, sdk_ver)
    sdk_ready = (
        sdk_pending and sdk_ver is not None and not _sdk_lock and
        os.path.isdir(_sdk_installed_path)
    )
    sdk_installing = bool(sdk_pending and sdk_ver is not None and _sdk_lock)

    sdk_download_url = None
    if core.clb_rev and sdk_ver and _SDK_BASE_URL and _SDK_PACKAGE_NAME:
        sdk_download_url = f'{_SDK_BASE_URL}/{_SDK_PACKAGE_NAME}-{sdk_ver}.tar.gz'

    ticket = _fetch_tickets().get(core.clc_bt_csum)
    # Plain-text backtrace for GitHub issue body — truncated to first 10 frames
    gh_bt_plain = ''.join(row[1] + '\n' for row in backtrace[:10])
    if len(backtrace) > 10:
        gh_bt_plain += f'... ({len(backtrace) - 10} more frames truncated)\n'
    return render_template('core_detail.html',
        core=core, backtrace=backtrace, journal=journal, related=related,
        related_total=related_total, no_sdk=no_sdk, sdk_pending=sdk_pending,
        sdk_ready=sdk_ready, sdk_installing=sdk_installing, sdk_ver=sdk_ver,
        sdk_download_url=sdk_download_url, ticket=ticket,
        gh_bt_plain=gh_bt_plain)

@app.route('/core/<int:core_id>/reprocess', methods=['POST'])
def core_reprocess(core_id):
    """Trigger on-demand backtrace generation via CCS API."""
    ccs_url = os.environ.get('CCS_API_URL', 'http://ccs:5556')
    try:
        req = urllib.request.Request(
            f'{ccs_url}/reprocess?core_id={core_id}',
            data=b'',
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return jsonify(_json.loads(resp.read()))
    except urllib.error.HTTPError as e:
        try:
            data = _json.loads(e.read())
        except Exception:
            data = {'error': f'CCS returned HTTP {e.code}'}
        return jsonify(data), e.code
    except Exception as e:
        return jsonify({'error': str(e)}), 502

@app.route('/core/<int:core_id>/install_sdk', methods=['POST'])
def core_install_sdk(core_id):
    """Trigger SDK install for this core's version, deduplicating concurrent requests."""
    try:
        row = db.session.execute(text(
            "SELECT r.clb_rev FROM cla_core c JOIN cla_sw_rev r ON c.clc_sw_rev=r.clb_id WHERE c.clc_id=:id"
        ), {'id': core_id}).fetchone()
    except Exception:
        return jsonify({'error': 'Database error'}), 500
    if not row:
        return jsonify({'error': 'Core not found'}), 404
    m = re.search(r'(\d+\.\d+\.\d+)', row[0])
    if not m:
        return jsonify({'error': 'Cannot determine SDK version from SW revision'}), 409
    sdk_ver = 'v' + m.group(1)
    available = _fetch_artifactory_versions()
    avail = next((s for s in available if s['version'] == sdk_ver), None)
    if not avail:
        return jsonify({'error': f'SDK {sdk_ver} not found in Artifactory'}), 404
    return _start_sdk_install(sdk_ver, avail['art_version'])

@app.route('/devices')
def devices():
    """List all devices with crash counts."""
    try:
        rows = db.session.execute(text(
            "SELECT d.*, COUNT(c.clc_id) as crash_count, MAX(c.clc_date) as last_crash "
            "FROM cla_devices d "
            "LEFT JOIN cla_core c ON d.cla_id = c.clc_device "
            "GROUP BY d.cla_id ORDER BY crash_count DESC"
        )).fetchall()
    except Exception as e:
        app.logger.exception('Error in devices()')
        return render_template('error.html', error='Failed to load devices. Check server logs.')
    return render_template('devices.html', devices=rows)


@app.route('/device/<int:device_id>')
def device_detail(device_id):
    """Show device info and its coredumps."""
    try:
        device = db.session.execute(text(
            "SELECT * FROM cla_devices WHERE cla_id = :id"
        ), {"id": device_id}).fetchone()
        if not device:
            return render_template('error.html', error=f"Device #{device_id} not found")
    except Exception as e:
        app.logger.exception('Error in device_detail(device_id=%s)', device_id)
        return render_template('error.html', error='Failed to load device detail. Check server logs.')
    return render_template('device_detail.html', device=device)


@app.route('/revisions')
def revisions():
    """List SW revisions with crash counts."""
    try:
        rows = db.session.execute(text(
            "SELECT s.clb_id, s.clb_rev, s.clb_type, COUNT(c.clc_id) as crash_count "
            "FROM cla_sw_rev s "
            "LEFT JOIN cla_core c ON s.clb_id = c.clc_sw_rev "
            "GROUP BY s.clb_id ORDER BY s.clb_id DESC"
        )).fetchall()
    except Exception as e:
        app.logger.exception('Error in revisions()')
        return render_template('error.html', error='Failed to load revisions. Check server logs.')
    installed_vers = {s['version'] for s in _installed_sdks() if s['installed']}
    revisions_data = []
    for r in rows:
        m = re.search(r'(\d+\.\d+\.\d+)', r[1] or '')
        sdk_ver = ('v' + m.group(1)) if m else None
        sdk_installed = (sdk_ver in installed_vers) if sdk_ver else None
        revisions_data.append((r[0], r[1], r[2], r[3], sdk_ver, sdk_installed))
    return render_template('revisions.html', revisions=revisions_data)



from bt_utils import (
    _normalize_bt_line,
    _is_abort_frame,
    _strip_leading_abort_frames,
    _bt_signature,
    _ABORT_FRAME_RE,
)


def _extract_common_library(bt_lines):
    """Extract the primary library name from backtrace for display."""
    for line in bt_lines:
        match = re.search(r'(lib[a-zA-Z0-9_+-]+\.so[.0-9]*)', line)
        if match:
            return match.group(1)
    return None


@app.route('/analyze')
def analyze():
    """Analyze crashes for a revision: group by process or call stack similarity."""
    rev = request.args.get('rev', '', type=str)
    group_mode = request.args.get('mode', 'service', type=str)  # 'service' or 'stack'

    try:
        # All revisions for dropdown
        sw_revs = db.session.execute(text(
            "SELECT DISTINCT clb_rev FROM cla_sw_rev ORDER BY clb_id DESC"
        )).fetchall()

        # Don't auto-select revision - wait for user to click Analyze

        processes = {}
        total_crashes = 0
        bt_snippets = {}
        bt_frame_counts = {}
        unique_type_count = 0

        if rev:
            # Step 1: Get all bt_csum groups with counts and a sample core
            raw_groups = db.session.execute(text(
                "SELECT c.clc_core_name, c.clc_core_binary, c.clc_core_signal, "
                "c.clc_bt_csum, COUNT(*) as cnt, MIN(c.clc_id) as sample_id, "
                "MIN(c.clc_date) as first_seen, MAX(c.clc_date) as last_seen, "
                "COUNT(DISTINCT c.clc_device) as dev_cnt "
                "FROM cla_core c "
                "LEFT JOIN cla_sw_rev s ON c.clc_sw_rev = s.clb_id "
                "WHERE s.clb_rev = :rev "
                "GROUP BY c.clc_core_name, c.clc_core_binary, c.clc_core_signal, c.clc_bt_csum "
                "ORDER BY c.clc_core_name, cnt DESC"
            ), {"rev": rev}).fetchall()

            # Step 2: Fetch backtraces for all sample cores
            sample_ids = [g[5] for g in raw_groups]
            raw_bt = {}
            if sample_ids:
                placeholders = ",".join(str(int(sid)) for sid in sample_ids)
                bt_rows = db.session.execute(text(
                    f"SELECT cle_core, cle_line_no, cle_line FROM cla_backtrace "
                    f"WHERE cle_core IN ({placeholders}) "
                    f"ORDER BY cle_core, cle_line_no"
                )).fetchall()
                for row in bt_rows:
                    if row[0] not in raw_bt:
                        raw_bt[row[0]] = []
                    raw_bt[row[0]].append(row[2])

            # Step 3: Compute normalized signature per bt_csum group, then merge
            # Key: (process, signal, normalized_hash) -> merged group
            # SIGXCPU is emitted by the watchdog; call stacks captured then
            # reflect wherever the process happened to be, not the fault
            # location. Collapse all SIGXCPU crashes per service into one
            # bucket instead of pretending backtrace similarity means anything.
            merged = {}
            for g in raw_groups:
                proc, binary, signal, bt_csum, cnt, sample_id, first_seen, last_seen, dev_cnt = g
                proc = proc or 'unknown'
                is_watchdog = (signal == SIGXCPU)

                if is_watchdog:
                    sig = 'watchdog'
                    merge_key = (proc, signal, sig)
                else:
                    bt_lines = raw_bt.get(sample_id, [])
                    sig = _bt_signature(bt_lines) if bt_lines else (bt_csum or 'no-bt')
                    merge_key = (proc, binary, signal, sig)

                if merge_key not in merged:
                    merged[merge_key] = {
                        "proc": proc, "binary": binary, "signal": signal,
                        "cnt": 0, "sample_id": sample_id,
                        "first_seen": first_seen, "last_seen": last_seen,
                        "sig": sig, "bt_csums": [],
                        "is_watchdog": is_watchdog,
                        "is_systematic": False,
                    }
                m = merged[merge_key]
                m["cnt"] += cnt
                m["bt_csums"].append(bt_csum)
                if dev_cnt > 1:
                    m["is_systematic"] = True
                if first_seen and (not m["first_seen"] or first_seen < m["first_seen"]):
                    m["first_seen"] = first_seen
                if last_seen and (not m["last_seen"] or last_seen > m["last_seen"]):
                    m["last_seen"] = last_seen

            # Batch fetch journal for sample cores + compute cause per group
            all_sample_ids_merged = list({mg["sample_id"] for mg in merged.values()})
            raw_journal = {}
            if all_sample_ids_merged:
                j_ph = ",".join(str(int(sid)) for sid in all_sample_ids_merged)
                jn_rows = db.session.execute(text(
                    f"SELECT cld_core, cld_line FROM cla_journal "
                    f"WHERE cld_core IN ({j_ph}) ORDER BY cld_core, cld_line_no"
                )).fetchall()
                for jrow in jn_rows:
                    raw_journal.setdefault(jrow[0], []).append(jrow[1])
            for mg in merged.values():
                mg["cause"] = _classify_crash(raw_journal.get(mg["sample_id"], []))

            # Step 4: Group by mode
            if group_mode == 'stack':
                # Re-group by signature only (ignore process) for cross-process view
                similarity_groups = {}

                for g in raw_groups:
                    proc, binary, signal, bt_csum, cnt, sample_id, first_seen, last_seen, dev_cnt = g
                    bt_lines = raw_bt.get(sample_id, [])

                    # Use same signature method as service mode, but group across processes
                    sig = _bt_signature(bt_lines) if bt_lines else (bt_csum or 'no-bt')
                    group_key = (signal, sig)

                    if group_key not in similarity_groups:
                        similarity_groups[group_key] = {
                            "lib_sig": sig, "signal": signal, "cnt": 0,
                            "processes": set(), "binaries": set(),
                            "sample_id": sample_id, "first_seen": first_seen,
                            "last_seen": last_seen,
                            "common_library": _extract_common_library(bt_lines),
                            "bt_csums": set(),
                        }

                    sg = similarity_groups[group_key]
                    sg["cnt"] += cnt
                    sg["processes"].add(proc or 'unknown')
                    if bt_csum:
                        sg["bt_csums"].add(bt_csum)
                    if binary:
                        sg["binaries"].add(binary.split('/')[-1])
                    if first_seen and (not sg["first_seen"] or first_seen < sg["first_seen"]):
                        sg["first_seen"] = first_seen
                    if last_seen and (not sg["last_seen"] or last_seen > sg["last_seen"]):
                        sg["last_seen"] = last_seen

                # Convert sets to sorted lists, compute snippets
                for sg in similarity_groups.values():
                    sg["processes"] = sorted(sg["processes"])
                    sg["binaries"] = sorted(sg["binaries"])
                    sg["bt_csums"] = sorted(sg["bt_csums"])
                    bt_lines = raw_bt.get(sg["sample_id"], [])
                    bt_snippets[sg["sample_id"]] = bt_lines[:5]
                    total_frames = len([l for l in bt_lines if re.match(r'\s*#\d+', l)])
                    bt_frame_counts[sg["sample_id"]] = total_frames
                    total_crashes += sg["cnt"]

                sorted_similarity = sorted(
                    similarity_groups.values(),
                    key=lambda x: x["cnt"],
                    reverse=True
                )
                unique_type_count = len(similarity_groups)
                process_count = len(set(p for sg in similarity_groups.values() for p in sg["processes"]))

                return render_template('analyze.html',
                    rev=rev, sw_revs=sw_revs, processes=[],
                    similarity_groups=sorted_similarity, group_mode='stack',
                    total_crashes=total_crashes, unique_types=unique_type_count,
                    process_count=process_count, bt_snippets=bt_snippets,
                    bt_frame_counts=bt_frame_counts,
                    tickets=_fetch_tickets())

            # Default: organize by process (service mode)
            for m in merged.values():
                proc = m["proc"]
                total_crashes += m["cnt"]
                if proc not in processes:
                    processes[proc] = {"groups": [], "total": 0, "watchdog": 0}
                processes[proc]["groups"].append(m)
                processes[proc]["total"] += m["cnt"]
                if m["is_watchdog"]:
                    processes[proc]["watchdog"] += m["cnt"]
                # Watchdog groups have meaningless backtraces — skip snippet.
                if not m["is_watchdog"]:
                    bt_lines = raw_bt.get(m["sample_id"], [])
                    bt_snippets[m["sample_id"]] = bt_lines[:5]
                    total_frames = len([l for l in bt_lines if re.match(r'\s*#\d+', l)])
                    bt_frame_counts[m["sample_id"]] = total_frames

            # Sort groups within each process by count desc
            for proc_data in processes.values():
                proc_data["groups"].sort(key=lambda x: x["cnt"], reverse=True)

            unique_type_count = len(merged)

    except Exception as e:
        app.logger.exception('Error in analyze()')
        return render_template('error.html', error='Failed to load analysis. Check server logs.')

    sorted_processes = sorted(processes.items(), key=lambda x: x[1]["total"], reverse=True)
    return render_template('analyze.html',
        rev=rev, sw_revs=sw_revs, processes=sorted_processes,
        similarity_groups=[], group_mode='service',
        total_crashes=total_crashes, unique_types=unique_type_count,
        process_count=len(processes), bt_snippets=bt_snippets,
        bt_frame_counts=bt_frame_counts,
        tickets=_fetch_tickets())


# ── Ticket API ────────────────────────────────────────────────────────────────


def _fetch_tickets():
    """Return {bt_csum: {issue, note, created_at}} for all tickets."""
    try:
        rows = db.session.execute(text(
            "SELECT clt_bt_csum, clt_issue, clt_note, clt_created_at FROM cla_ticket"
        )).fetchall()
        return {r[0]: {'issue': r[1], 'note': r[2], 'created_at': str(r[3])} for r in rows}
    except Exception:
        return {}


def _github_url(issue):
    issue = (issue or '').strip()
    github_repo = app.config.get('GITHUB_REPO', '')
    if not github_repo or not re.match(r'^\d+$', issue):
        return None
    return f'https://github.com/{github_repo}/issues/{issue}'


app.jinja_env.globals['github_url'] = _github_url


@app.route('/ticket_api', methods=['POST'])
def ticket_api():
    action = request.form.get('action', '')
    bt_csum = request.form.get('bt_csum', '').strip()
    if not bt_csum or len(bt_csum) > 64:
        return jsonify({'error': 'Invalid bt_csum'}), 400

    if action == 'mark':
        issue = request.form.get('issue', '').strip()[:32]
        note = request.form.get('note', '').strip()[:255]
        if not issue:
            return jsonify({'error': 'issue is required'}), 400
        db.session.execute(text(
            "INSERT INTO cla_ticket (clt_bt_csum, clt_issue, clt_note) VALUES (:csum, :issue, :note) "
            "ON DUPLICATE KEY UPDATE clt_issue=:issue, clt_note=:note, clt_created_at=CURRENT_TIMESTAMP"
        ), {'csum': bt_csum, 'issue': issue, 'note': note})
        db.session.commit()
        url = _github_url(issue)
        return jsonify({'status': 'ok', 'issue': issue, 'note': note, 'url': url})

    if action == 'unmark':
        db.session.execute(text(
            "DELETE FROM cla_ticket WHERE clt_bt_csum = :csum"
        ), {'csum': bt_csum})
        db.session.commit()
        return jsonify({'status': 'ok'})

    return jsonify({'error': 'Unknown action'}), 400


# ── SDK Management API ────────────────────────────────────────────────────────
_SDK_DIR          = app.config['SDK_DIR']
_SDK_BASE_URL     = app.config['SDK_BASE_URL']
_SDK_PACKAGE_NAME = app.config['SDK_PACKAGE_NAME']
_SDK_SYSROOT_SUBPATH = app.config['SDK_SYSROOT_SUBPATH']


def _evict_sdks_for_space(needed_bytes: int, keep_version: str):
    evict_sdks_for_space(_SDK_DIR, needed_bytes, keep_version)


def _sdk_version_key(v):
    nums = re.findall(r'\d+', v)
    return tuple(int(n) for n in nums) + (0,) * 4


def _installed_sdks():
    result = []
    if not os.path.isdir(_SDK_DIR):
        return result
    for entry in os.scandir(_SDK_DIR):
        if not entry.is_dir() or not entry.name.startswith('v'):
            continue
        if _SDK_SYSROOT_SUBPATH:
            sysroot = os.path.join(entry.path, _SDK_SYSROOT_SUBPATH)
        else:
            sysroot = entry.path
        lock = os.path.join(entry.path, '.installing')
        pid_file = os.path.join(entry.path, '.installing.pid')
        # Auto-clean stale lock: sysroot present AND install process is dead
        if os.path.exists(lock) and os.path.isdir(sysroot):
            stale = True
            if os.path.isfile(pid_file):
                try:
                    with open(pid_file) as fh:
                        pid = int(fh.read().strip())
                    os.kill(pid, 0)
                    stale = False  # process still alive — install in progress
                except (ValueError, OSError):
                    pass
            if stale:
                try:
                    os.unlink(lock)
                    if os.path.isfile(pid_file):
                        os.unlink(pid_file)
                except OSError:
                    pass
        # Auto-clean stale lock: install process is dead and sysroot is absent
        if os.path.exists(lock) and not os.path.isdir(sysroot) and os.path.isfile(pid_file):
            try:
                with open(pid_file) as fh:
                    pid = int(fh.read().strip())
                os.kill(pid, 0)  # raises if process is gone
            except (ValueError, OSError):
                # Process is dead — stale lock
                try:
                    os.unlink(lock)
                    os.unlink(pid_file)
                except OSError:
                    pass
        is_installing = os.path.exists(lock)
        is_installed = os.path.isdir(sysroot) and not is_installing
        if not is_installed and not is_installing:
            continue
        result.append({
            'version': entry.name,
            'installed': is_installed,
            'installing': is_installing,
        })
    result.sort(key=lambda x: _sdk_version_key(x['version']), reverse=True)
    return result


def _fetch_artifactory_versions():
    user = os.environ.get('ARTIFACTORY_USER', '')
    password = os.environ.get('ARTIFACTORY_PASS', '')
    url = _ART_LIST_API + '?list&deep=0&listFolders=0'
    req = urllib.request.Request(url)
    if user and password:
        creds = base64.b64encode(f'{user}:{password}'.encode()).decode()
        req.add_header('Authorization', f'Basic {creds}')
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = _json.loads(resp.read())
    except Exception:
        return []
    versions = []
    for f in data.get('files', []):
        m = re.search(
            r'sdk-philips-imx8mp-delta-transport-(\d+\.\d+\.\d+)\+dev\.(\d+)\.tar\.gz$',
            f['uri'],
        )
        if m:
            versions.append({
                'version': 'v' + m.group(1),
                'run': int(m.group(2)),
                'art_version': m.group(1) + '+dev.' + m.group(2),
                'filename': f['uri'].split('/')[-1],
            })
    versions.sort(key=lambda x: (_sdk_version_key(x['version']), x['run']), reverse=True)
    return versions


def _start_sdk_install(version, art_version):
    """Start an SDK install subprocess. Deduplicates via lock file. Returns a jsonify response."""
    user = os.environ.get('ARTIFACTORY_USER', '')
    password = os.environ.get('ARTIFACTORY_PASS', '')
    if not user or not password:
        return jsonify({'error': 'No Artifactory credentials. Set ARTIFACTORY_USER and ARTIFACTORY_PASS environment variables.'}), 403
    sdk_vdir = os.path.join(_SDK_DIR, version)
    sysroot = os.path.join(sdk_vdir, _SYSROOT_SUBPATH)
    lock = os.path.join(sdk_vdir, '.installing')
    if os.path.isdir(sysroot) and not os.path.exists(lock):
        return jsonify({'status': 'already_installed', 'version': version})
    if os.path.exists(lock):
        return jsonify({'status': 'already_installing', 'version': version})
    os.makedirs(sdk_vdir, mode=0o755, exist_ok=True)
    log_path = os.path.join(sdk_vdir, '.install.log')
    install_script = os.path.join(sdk_vdir, '.run-install.sh')
    url = f'{_ART_BASE}/sdk-philips-imx8mp-delta-transport-{art_version}.tar.gz'
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('Authorization', 'Basic ' + base64.b64encode(f'{user}:{password}'.encode()).decode())
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_length = int(resp.headers.get('Content-Length', 0))
    except Exception:
        content_length = 0
    needed = max(content_length * 8, 30 * 1024 ** 3) if content_length else 30 * 1024 ** 3
    os.makedirs(_SDK_DIR, exist_ok=True)
    _evict_sdks_for_space(needed, version)
    sq = shlex.quote
    pid_file = os.path.join(sdk_vdir, '.installing.pid')
    script = (
        '#!/bin/bash\n'
        'set -euo pipefail\n'
        f"trap 'echo FAILED >> {sq(log_path)}; rm -f {sq(lock)} {sq(pid_file)} {sq(install_script)}' ERR\n"
        f'touch {sq(lock)}\n'
        f"echo 'Downloading {url} ...' > {sq(log_path)}\n"
        f'curl -fsSL --retry 3 --retry-delay 5 -u {sq(user + ":" + password)} {sq(url)} | tar xz -C {sq(sdk_vdir)}\n'
        f'SH_FILE=$(ls {sq(sdk_vdir)}/*.sh 2>/dev/null | head -1) || true\n'
        f'if [[ -n "$SH_FILE" ]]; then\n'
        f'  echo "Running SDK installer: $SH_FILE ..." >> {sq(log_path)}\n'
        f'  bash "$SH_FILE" -y -d {sq(sdk_vdir)} >> {sq(log_path)} 2>&1\n'
        f'  rm -f "$SH_FILE"\n'
        f'fi\n'
        f'chmod -R a+rX {sq(sdk_vdir)}\n'
        f"echo 'Done.' >> {sq(log_path)}\n"
        f'rm -f {sq(lock)} {sq(pid_file)} {sq(install_script)}\n'
    )
    with open(install_script, 'w') as fh:
        fh.write(script)
    os.chmod(install_script, 0o755)
    proc = subprocess.Popen(
        ['bash', install_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    with open(pid_file, 'w') as fh:
        fh.write(str(proc.pid))
    return jsonify({'status': 'started', 'version': version})


@app.route('/sdk_api', methods=['GET', 'POST'])
def sdk_api():
    action = request.args.get('action')
    if action is None:
        action = request.form.get('action', 'status')

    if action == 'status' and request.method == 'GET':
        installed = _installed_sdks()
        available = _fetch_artifactory_versions()
        installed_vers = {s['version'] for s in installed if s['installed']}
        for av in available:
            sysroot = os.path.join(_SDK_DIR, av['version'], _SYSROOT_SUBPATH)
            av['installed'] = av['version'] in installed_vers
            av['ready'] = os.path.isdir(sysroot)
            av['installing'] = os.path.exists(os.path.join(_SDK_DIR, av['version'], '.installing'))
        return jsonify({
            'installed': installed,
            'available': available,
            'has_credentials': bool(os.environ.get('ARTIFACTORY_USER')),
            'sdk_dir': _SDK_DIR,
        })

    if action == 'log' and request.method == 'GET':
        ver = re.sub(r'[^0-9a-zA-Z._+]', '', request.args.get('version', ''))
        log_path = os.path.join(_SDK_DIR, ver, '.install.log')
        content = ''
        if ver and os.path.isfile(log_path):
            try:
                with open(log_path) as fh:
                    content = fh.read()
            except OSError:
                pass
        return jsonify({'log': content})

    if action == 'autolog' and request.method == 'GET':
        log_path = os.path.join(_SDK_DIR, '.auto-install.log')
        content = ''
        if os.path.isfile(log_path):
            try:
                with open(log_path) as fh:
                    lines = fh.readlines()
                content = ''.join(lines[-30:])
            except OSError:
                pass
        # Append the latest SDK version's .install.log so the UI shows
        # detailed steps (Downloading, Extracting, Done.) alongside meta lines.
        try:
            sdk_dirs = [d for d in os.listdir(_SDK_DIR)
                        if os.path.isdir(os.path.join(_SDK_DIR, d)) and d.startswith('v')]
            if sdk_dirs:
                sdk_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(_SDK_DIR, d)), reverse=True)
                latest_install_log = os.path.join(_SDK_DIR, sdk_dirs[0], '.install.log')
                if os.path.isfile(latest_install_log):
                    with open(latest_install_log) as fh:
                        install_content = fh.read()
                    if install_content.strip():
                        content = content.rstrip('\n') + '\n--- install log (' + sdk_dirs[0] + ') ---\n' + install_content
        except OSError:
            pass
        return jsonify({'log': content})

    if action == 'install' and request.method == 'POST':
        version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('version', ''))
        art_version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('art_version', ''))
        if not version or not art_version:
            return jsonify({'error': 'Missing version or art_version'}), 400
        return _start_sdk_install(version, art_version)

    if action == 'cancel' and request.method == 'POST':
        version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('version', ''))
        if not version:
            return jsonify({'error': 'Missing version'}), 400
        sdk_vdir = os.path.join(_SDK_DIR, version)
        pid_file = os.path.join(sdk_vdir, '.installing.pid')
        killed = False
        if os.path.isfile(pid_file):
            try:
                with open(pid_file) as fh:
                    pid = int(fh.read().strip())
                os.killpg(pid, signal.SIGKILL)
                killed = True
            except (ValueError, ProcessLookupError, PermissionError, OSError):
                pass
        subprocess.run(['rm', '-rf', sdk_vdir], check=False)
        return jsonify({'status': 'cancelled', 'killed': killed})

    return jsonify({'error': 'Unknown action or method'}), 400


if __name__ == '__main__':
    app.run(port=8080)
