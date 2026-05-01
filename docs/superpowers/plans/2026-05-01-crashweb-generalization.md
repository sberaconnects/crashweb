# crashweb Generalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy `synergy-coredump-web` from `/home/sbera/git/work/synergy-coredump-web` into `/home/sbera/git/personal/crashweb`, strip all Philips/Synergy company coupling, and push as a public repo to `github.com/sbera.connects/crashweb`.

**Architecture:** Config-driven generalization — all company-specific values moved to env vars read through `web/config.py`. No structural changes to Flask app, DB schema, or Docker service topology.

**Tech Stack:** Python 3 / Flask, MariaDB 10.6, Traefik 3.6.7, Docker Compose, GitHub Actions

---

## File Map

| File | Action | Change summary |
|------|--------|----------------|
| `web/config.py` | Modify | Add SDK_BASE_URL, SDK_PACKAGE_NAME, SDK_SYSROOT_SUBPATH, GITHUB_REPO, COREDUMP_DIR; make SECRET_KEY required |
| `web/app.py` | Modify | Replace hardcoded Artifactory/GitHub/Philips constants; rewrite SDK install logic |
| `web/templates/core_detail.html` | Modify | Conditional GitHub issue link; rename `art_sdk_url` → `sdk_download_url` |
| `web/tests/test_app.py` | Modify | Set SECRET_KEY + GITHUB_REPO env vars; update hardcoded URL assertions |
| `web/sdk_space.py` | Copy as-is | No Philips refs |
| `traefik/traefik_dynamic-dev.yml` | Modify | Strip LDAP plugin, embedded CA cert, IP whitelist |
| `traefik/traefik_dynamic-prod.yml` | Modify | Strip LDAP, IP whitelist, replace domain + cert paths |
| `traefik/traefik_dynamic-staging.yml` | Modify | Strip LDAP, all Synergy/Philips domain refs |
| `docker-compose.yml` | Modify | Remove LDAP plugin + env vars; add SECRET_KEY, GITHUB_REPO, SDK_* env vars |
| `docker-compose-local.yml` | Copy as-is | No Philips refs (uses ./data/ paths) |
| `docker-compose-dev.yml` | Modify | Remove LDAP plugin + auth-users mount |
| `docker-compose-production.yml` | Modify | Remove LDAP plugin; rename SSL secret to generic name |
| `docker/flask-web/auto-install-sdk.sh` | Modify | Replace Artifactory listing API with generic SDK_BASE_URL/SDK_PACKAGE_NAME/SDK_VERSION pattern |
| `README.md` | Rewrite | Generic setup guide; remove all Philips/Synergy refs |
| `CONTRIBUTING.md` | Modify | Remove "Philips" and "innersource" references |
| `.github/workflows/deploy-production.yml` | Modify | Replace self-hosted runner with ubuntu-latest; remove Artifactory/LDAP secrets |
| `.env.example` | Create | Documented env var template |
| `catalog-info.yaml` | Delete | Philips Backstage — not copied |
| `.github/philips-repo.yaml` | Delete | Philips internal — not copied |
| `mkdocs.yaml` | Delete | Philips portal — not copied |
| `docs/index.md` | Delete | Philips portal — not copied |
| `traefik/auth-users-dev` | Delete | LDAP auth file — not copied |

---

## Task 1: Copy source files into crashweb

**Files:**
- Create: `/home/sbera/git/personal/crashweb/` (all source files from original)

- [ ] **Step 1: rsync all files, excluding deleted items**

```bash
rsync -a \
  --exclude='.git' \
  --exclude='catalog-info.yaml' \
  --exclude='.github/philips-repo.yaml' \
  --exclude='mkdocs.yaml' \
  --exclude='docs/index.md' \
  --exclude='traefik/auth-users-dev' \
  /home/sbera/git/work/synergy-coredump-web/ \
  /home/sbera/git/personal/crashweb/
```

- [ ] **Step 2: Initialize git repo**

```bash
cd /home/sbera/git/personal/crashweb
git init
git branch -m main
```

- [ ] **Step 3: Verify key files copied**

```bash
ls /home/sbera/git/personal/crashweb/web/app.py
ls /home/sbera/git/personal/crashweb/docker-compose.yml
ls /home/sbera/git/personal/crashweb/traefik/traefik_dynamic-prod.yml
# Verify deleted files are absent:
test ! -f /home/sbera/git/personal/crashweb/catalog-info.yaml && echo "OK: catalog-info.yaml absent"
test ! -f /home/sbera/git/personal/crashweb/traefik/auth-users-dev && echo "OK: auth-users-dev absent"
test ! -f /home/sbera/git/personal/crashweb/.github/philips-repo.yaml && echo "OK: philips-repo.yaml absent"
```

Expected: all three "OK" lines print.

- [ ] **Step 4: Stage and commit initial copy**

```bash
cd /home/sbera/git/personal/crashweb
git add .
git commit -m "chore: initial source copy — pre-generalization"
```

---

## Task 2: Rewrite web/config.py

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/web/config.py`
- Test: `/home/sbera/git/personal/crashweb/web/tests/test_app.py`

- [ ] **Step 1: Write failing test for SECRET_KEY validation**

Add this test class at the very end of `web/tests/test_app.py`, after all existing test classes:

```python
class TestConfigSecretKeyRequired(unittest.TestCase):
    def test_missing_secret_key_raises(self):
        """config.py must raise RuntimeError when SECRET_KEY env var is missing."""
        import importlib
        import config as cfg_module
        old_val = os.environ.pop('SECRET_KEY', None)
        try:
            importlib.reload(cfg_module)
            # If we reach here without error, the check is missing
            self.fail("Expected RuntimeError when SECRET_KEY is not set")
        except RuntimeError as e:
            assert 'SECRET_KEY' in str(e)
        finally:
            if old_val is not None:
                os.environ['SECRET_KEY'] = old_val
            else:
                os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
            importlib.reload(cfg_module)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py::TestConfigSecretKeyRequired -v 2>&1 | tail -20
