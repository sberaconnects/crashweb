"""
Unit and integration tests for the Flask coredump web app.

Run from the repo root:
    /home/sbera_320291074/git/.venv/bin/pytest web/tests/ -v

No real DB is needed — all DB calls are patched via unittest.mock.
"""
import os
import sys
import json
import types
import unittest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Ensure web/ and shared utilities are importable; config points at sqlite
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
_repo_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.join(_repo_root, 'docker', 'shared'))

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_NAME', 'test')
os.environ.setdefault('DB_PORT', '3306')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing')
os.environ.setdefault('GITHUB_REPO', 'test-owner/test-repo')

# Patch pymysql before app import so SQLAlchemy doesn't try to connect
import pymysql
_orig_connect = pymysql.connect
pymysql.connect = MagicMock(side_effect=Exception("no real db in tests"))

import app as flask_app   # noqa: E402  (must be after sys.path insert)

pymysql.connect = _orig_connect  # restore (not used further but clean)


# ---------------------------------------------------------------------------
# Helper: fresh test client with DB calls fully mocked
# ---------------------------------------------------------------------------
def make_client():
    flask_app.app.config['TESTING'] = True
    flask_app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'  # in-memory
    return flask_app.app.test_client()


# ===========================================================================
# 1. Pure-function unit tests (no DB, no HTTP)
# ===========================================================================
class TestGithubUrl(unittest.TestCase):
    def test_numeric_issue_returns_url(self):
        url = flask_app._github_url('15884')
        assert url == 'https://github.com/test-owner/test-repo/issues/15884'

    def test_non_numeric_returns_none(self):
        assert flask_app._github_url('ABC-123') is None

    def test_empty_returns_none(self):
        assert flask_app._github_url('') is None

    def test_none_returns_none(self):
        assert flask_app._github_url(None) is None

    def test_whitespace_stripped(self):
        url = flask_app._github_url('  42  ')
        assert url == 'https://github.com/test-owner/test-repo/issues/42'

    def test_no_github_repo_returns_none(self):
        """When GITHUB_REPO is not configured, _github_url always returns None."""
        with flask_app.app.test_request_context():
            flask_app.app.config['GITHUB_REPO'] = ''
            result = flask_app._github_url('123')
            flask_app.app.config['GITHUB_REPO'] = 'test-owner/test-repo'
        assert result is None


class TestBadgeColor(unittest.TestCase):
    def test_returns_hex_color(self):
        color = flask_app.badge_color('some-process')
        assert color.startswith('#')
        assert len(color) == 7

    def test_deterministic(self):
        assert flask_app.badge_color('foo') == flask_app.badge_color('foo')

    def test_different_inputs_may_differ(self):
        # Not guaranteed to differ for every pair, but these do
        colors = {flask_app.badge_color(str(i)) for i in range(10)}
        assert len(colors) > 1


# ===========================================================================
# 2. ticket_api — input validation (no DB needed, validation fires first)
# ===========================================================================
class TestTicketApiValidation(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_missing_bt_csum_returns_400(self):
        r = self.client.post('/ticket_api', data={'action': 'mark', 'issue': '123'})
        assert r.status_code == 400
        assert b'Invalid bt_csum' in r.data

    def test_bt_csum_too_long_returns_400(self):
        r = self.client.post('/ticket_api', data={
            'action': 'mark', 'bt_csum': 'a' * 65, 'issue': '123'
        })
        assert r.status_code == 400

    def test_unknown_action_returns_400(self):
        r = self.client.post('/ticket_api', data={
            'action': 'delete', 'bt_csum': 'abc123'
        })
        assert r.status_code == 400
        assert b'Unknown action' in r.data

    def test_mark_without_issue_returns_400(self):
        r = self.client.post('/ticket_api', data={
            'action': 'mark', 'bt_csum': 'abc123', 'issue': ''
        })
        assert r.status_code == 400
        assert b'issue is required' in r.data


# ===========================================================================
# 3. ticket_api — mark success (DB mocked)
# ===========================================================================
class TestTicketApiMark(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    @patch.object(flask_app.db.session, 'execute')
    @patch.object(flask_app.db.session, 'commit')
    def test_mark_returns_ok_with_url(self, mock_commit, mock_execute):
        r = self.client.post('/ticket_api', data={
            'action': 'mark',
            'bt_csum': 'deadbeef' * 4,  # 32 chars, valid
            'issue': '15884',
            'note': 'root cause found',
        })
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body['status'] == 'ok'
        assert body['issue'] == '15884'
        assert body['note'] == 'root cause found'
        assert 'issues/15884' in body['url']
        mock_commit.assert_called_once()

    @patch.object(flask_app.db.session, 'execute')
    @patch.object(flask_app.db.session, 'commit')
    def test_mark_non_numeric_issue_url_is_none(self, mock_commit, mock_execute):
        r = self.client.post('/ticket_api', data={
            'action': 'mark',
            'bt_csum': 'deadbeef' * 4,
            'issue': 'JIRA-99',
            'note': '',
        })
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body['url'] is None

    @patch.object(flask_app.db.session, 'execute')
    @patch.object(flask_app.db.session, 'commit')
    def test_mark_truncates_long_issue(self, mock_commit, mock_execute):
        # issue field is capped at 32 chars in app.py
        long_issue = '1' * 50
        r = self.client.post('/ticket_api', data={
            'action': 'mark',
            'bt_csum': 'abc123',
            'issue': long_issue,
        })
        assert r.status_code == 200
        body = json.loads(r.data)
        assert len(body['issue']) <= 32


# ===========================================================================
# 4. ticket_api — unmark success (DB mocked)
# ===========================================================================
class TestTicketApiUnmark(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    @patch.object(flask_app.db.session, 'execute')
    @patch.object(flask_app.db.session, 'commit')
    def test_unmark_returns_ok(self, mock_commit, mock_execute):
        r = self.client.post('/ticket_api', data={
            'action': 'unmark',
            'bt_csum': 'deadbeef' * 4,
        })
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body['status'] == 'ok'
        mock_commit.assert_called_once()


# ===========================================================================
# 5. _fetch_tickets — graceful on DB error
# ===========================================================================
class TestFetchTickets(unittest.TestCase):
    @patch.object(flask_app.db.session, 'execute', side_effect=Exception('db down'))
    def test_returns_empty_dict_on_error(self, _mock):
        with flask_app.app.app_context():
            result = flask_app._fetch_tickets()
        assert result == {}

    @patch.object(flask_app.db.session, 'execute')
    def test_returns_keyed_by_csum(self, mock_execute):
        mock_execute.return_value.fetchall.return_value = [
            ('csum1', '15884', 'some note', '2026-04-22 10:00:00'),
            ('csum2', '15885', None, '2026-04-22 11:00:00'),
        ]
        with flask_app.app.app_context():
            result = flask_app._fetch_tickets()
        assert 'csum1' in result
        assert result['csum1']['issue'] == '15884'
        assert result['csum1']['note'] == 'some note'
        assert 'csum2' in result


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


if __name__ == '__main__':
    unittest.main()