```

Expected: FAIL — RuntimeError not raised because current config has a hardcoded default.

- [ ] **Step 3: Rewrite web/config.py**

```python
import os

DB_HOST     = os.environ.get('DB_HOST', 'mariadb')
DB_USER     = os.environ.get('DB_USER', 'apache')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME     = os.environ.get('DB_NAME', 'coredumps')
DB_PORT     = os.environ.get('DB_PORT', '3306')

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is required. "
        "Set it to a long random string before starting the app."
    )

COREDUMP_DIR     = os.environ.get('COREDUMP_DIR', '/var/www/html/coredumps')
SDK_DIR          = os.environ.get('SDK_DIR', '/var/www/sdks')
SDK_BASE_URL     = os.environ.get('SDK_BASE_URL', '').rstrip('/')
SDK_PACKAGE_NAME = os.environ.get('SDK_PACKAGE_NAME', '')
SDK_SYSROOT_SUBPATH = os.environ.get('SDK_SYSROOT_SUBPATH', '')

GITHUB_REPO = os.environ.get('GITHUB_REPO', '')
```

- [ ] **Step 4: Add SECRET_KEY and GITHUB_REPO to test env setup**

In `web/tests/test_app.py`, find the block of `os.environ.setdefault` calls (around line 23) and add two lines:

```python
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_NAME', 'test')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing')   # ADD THIS
os.environ.setdefault('GITHUB_REPO', 'test-owner/test-repo')          # ADD THIS
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py::TestConfigSecretKeyRequired -v 2>&1 | tail -20
```

Expected: PASS.

- [ ] **Step 6: Run full test suite to confirm no regressions**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py -v 2>&1 | tail -30
```

Expected: all existing tests pass (except `TestGithubUrl` — will fail, fixed in Task 4).

- [ ] **Step 7: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/config.py web/tests/test_app.py
git commit -m "feat: require SECRET_KEY env var; add SDK and GitHub config to config.py"
```

---

## Task 3: Update web/app.py — module-level constants

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/web/app.py`

Replace all hardcoded company constants with config-driven values.

- [ ] **Step 1: Replace COREDUMPS_DIR (line 322)**

Find:
```python
COREDUMPS_DIR = '/var/www/html/coredumps'
```

Replace with:
```python
COREDUMPS_DIR = app.config['COREDUMP_DIR']
```

- [ ] **Step 2: Replace _GITHUB_ISSUE_BASE and SDK constants (lines 743, 799-802)**

Find:
```python
# ── Ticket API ────────────────────────────────────────────────────────────────
_GITHUB_ISSUE_BASE = 'https://github.com/philips-internal/synergy-base/issues'
```

Replace with:
```python
# ── Ticket API ────────────────────────────────────────────────────────────────
```

Find:
```python
# ── SDK Management API ────────────────────────────────────────────────────────
_SDK_DIR = os.environ.get('SDK_DIR', '/var/www/sdks')
_ART_BASE = 'https://artifactory-ehv.ta.philips.com/artifactory/synergy-generic-rnd/sdk/philips-imx8mp-delta-transport/release'
_ART_LIST_API = 'https://artifactory-ehv.ta.philips.com/artifactory/api/storage/synergy-generic-rnd/sdk/philips-imx8mp-delta-transport/release'
_SYSROOT_SUBPATH = 'sysroots/cortexa53-crypto-mgl-linux'
```

Replace with:
```python
# ── SDK Management API ────────────────────────────────────────────────────────
_SDK_DIR          = app.config['SDK_DIR']
_SDK_BASE_URL     = app.config['SDK_BASE_URL']
_SDK_PACKAGE_NAME = app.config['SDK_PACKAGE_NAME']
_SDK_SYSROOT_SUBPATH = app.config['SDK_SYSROOT_SUBPATH']
```

- [ ] **Step 3: Update _github_url() to use config instead of module constant**

Find:
```python
def _github_url(issue):
    """Return GitHub issue URL if issue is numeric, else return as-is."""
    issue = (issue or '').strip()
    if re.match(r'^\d+$', issue):
        return f'{_GITHUB_ISSUE_BASE}/{issue}'
    return None
```

Replace with:
```python
def _github_url(issue):
    issue = (issue or '').strip()
    github_repo = app.config.get('GITHUB_REPO', '')
    if not github_repo or not re.match(r'^\d+$', issue):
        return None
    return f'https://github.com/{github_repo}/issues/{issue}'
```

- [ ] **Step 4: Update _installed_sdks() to use _SDK_SYSROOT_SUBPATH (lines 814-865)**

Find inside `_installed_sdks()`:
```python
        sysroot = os.path.join(entry.path, _SYSROOT_SUBPATH)
```

Replace with:
```python
        if _SDK_SYSROOT_SUBPATH:
            sysroot = os.path.join(entry.path, _SDK_SYSROOT_SUBPATH)
        else:
            sysroot = entry.path
```

- [ ] **Step 5: Update art_sdk_url in core_detail route (lines 405-413)**

Find:
```python
    # SDK Artifactory URL for download
    art_sdk_url = None
    if core.clb_rev and sdk_ver:
        art_ver = re.sub(r'^v', '', core.clb_rev).replace('-', '+')
        art_sdk_url = (
            'https://artifactory-ehv.ta.philips.com/artifactory/synergy-generic-rnd'
            f'/sdk/philips-imx8mp-delta-transport/release'
            f'/sdk-philips-imx8mp-delta-transport-{art_ver}.tar.gz'
        )
```

Replace with:
```python
    sdk_download_url = None
    if core.clb_rev and sdk_ver and _SDK_BASE_URL and _SDK_PACKAGE_NAME:
        sdk_download_url = f'{_SDK_BASE_URL}/{_SDK_PACKAGE_NAME}-{sdk_ver}.tar.gz'
```

- [ ] **Step 6: Update render_template call in core_detail (line 420-424)**

Find:
```python
    return render_template('core_detail.html',
        core=core, backtrace=backtrace, journal=journal, related=related,
        related_total=related_total, no_sdk=no_sdk, sdk_pending=sdk_pending,
        sdk_ready=sdk_ready, sdk_installing=sdk_installing, sdk_ver=sdk_ver, art_sdk_url=art_sdk_url, ticket=ticket,
        gh_bt_plain=gh_bt_plain)
```

Replace with:
```python
    return render_template('core_detail.html',
        core=core, backtrace=backtrace, journal=journal, related=related,
        related_total=related_total, no_sdk=no_sdk, sdk_pending=sdk_pending,
        sdk_ready=sdk_ready, sdk_installing=sdk_installing, sdk_ver=sdk_ver,
        sdk_download_url=sdk_download_url, ticket=ticket,
        gh_bt_plain=gh_bt_plain)
```

- [ ] **Step 7: Update sdk_ready check to use _SDK_SYSROOT_SUBPATH (lines 397-403)**

Find:
```python
    _sdk_lock = sdk_ver and os.path.exists(os.path.join(_SDK_DIR, sdk_ver, '.installing'))
    # Only truly installed when sysroot exists AND lock is gone
    sdk_ready = (
        sdk_pending and sdk_ver is not None and not _sdk_lock and
        os.path.isdir(os.path.join(_SDK_DIR, sdk_ver, _SYSROOT_SUBPATH))
    )
```

Replace with:
```python
    _sdk_lock = sdk_ver and os.path.exists(os.path.join(_SDK_DIR, sdk_ver, '.installing'))
    if _SDK_SYSROOT_SUBPATH:
        _sdk_installed_path = os.path.join(_SDK_DIR, sdk_ver, _SDK_SYSROOT_SUBPATH)
    else:
        _sdk_installed_path = os.path.join(_SDK_DIR, sdk_ver)
    sdk_ready = (
        sdk_pending and sdk_ver is not None and not _sdk_lock and
        os.path.isdir(_sdk_installed_path)
    )
```

- [ ] **Step 8: Run tests to verify no regressions**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py -v 2>&1 | tail -30
```

Expected: `TestGithubUrl` tests still fail (wrong URL assertion — fixed in Task 4), all others pass.

- [ ] **Step 9: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/app.py
git commit -m "feat: replace hardcoded Philips/Artifactory constants with config-driven values"
```

---

## Task 4: Update web/app.py — SDK API (remove Artifactory)

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/web/app.py`

Remove `_fetch_artifactory_versions()` (Artifactory-specific listing API). Rewrite `_start_sdk_install()` for generic HTTP. Update `core_install_sdk` and `sdk_api` routes.

- [ ] **Step 1: Delete _fetch_artifactory_versions() entirely (lines 868-895)**

Remove the entire function:
```python
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
```

- [ ] **Step 2: Rewrite _start_sdk_install() — remove Artifactory auth, use SDK_BASE_URL**

Find (lines 898-955):
```python
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
```

Replace with:
```python
def _start_sdk_install(version):
    """Start an SDK install subprocess. Deduplicates via lock file. Returns a jsonify response."""
    if not _SDK_BASE_URL or not _SDK_PACKAGE_NAME:
        return jsonify({'error': 'SDK_BASE_URL and SDK_PACKAGE_NAME must be configured to install SDKs remotely'}), 503
    sdk_vdir = os.path.join(_SDK_DIR, version)
    if _SDK_SYSROOT_SUBPATH:
        sysroot = os.path.join(sdk_vdir, _SDK_SYSROOT_SUBPATH)
    else:
        sysroot = sdk_vdir
    lock = os.path.join(sdk_vdir, '.installing')
    if os.path.isdir(sysroot) and not os.path.exists(lock):
        return jsonify({'status': 'already_installed', 'version': version})
    if os.path.exists(lock):
        return jsonify({'status': 'already_installing', 'version': version})
    os.makedirs(sdk_vdir, mode=0o755, exist_ok=True)
    log_path = os.path.join(sdk_vdir, '.install.log')
    install_script = os.path.join(sdk_vdir, '.run-install.sh')
    url = f'{_SDK_BASE_URL}/{_SDK_PACKAGE_NAME}-{version}.tar.gz'
    try:
        req = urllib.request.Request(url, method='HEAD')
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
        f'curl -fsSL --retry 3 --retry-delay 5 {sq(url)} | tar xz -C {sq(sdk_vdir)}\n'
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
```

- [ ] **Step 3: Update core_install_sdk route (lines 447-466)**

Find:
```python
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
```

Replace with:
```python
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
    return _start_sdk_install(sdk_ver)
```

- [ ] **Step 4: Update sdk_api route status action (lines 958-978)**

Find:
```python
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
```

Replace with:
```python
    if action == 'status' and request.method == 'GET':
        installed = _installed_sdks()
        return jsonify({
            'installed': installed,
            'has_remote': bool(_SDK_BASE_URL),
            'sdk_dir': _SDK_DIR,
        })
```

- [ ] **Step 5: Update sdk_api install action (lines 1019-1024)**

Find:
```python
    if action == 'install' and request.method == 'POST':
        version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('version', ''))
        art_version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('art_version', ''))
        if not version or not art_version:
            return jsonify({'error': 'Missing version or art_version'}), 400
        return _start_sdk_install(version, art_version)
```

Replace with:
```python
    if action == 'install' and request.method == 'POST':
        version = re.sub(r'[^0-9a-zA-Z._+]', '', request.form.get('version', ''))
        if not version:
            return jsonify({'error': 'Missing version'}), 400
        return _start_sdk_install(version)
```

- [ ] **Step 6: Remove unused import (base64 — was only used for Artifactory auth)**

Check if `base64` is still used anywhere in app.py:

```bash
grep -n 'base64' /home/sbera/git/personal/crashweb/web/app.py
```

If the only remaining usage is `import base64` at the top, remove that import line.

- [ ] **Step 7: Run full test suite**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py -v 2>&1 | tail -30
```

Expected: all tests pass except `TestGithubUrl.test_numeric_issue_returns_url` and `test_whitespace_stripped` (hardcoded Philips URL — fixed in Task 5).

- [ ] **Step 8: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/app.py
git commit -m "feat: remove Artifactory SDK listing; generic SDK install via SDK_BASE_URL"
```

---

## Task 5: Fix tests and update core_detail.html

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/web/tests/test_app.py`
- Modify: `/home/sbera/git/personal/crashweb/web/templates/core_detail.html`

- [ ] **Step 1: Fix TestGithubUrl assertions to use GITHUB_REPO env var**

In `web/tests/test_app.py`, find `TestGithubUrl`:

```python
class TestGithubUrl(unittest.TestCase):
    def test_numeric_issue_returns_url(self):
        url = flask_app._github_url('15884')
        assert url == 'https://github.com/philips-internal/synergy-base/issues/15884'
```

Replace the assertion:
```python
    def test_numeric_issue_returns_url(self):
        url = flask_app._github_url('15884')
        assert url == 'https://github.com/test-owner/test-repo/issues/15884'
```

Also fix `test_whitespace_stripped`:
```python
    def test_whitespace_stripped(self):
        url = flask_app._github_url('  42  ')
        assert url == 'https://github.com/test-owner/test-repo/issues/42'
```

Add new test for when GITHUB_REPO is not set:
```python
    def test_no_github_repo_returns_none(self):
        """When GITHUB_REPO is not configured, _github_url always returns None."""
        with flask_app.app.test_request_context():
            flask_app.app.config['GITHUB_REPO'] = ''
            result = flask_app._github_url('123')
            flask_app.app.config['GITHUB_REPO'] = 'test-owner/test-repo'
        assert result is None
```

- [ ] **Step 2: Run TestGithubUrl to verify pass**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py::TestGithubUrl -v 2>&1 | tail -20
```

Expected: all TestGithubUrl tests PASS.

- [ ] **Step 3: Run full test suite**

```bash
cd /home/sbera/git/personal/crashweb/web
python -m pytest tests/test_app.py -v 2>&1 | tail -30
```

Expected: ALL tests PASS.

- [ ] **Step 4: Update core_detail.html — conditional GitHub link and rename art_sdk_url**

In `web/templates/core_detail.html`, find line 27:

```jinja2
{% set gh_url = "https://github.com/philips-internal/synergy-base/issues/new?title=" ~ gh_title|urlencode ~ "&body=" ~ gh_body|urlencode %}

<textarea id="gh-issue-body" style="display:none;" aria-hidden="true">{{ gh_body }}</textarea>
<div id="gh-issue-area" style="float:right">
<a href="{{ gh_url }}" target="_blank" rel="noopener" class="btn" id="gh-issue-btn">&#128030; Create GitHub Issue</a>
</div>
```

Replace with:
```jinja2
{% if config.GITHUB_REPO %}
{% set gh_url = "https://github.com/" ~ config.GITHUB_REPO ~ "/issues/new?title=" ~ gh_title|urlencode ~ "&body=" ~ gh_body|urlencode %}
<textarea id="gh-issue-body" style="display:none;" aria-hidden="true">{{ gh_body }}</textarea>
<div id="gh-issue-area" style="float:right">
<a href="{{ gh_url }}" target="_blank" rel="noopener" class="btn" id="gh-issue-btn">&#128030; Create GitHub Issue</a>
</div>
{% endif %}
```

- [ ] **Step 5: Update core_detail.html — rename art_sdk_url to sdk_download_url (line ~71)**

Find:
```jinja2
                {% if art_sdk_url %}
                <a href="{{ art_sdk_url }}" class="btn btn-sm" style="margin-left:4px;background:#6c757d">Download SDK</a>
                {% endif %}
```

Replace with:
```jinja2
                {% if sdk_download_url %}
                <a href="{{ sdk_download_url }}" class="btn btn-sm" style="margin-left:4px;background:#6c757d">Download SDK</a>
                {% endif %}
```

- [ ] **Step 6: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add web/tests/test_app.py web/templates/core_detail.html
git commit -m "fix: update GitHub URL assertions; conditional GitHub issue link in template"
```

---

## Task 6: Rewrite traefik dynamic configs

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/traefik/traefik_dynamic-dev.yml`
- Modify: `/home/sbera/git/personal/crashweb/traefik/traefik_dynamic-prod.yml`
- Modify: `/home/sbera/git/personal/crashweb/traefik/traefik_dynamic-staging.yml`

All three files: strip `ldap-auth` middleware + embedded Philips CA cert, strip `auth` middleware, strip `ip-whitelist`. Replace Philips domains with generic. Keep `api-headers`, `redirect-to-https`, services.

- [ ] **Step 1: Overwrite traefik_dynamic-dev.yml**

```yaml
http:
  middlewares:
    api-headers:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
        accessControlAllowOriginList:
          - "*"
        accessControlAllowHeaders:
          - "*"
        accessControlMaxAge: 100
        addVaryHeader: true

    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true

  routers:
    crashweb-http:
      rule: Host(`coredumps.localhost`)
      entryPoints:
        - http
      middlewares:
        - redirect-to-https
      service: flask-service

    crashweb-router:
      rule: Host(`coredumps.localhost`)
      service: flask-service
      entryPoints:
        - https
      tls: true

  services:
    flask-service:
      loadBalancer:
        servers:
          - url: "http://flask-web:8080"

tls:
  stores:
    default:
      defaultCertificate:
        certFile: "/etc/ssl/custom-certs/localhost.crt"
        keyFile: "/etc/ssl/custom-certs/localhost.key"
```

- [ ] **Step 2: Overwrite traefik_dynamic-prod.yml**

```yaml
# Replace YOUR_DOMAIN with your actual domain name (e.g. crashweb.example.com)
http:
  middlewares:
    api-headers:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
        accessControlAllowOriginList:
          - "*"
        accessControlAllowHeaders:
          - "*"
        accessControlMaxAge: 100
        addVaryHeader: true

    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true

  routers:
    crashweb-http:
      rule: Host(`YOUR_DOMAIN`)
      entryPoints:
        - http
      middlewares:
        - redirect-to-https
      service: flask-service

    crashweb-router:
      rule: Host(`YOUR_DOMAIN`)
      service: flask-service
      entryPoints:
        - https
      tls: true

  services:
    flask-service:
      loadBalancer:
        servers:
          - url: "http://flask-web:8080"

tls:
  stores:
    default:
      defaultCertificate:
        certFile: "/etc/ssl/certs/crashweb.pem"
        keyFile: "/run/secrets/ssl_key_file"
```

- [ ] **Step 3: Overwrite traefik_dynamic-staging.yml**

```yaml
# Staging config — replace YOUR_STAGING_DOMAIN with your staging hostname
http:
  middlewares:
    api-headers:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
        accessControlAllowOriginList:
          - "*"
        accessControlAllowHeaders:
          - "*"
        accessControlMaxAge: 100
        addVaryHeader: true

    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true

  routers:
    crashweb-http:
      rule: Host(`YOUR_STAGING_DOMAIN`)
      entryPoints:
        - http
      middlewares:
        - redirect-to-https
      service: flask-service

    crashweb-router:
      rule: Host(`YOUR_STAGING_DOMAIN`)
      service: flask-service
      entryPoints:
        - https
      tls: true

  services:
    flask-service:
      loadBalancer:
        servers:
          - url: "http://flask-web:8080"

tls:
  stores:
    default:
      defaultCertificate:
        certFile: "/etc/ssl/certs/crashweb-staging.pem"
        keyFile: "/run/secrets/ssl_key_file"
```

- [ ] **Step 4: Verify no Philips/LDAP strings remain**

```bash
grep -ri 'philips\|synergy\|ldap\|artifactory\|nlvhtcway\|code1\.emi' \
  /home/sbera/git/personal/crashweb/traefik/
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add traefik/
git commit -m "feat: strip LDAP auth and Philips domains from traefik configs"
```

---

## Task 7: Update docker-compose files

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/docker-compose.yml`
- Modify: `/home/sbera/git/personal/crashweb/docker-compose-dev.yml`
- Modify: `/home/sbera/git/personal/crashweb/docker-compose-production.yml`

- [ ] **Step 1: Overwrite docker-compose.yml**

```yaml
services:
  traefik:
    image: "traefik:3.6.7"
    container_name: "traefik"
    ports:
      - "80:80"
      - "443:443"
    command:
      - "--providers.docker=true"
      - "--entrypoints.http.address=:80"
      - "--entrypoints.https.address=:443"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.filename=/etc/traefik/traefik_dynamic.yml"
      - "--log.level=INFO"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      - "traefik.enable=true"
    networks:
      - web
    restart: 'always'

  ccs:
    image: "ccs-ccs"
    build:
      context: .
      dockerfile: docker/ccs/Dockerfile
    depends_on:
      - mariadb
    restart: 'always'
    volumes:
      - "/home/coredumps:/space/coredumps"
      - "/home/sdks:/space/sdks"
    ports:
      - '5555:5555'
    networks:
      - default

  flask-web:
    image: "ccs-flask-web"
    build:
      context: .
      dockerfile: docker/flask-web/Dockerfile
    depends_on:
      - mariadb
    restart: 'always'
    volumes:
      - "/home/sdks:/var/www/sdks"
      - "/home/coredumps:/var/www/html/coredumps"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - SDK_BASE_URL=${SDK_BASE_URL:-}
      - SDK_PACKAGE_NAME=${SDK_PACKAGE_NAME:-}
      - SDK_SYSROOT_SUBPATH=${SDK_SYSROOT_SUBPATH:-}
      - GITHUB_REPO=${GITHUB_REPO:-}
    networks:
      - web
      - default

  mariadb:
    image: mariadb:10.6
    environment:
        MARIADB_ALLOW_EMPTY_ROOT_PASSWORD: 1
    restart: 'always'
    volumes:
      - "/home/mariadb:/var/lib/mysql"
      - "./docker/ccs/sql:/docker-entrypoint-initdb.d:ro"
    networks:
      - default

networks:
  web:
    name: web
```

- [ ] **Step 2: Update docker-compose-dev.yml — remove LDAP plugin and auth-users mount**

Find in `docker-compose-dev.yml`:
```yaml
  traefik:
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:9090"
      - "--entrypoints.http.address=:80"
      - "--entrypoints.https.address=:443"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.filename=/etc/traefik/traefik_dynamic.yml"
      - "--experimental.plugins.ldapAuth.modulename=github.com/wiltonsr/ldapAuth"
      - "--experimental.plugins.ldapAuth.version=v0.1.11"
      - "--log.level=DEBUG"
    volumes:
      - ${PWD}/certs:/etc/ssl/custom-certs:ro
      - ${PWD}/traefik/traefik_dynamic-dev.yml:/etc/traefik/traefik_dynamic.yml:ro
      - ${PWD}/traefik/auth-users-dev:/run/secrets/traefik-auth-users:ro
```

Replace with:
```yaml
  traefik:
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:9090"
      - "--entrypoints.http.address=:80"
      - "--entrypoints.https.address=:443"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.filename=/etc/traefik/traefik_dynamic.yml"
      - "--log.level=DEBUG"
    volumes:
      - ${PWD}/certs:/etc/ssl/custom-certs:ro
      - ${PWD}/traefik/traefik_dynamic-dev.yml:/etc/traefik/traefik_dynamic.yml:ro
```

- [ ] **Step 3: Overwrite docker-compose-production.yml**

```yaml
---
services:
  traefik:
    command:
      - "--providers.docker=true"
      - "--entrypoints.http.address=:80"
      - "--entrypoints.https.address=:443"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.filename=/etc/traefik/traefik_dynamic.yml"
      - "--log.level=INFO"
    volumes:
      - /etc/ssl/certs:/etc/ssl/certs:ro
      - /etc/pki:/etc/pki:ro
      - ${PWD}/traefik/traefik_dynamic-prod.yml:/etc/traefik/traefik_dynamic.yml:ro
    secrets:
      - ssl_key_file

secrets:
  ssl_key_file:
    file: ${HOME}/.ssh/crashweb.key
```

- [ ] **Step 4: Verify no Philips/LDAP/Artifactory strings remain**

```bash
grep -ri 'philips\|synergy\|ldap\|artifactory' \
  /home/sbera/git/personal/crashweb/docker-compose*.yml
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add docker-compose.yml docker-compose-dev.yml docker-compose-production.yml
git commit -m "feat: remove LDAP/Artifactory from docker-compose; add generic SDK and GitHub env vars"
```

---

## Task 8: Rewrite auto-install-sdk.sh

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/docker/flask-web/auto-install-sdk.sh`

Remove Artifactory listing API. Use `SDK_BASE_URL`, `SDK_PACKAGE_NAME`, `SDK_VERSION` env vars. No-op when not configured.

- [ ] **Step 1: Overwrite auto-install-sdk.sh**

```bash
#!/bin/bash
# Auto-install an SDK from a remote artifact server.
# Triggered by cron or on container start.
#
# Required env vars (set in docker-compose or .env):
#   SDK_BASE_URL      — base URL of artifact server, e.g. https://artifacts.example.com/sdks
#   SDK_PACKAGE_NAME  — package name prefix, e.g. my-device-sdk
#   SDK_VERSION       — version to install, e.g. v1.2.3
#
# Optional env vars:
#   SDK_DIR           — where to install SDKs (default: /var/www/sdks)
#   SDK_SYSROOT_SUBPATH — subdir that marks a successful install (default: empty = dir itself)
#
# No-op if any of SDK_BASE_URL, SDK_PACKAGE_NAME, SDK_VERSION are unset.

set -euo pipefail

SDK_DIR="${SDK_DIR:-/var/www/sdks}"
SDK_BASE_URL="${SDK_BASE_URL:-}"
SDK_PACKAGE_NAME="${SDK_PACKAGE_NAME:-}"
SDK_VERSION="${SDK_VERSION:-}"
SDK_SYSROOT_SUBPATH="${SDK_SYSROOT_SUBPATH:-}"
AUTO_LOG="${SDK_DIR}/.auto-install.log"

LOCK=""
cleanup() { [[ -n "$LOCK" && -f "$LOCK" ]] && rm -f "$LOCK"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$AUTO_LOG"; }

mkdir -p "$SDK_DIR"

if [[ -z "$SDK_BASE_URL" || -z "$SDK_PACKAGE_NAME" || -z "$SDK_VERSION" ]]; then
    log "SDK_BASE_URL, SDK_PACKAGE_NAME, or SDK_VERSION not configured. Skipping auto-install."
    exit 0
fi

VERSION="$SDK_VERSION"
SDK_VDIR="${SDK_DIR}/${VERSION}"
LOCK="${SDK_VDIR}/.installing"
INSTALL_LOG="${SDK_VDIR}/.install.log"

if [[ -n "$SDK_SYSROOT_SUBPATH" ]]; then
    INSTALLED_MARKER="${SDK_VDIR}/${SDK_SYSROOT_SUBPATH}"
else
    INSTALLED_MARKER="${SDK_VDIR}"
fi

log "Checking SDK ${VERSION}..."

if [[ -d "$INSTALLED_MARKER" && ! -f "$LOCK" ]]; then
    log "SDK ${VERSION} already installed. Nothing to do."
    exit 0
fi

if [[ -f "$LOCK" ]]; then
    log "Install already in progress. Nothing to do."
    exit 0
fi

log "Starting install of ${VERSION}..."
mkdir -p "$SDK_VDIR"
touch "$LOCK"

URL="${SDK_BASE_URL}/${SDK_PACKAGE_NAME}-${VERSION}.tar.gz"

CONTENT_LENGTH=$(curl -fsSI "$URL" 2>/dev/null | awk 'tolower($1)=="content-length:" {print $2+0}') || true
CALC=$(( ${CONTENT_LENGTH:-0} > 0 ? CONTENT_LENGTH * 8 : 30 * 1024 * 1024 * 1024 ))
MIN=$(( 30 * 1024 * 1024 * 1024 ))
NEEDED=$(( CALC > MIN ? CALC : MIN ))
log "Space needed: $(( NEEDED / 1024 / 1024 / 1024 )) GB"
python3 /app/sdk_space.py evict "$NEEDED" "$VERSION" "$SDK_DIR" >> "$AUTO_LOG" 2>&1 || \
    log "WARNING: not enough space after eviction; download may fail."

echo "Downloading ${URL} ..." >> "$INSTALL_LOG"
if curl -fsSL --retry 3 --retry-delay 5 "$URL" | tar xz -C "$SDK_VDIR" >> "$INSTALL_LOG" 2>&1; then
    SH_FILE=$(ls "$SDK_VDIR"/*.sh 2>/dev/null | head -1) || true
    if [[ -n "$SH_FILE" ]]; then
        echo "Running SDK installer: $SH_FILE ..." >> "$INSTALL_LOG"
        bash "$SH_FILE" -y -d "$SDK_VDIR" >> "$INSTALL_LOG" 2>&1 || true
        rm -f "$SH_FILE"
    fi
    echo "Done." >> "$INSTALL_LOG"
    rm -f "$LOCK"
    log "Install of ${VERSION} completed successfully."
else
    echo "FAILED" >> "$INSTALL_LOG"
    rm -f "$LOCK"
    log "ERROR: Install of ${VERSION} FAILED. See ${INSTALL_LOG}"
    exit 1
fi
```

- [ ] **Step 2: Verify no Philips/Artifactory strings remain**

```bash
grep -i 'philips\|synergy\|artifactory\|nlvhtcway' \
  /home/sbera/git/personal/crashweb/docker/flask-web/auto-install-sdk.sh
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add docker/flask-web/auto-install-sdk.sh
git commit -m "feat: rewrite auto-install-sdk.sh for generic SDK_BASE_URL pattern"
```

---

## Task 9: Add .env.example

**Files:**
- Create: `/home/sbera/git/personal/crashweb/.env.example`

- [ ] **Step 1: Create .env.example**

```env
# crashweb — environment configuration
# Copy this file to .env and fill in values before running docker compose.

# Required: set to a long random string (e.g. openssl rand -hex 32)
SECRET_KEY=change-me-to-a-long-random-string

# Optional: enables "Create GitHub Issue" button in core detail view
# Format: owner/repo  (e.g. myorg/my-firmware)
GITHUB_REPO=

# Optional: enables remote SDK download from an artifact server
# SDK_BASE_URL — base URL of your artifact server
# SDK_PACKAGE_NAME — filename prefix of the SDK tarball
# SDK_VERSION — version to auto-install at container start (used by auto-install-sdk.sh)
# SDK_SYSROOT_SUBPATH — subdir inside the SDK version dir that marks a completed install
#                        leave empty to treat the version dir itself as the install marker
SDK_BASE_URL=
SDK_PACKAGE_NAME=
SDK_VERSION=
SDK_SYSROOT_SUBPATH=

# Database — defaults work with the provided docker-compose.yml
DB_HOST=mariadb
DB_USER=apache
DB_PASSWORD=
DB_NAME=coredumps
DB_PORT=3306
```

- [ ] **Step 2: Verify .env.example not tracked as .env (check .gitignore)**

```bash
grep '\.env' /home/sbera/git/personal/crashweb/.gitignore
```

Expected: `.env` appears in .gitignore (`.env.example` should NOT be ignored — it's intentionally committed).

If `.env.example` is listed in .gitignore, remove that entry.

- [ ] **Step 3: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add .env.example
git commit -m "docs: add .env.example with all configurable env vars"
```

---

## Task 10: Update CONTRIBUTING.md and CI/CD workflow

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/CONTRIBUTING.md`
- Modify: `/home/sbera/git/personal/crashweb/.github/workflows/deploy-production.yml`

- [ ] **Step 1: Remove Philips references from CONTRIBUTING.md**

Find in `CONTRIBUTING.md` line 32:
```
Following these guidelines helps to communicate that you respect the time of the developers managing and developing this innersource project.
```
Replace `innersource project` with `open source project`.

Find line 37:
```
There is currently no official code of conduct, follow general Philips guidelines and rules and apply common sense.
```
Replace with:
```
There is currently no official code of conduct. Apply common sense and basic open-source etiquette.
```

Find lines 40-41:
```
At Philips, we use two different contribution models, OSS and GitHub.
This project uses the [OSS Model](#oss-model).
```
Replace with:
```
This project uses the standard open source contribution model.
```

- [ ] **Step 2: Overwrite .github/workflows/deploy-production.yml**

```yaml
name: Deploy to Production

# Example deployment workflow — customize for your infrastructure.
# This workflow SSHes into a server and restarts docker compose.
# For alternatives, see the README deployment section.

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy Production
    runs-on: ubuntu-latest
    environment: production
    env:
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
      SDK_BASE_URL: ${{ secrets.SDK_BASE_URL }}
      SDK_PACKAGE_NAME: ${{ secrets.SDK_PACKAGE_NAME }}
      GITHUB_REPO: ${{ secrets.GITHUB_REPO }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Deploy via SSH
        # Replace SSH_HOST, SSH_USER, SSH_KEY with your server details.
        # Store SSH_KEY as a GitHub Actions secret.
        # This step rsync's the repo to the server and restarts docker compose.
        run: |
          echo "Configure your own deployment step here."
          echo "Example: ssh user@host 'cd crashweb && git pull && docker compose up -d --build'"
          echo "Or use a dedicated deploy action (appleboy/ssh-action, etc.)"
```

- [ ] **Step 3: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add CONTRIBUTING.md .github/workflows/deploy-production.yml
git commit -m "docs: generalize CONTRIBUTING.md and CI/CD workflow template"
```

---

## Task 11: Rewrite README.md

**Files:**
- Modify: `/home/sbera/git/personal/crashweb/README.md`

- [ ] **Step 1: Overwrite README.md**

```markdown
# crashweb

A self-hosted web UI for collecting, browsing, and analyzing coredumps from embedded Linux devices.

## Features

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Stats, top crashing binaries with cause classification, recent coredumps |
| Coredumps | `/cores` | Filterable list by device, SW revision, signal, binary, backtrace checksum |
| Core detail | `/core/<id>` | Metadata, backtrace, journal, related crashes, ticket marking, GitHub issue creation |
| Devices | `/devices` | All known devices with crash counts |
| Device detail | `/device/<id>` | Per-device coredump list |
| SW Revisions | `/revisions` | All SW revisions with crash counts and SDK install status |
| Crash Analysis | `/analyze` | Crash grouping by backtrace signature — systematic bug detection, cause badges |

Key capabilities:
- **Crash cause classification** — detects Watchdog Timeout, OOM Kill, Stack Smash, Bus Error, Segfault from journal lines
- **Systematic bug detection** — flags crash signatures seen on more than one device
- **Ticket / Mark-as-analyzed** — mark any crash signature with an issue number, propagated across all pages
- **Create GitHub Issue** — pre-fills title and backtrace in GitHub `issues/new` (requires `GITHUB_REPO`)
- **SDK management** — install SDKs per revision for backtrace generation (requires `SDK_BASE_URL`)
- **Coredump download** — direct download of `.core.gz` files with path traversal protection

## Stack

- **Flask** (Python 3) + gunicorn
- **MariaDB 10.6**
- **Traefik 3.6.7** (reverse proxy + TLS)
- **Docker Compose**

## Quick Start (local, no TLS)

```bash
# 1. Clone
git clone https://github.com/sbera.connects/crashweb
cd crashweb

# 2. Configure
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a random string:
#   SECRET_KEY=$(openssl rand -hex 32)

# 3. Start (no Traefik — Flask on port 8080)
docker compose -f docker-compose.yml -f docker-compose-local.yml up -d mariadb flask-web ccs

# 4. Open http://localhost:8080
```

## Production Deployment

```bash
cp .env.example .env
# Fill in SECRET_KEY and any optional settings

# Edit traefik/traefik_dynamic-prod.yml:
#   - Replace YOUR_DOMAIN with your domain name
#   - Set certFile path to your TLS certificate

# Place SSL key at: ~/.ssh/crashweb.key

docker compose -f docker-compose.yml -f docker-compose-production.yml up -d --build
```

## Configuration

All settings via environment variables (or `.env` file). See `.env.example` for full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key — any long random string |
| `GITHUB_REPO` | No | `owner/repo` — enables "Create GitHub Issue" button |
| `SDK_BASE_URL` | No | Base URL for SDK downloads — enables remote SDK install |
| `SDK_PACKAGE_NAME` | No | SDK tarball name prefix (e.g. `my-device-sdk`) |
| `SDK_VERSION` | No | Version to auto-install on container start |
| `SDK_SYSROOT_SUBPATH` | No | Subdir inside SDK dir that marks install complete |
| `DB_HOST` | No | MariaDB host (default: `mariadb`) |
| `DB_USER` | No | DB user (default: `apache`) |
| `DB_PASSWORD` | No | DB password (default: empty) |
| `DB_NAME` | No | DB name (default: `coredumps`) |

## Device Setup

Devices send coredumps to the `ccs` service on port 5555. The collector service:
1. Receives the coredump file
2. Stores it to `COREDUMP_DIR` (`/home/coredumps` on the host)
3. Records metadata in MariaDB
4. Triggers backtrace generation (if SDK installed for the SW revision)

## SDK Installation

Backtraces require the matching SDK (cross-compiled sysroot) for the target device SW revision.

**Local:** Place SDKs in `/home/sdks/{version}/` on the host. The version dir must contain a sysroot (or set `SDK_SYSROOT_SUBPATH` appropriately).

**Remote:** Set `SDK_BASE_URL` and `SDK_PACKAGE_NAME`. The app will download `{SDK_BASE_URL}/{SDK_PACKAGE_NAME}-{version}.tar.gz` on demand. If the tarball contains a `.sh` installer, it runs automatically.

## Development

```bash
cp .env.example .env
# Set SECRET_KEY in .env

# Generate local certs (required for TLS in dev)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/localhost.key \
  -out certs/localhost.crt -days 365 -nodes \
  -subj '/CN=coredumps.localhost'

# Add to /etc/hosts: 127.0.0.1 coredumps.localhost

docker compose -f docker-compose.yml -f docker-compose-dev.yml up -d
# Flask hot-reloads on code changes
# UI: https://coredumps.localhost
```

### Running Tests

```bash
cd web
pip install -r requirements.txt
pytest tests/ -v
```

## License

See [LICENSE](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
```

- [ ] **Step 2: Verify no Philips/Synergy refs remain in README**

```bash
grep -i 'philips\|synergy\|artifactory\|ldap' /home/sbera/git/personal/crashweb/README.md
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
cd /home/sbera/git/personal/crashweb
git add README.md
git commit -m "docs: rewrite README for public crashweb project"
```

---

## Task 12: Final verification — grep for remaining company strings

**Files:**
- Read-only scan of entire crashweb directory

- [ ] **Step 1: Grep for all company-specific strings**

```bash
cd /home/sbera/git/personal/crashweb
grep -ri --include='*.py' --include='*.yml' --include='*.yaml' \
  --include='*.html' --include='*.md' --include='*.sh' \
  --include='*.txt' --include='*.json' --include='*.toml' \
  'philips\|synergy\|artifactory\|ldap\|nlvhtcway\|wiltonsr' \
  . 2>/dev/null | grep -v '.git/'
```

Expected: no output. If any hits appear, fix them before proceeding.

- [ ] **Step 2: Grep for hardcoded IPs**

```bash
grep -rn '10\.218\.\|130\.145\.\|130\.143\.' /home/sbera/git/personal/crashweb/ \
  --include='*.yml' --include='*.yaml' 2>/dev/null | grep -v '.git/'
```

Expected: no output.

- [ ] **Step 3: Verify SECRET_KEY has no default**

```bash
grep 'fgklhjwkmnlcbn' /home/sbera/git/personal/crashweb/web/config.py
```

Expected: no output (hardcoded secret was removed).

- [ ] **Step 4: Commit any remaining fixes**

If any hits were found in Steps 1-3, fix them and commit:
```bash
cd /home/sbera/git/personal/crashweb
git add -A
git commit -m "fix: remove remaining company-specific strings"
```

---

## Task 13: Create GitHub repo and push

- [ ] **Step 1: Create public GitHub repo**

```bash
cd /home/sbera/git/personal/crashweb
gh auth status
# Verify personal account (sbera.connects) is active
# If work account is shown, run: gh auth login --hostname github.com
gh repo create crashweb --public --description "Self-hosted coredump collection and analysis web UI"
```

- [ ] **Step 2: Push**

```bash
cd /home/sbera/git/personal/crashweb
git remote add origin https://github.com/sbera.connects/crashweb.git
git push -u origin main
```

- [ ] **Step 3: Verify repo is live**

```bash
gh repo view sbera.connects/crashweb
```

Expected: repo description, public visibility, main branch with recent commits.
