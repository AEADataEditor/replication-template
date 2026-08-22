#!/usr/bin/env python3
"""Tests for jira_add_comment.py. Run: python3 tools/test_jira_add_comment.py"""
import base64
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_add_comment as jac


def _issue(key, issuetype, summary="", parent=None, subtasks=()):
    """Build a normalized issue dict of the shape the clients return."""
    return {
        'key': key,
        'summary': summary,
        'issuetype': issuetype,
        'parent': parent,
        'subtasks': [
            {'key': k, 'issuetype': t, 'summary': s} for k, t, s in subtasks
        ],
    }


class FakeClient:
    """Stands in for RestClient/LibraryClient in the resolution tests."""

    def __init__(self, issues):
        self.issues = issues
        self.posted = []

    def get_issue(self, issue_key):
        if issue_key not in self.issues:
            raise KeyError(issue_key)
        return self.issues[issue_key]

    def add_comment(self, issue_key, comment):
        self.posted.append((issue_key, comment))


PART_B_TYPE = "Part B processing: run code or complete report"


class TestParseEnvFile(unittest.TestCase):
    def _write(self, content):
        handle = tempfile.NamedTemporaryFile('w', suffix='.env', delete=False)
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_plain_assignments(self):
        path = self._write("JIRA_USERNAME=me@example.com\nJIRA_API_KEY=abc123\n")
        self.assertEqual(
            jac.parse_env_file(path),
            {'JIRA_USERNAME': 'me@example.com', 'JIRA_API_KEY': 'abc123'},
        )

    def test_export_prefix_quotes_and_comments(self):
        path = self._write(
            "# a comment\n"
            "\n"
            'export JIRA_USERNAME="me@example.com"\n'
            "export JIRA_API_KEY='abc 123'\n"
            "NOT_AN_ASSIGNMENT\n"
        )
        self.assertEqual(
            jac.parse_env_file(path),
            {'JIRA_USERNAME': 'me@example.com', 'JIRA_API_KEY': 'abc 123'},
        )

    def test_value_may_contain_equals(self):
        path = self._write("JIRA_API_KEY=a=b=c\n")
        self.assertEqual(jac.parse_env_file(path)['JIRA_API_KEY'], 'a=b=c')

    def test_missing_file_is_empty(self):
        self.assertEqual(jac.parse_env_file('/nonexistent/path/.env'), {})


class TestGetCredentials(unittest.TestCase):
    def _write(self, content):
        handle = tempfile.NamedTemporaryFile('w', suffix='.env', delete=False)
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_environment_wins_over_file(self):
        path = self._write("JIRA_USERNAME=file@example.com\nJIRA_API_KEY=filekey\n")
        env = {'JIRA_USERNAME': 'env@example.com', 'JIRA_API_KEY': 'envkey'}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(jac.get_credentials([path]), ('env@example.com', 'envkey'))

    def test_file_fills_in_what_environment_lacks(self):
        path = self._write("JIRA_API_KEY=filekey\n")
        with patch.dict(os.environ, {'JIRA_USERNAME': 'env@example.com'}, clear=True):
            with patch.object(jac, 'candidate_env_files', return_value=[path]):
                self.assertEqual(jac.get_credentials(), ('env@example.com', 'filekey'))

    def test_returns_none_when_incomplete(self):
        with patch.dict(os.environ, {'JIRA_USERNAME': 'env@example.com'}, clear=True):
            with patch.object(jac, 'candidate_env_files', return_value=[]):
                self.assertEqual(jac.get_credentials(), (None, None))


class TestFindPartBSubtask(unittest.TestCase):
    def test_finds_part_b_by_issue_type(self):
        client = FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[
                    ('AEAREP-101', 'Prepare Prelim Report (Part A)', 'Prepare Part A'),
                    ('AEAREP-102', PART_B_TYPE, 'Prepare Part B'),
                ],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), 'AEAREP-102')

    def test_returns_empty_when_no_part_b_exists(self):
        client = FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[('AEAREP-101', 'Assess', 'Assess deposit')],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), '')

    def test_given_the_part_b_subtask_itself(self):
        client = FakeClient({
            'AEAREP-102': _issue('AEAREP-102', PART_B_TYPE, 'Prepare Part B',
                                 parent='AEAREP-100'),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-102'), 'AEAREP-102')

    def test_given_a_sibling_subtask_walks_up_to_the_parent(self):
        client = FakeClient({
            'AEAREP-101': _issue('AEAREP-101', 'Prepare Prelim Report (Part A)',
                                 'Prepare Part A', parent='AEAREP-100'),
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[
                    ('AEAREP-101', 'Prepare Prelim Report (Part A)', 'Prepare Part A'),
                    ('AEAREP-102', PART_B_TYPE, 'Prepare Part B'),
                ],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-101'), 'AEAREP-102')

    def test_summary_fallback_for_sivacor_style_subtasks(self):
        client = FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[
                    ('AEAREP-101', 'Assess', 'Assess deposit'),
                    ('AEAREP-103', 'Author-generated reproducibility check',
                     'Prepare Part B (SIVACOR)'),
                ],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), 'AEAREP-103')

    def test_issue_type_match_beats_summary_match(self):
        client = FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[
                    ('AEAREP-103', 'Author-generated reproducibility check',
                     'Prepare Part B (SIVACOR)'),
                    ('AEAREP-102', PART_B_TYPE, 'Prepare Part B'),
                ],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), 'AEAREP-102')

    def test_picks_highest_numbered_of_several_part_b_subtasks(self):
        client = FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[
                    ('AEAREP-102', PART_B_TYPE, 'Prepare Part B'),
                    ('AEAREP-140', PART_B_TYPE, 'Prepare Part B (revision)'),
                ],
            ),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), 'AEAREP-140')

    def test_parent_summary_mentioning_part_b_is_not_a_match(self):
        # A Task whose own summary says "Part B" must not be treated as the sub-task.
        client = FakeClient({
            'AEAREP-100': _issue('AEAREP-100', 'Task', 'Rerun Part B for this paper'),
        })
        self.assertEqual(jac.find_part_b_subtask(client, 'AEAREP-100'), '')

    def test_unreadable_issue_returns_empty(self):
        self.assertEqual(jac.find_part_b_subtask(FakeClient({}), 'AEAREP-999'), '')


class TestNormalizeIssue(unittest.TestCase):
    """Checks against the real shape returned by /rest/api/2/issue/KEY."""

    # Trimmed from a live AEAREP-10016 response: a Task with a Part A sub-task,
    # an author-generated reproducibility check, the real Part B sub-task, and
    # an FYI sub-task.
    PAYLOAD = {
        "key": "AEAREP-10016",
        "fields": {
            "summary": "JEL-2026-1813 Data Review Request R.0",
            "issuetype": {"id": "10005", "name": "Task", "subtask": False},
            "subtasks": [
                {"id": "44585", "key": "AEAREP-10028", "fields": {
                    "summary": "Prepare Part A",
                    "issuetype": {"id": "10011",
                                  "name": "Prepare Prelim Report (Part A)",
                                  "subtask": True}}},
                {"id": "44586", "key": "AEAREP-10029", "fields": {
                    "summary": "Request Author-Generated Reproducibility Check",
                    "issuetype": {"id": "10096",
                                  "name": "Author-generated reproducibility check",
                                  "subtask": True}}},
                {"id": "44589", "key": "AEAREP-10032", "fields": {
                    "summary": "Part B ",
                    "issuetype": {"id": "10010",
                                  "name": "Part B processing: run code or complete report",
                                  "subtask": True}}},
                {"id": "44623", "key": "AEAREP-10066", "fields": {
                    "summary": "JEL-2026-1813 Data Review Request R.1",
                    "issuetype": {"id": "10018", "name": "FYI", "subtask": True}}},
            ],
        },
    }

    def test_normalizes_a_real_payload(self):
        issue = jac._normalize_issue(self.PAYLOAD["fields"], self.PAYLOAD["key"])
        self.assertEqual(issue["issuetype"], "Task")
        self.assertIsNone(issue["parent"])
        self.assertEqual(
            [s["key"] for s in issue["subtasks"]],
            ["AEAREP-10028", "AEAREP-10029", "AEAREP-10032", "AEAREP-10066"],
        )

    def test_part_b_lookup_on_a_real_payload(self):
        issue = jac._normalize_issue(self.PAYLOAD["fields"], self.PAYLOAD["key"])
        client = FakeClient({"AEAREP-10016": issue})
        # The issue-type match must win over the reproducibility-check sub-task.
        self.assertEqual(jac.find_part_b_subtask(client, "AEAREP-10016"), "AEAREP-10032")

    def test_normalizes_a_subtask_payload_with_a_parent(self):
        fields = {
            "summary": "Part B ",
            "issuetype": {"name": "Part B processing: run code or complete report"},
            "parent": {"id": "44573", "key": "AEAREP-10016",
                       "fields": {"summary": "JEL-2026-1813 Data Review Request R.0"}},
        }
        issue = jac._normalize_issue(fields, "AEAREP-10032")
        self.assertEqual(issue["parent"], "AEAREP-10016")
        self.assertEqual(issue["subtasks"], [])


class TestStatusLine(unittest.TestCase):
    def test_started(self):
        self.assertEqual(jac.status_line('started'), '🚀 Job started')

    def test_completed(self):
        self.assertEqual(jac.status_line('completed'), '✅ Job completed')

    def test_exit_code_zero_stays_completed(self):
        self.assertEqual(jac.status_line('completed', 0), '✅ Job completed')

    def test_nonzero_exit_code_becomes_failed(self):
        self.assertEqual(jac.status_line('completed', 3), '❌ Job failed (exit code 3)')

    def test_label_is_used(self):
        self.assertEqual(jac.status_line('started', None, 'SLURM job main.do'),
                         '🚀 SLURM job main.do started')

    def test_exit_code_does_not_rewrite_a_started_status(self):
        self.assertEqual(jac.status_line('started', 0), '🚀 Job started')

    def test_unknown_status_passes_through(self):
        self.assertEqual(jac.status_line('queued'), 'ℹ️ Job queued')


class TestComposeComment(unittest.TestCase):
    def test_status_and_text(self):
        result = jac.compose_comment(comment='Running main.do', status='started')
        self.assertEqual(result, '🚀 Job started\n\nRunning main.do')

    def test_slurm_context_folded_into_the_status_line(self):
        env = {
            'SLURM_JOB_ID': '12345',
            'SLURM_JOB_NAME': 'RunStata',
            'SLURM_SUBMIT_DIR': '/home/lv39/jira-slurm-test',
        }
        with patch.dict(os.environ, env, clear=True):
            result = jac.compose_comment(status='started', slurm=True)
        self.assertEqual(
            result,
            '🚀 SLURM job 12345 RunStata started (directory: /home/lv39/jira-slurm-test)',
        )

    def test_slurm_ignores_the_explicit_label(self):
        env = {'SLURM_JOB_ID': '12345', 'SLURM_JOB_NAME': 'RunStata'}
        with patch.dict(os.environ, env, clear=True):
            result = jac.compose_comment(status='started', label='smoke test', slurm=True)
        self.assertIn('SLURM job 12345 RunStata', result)
        self.assertNotIn('smoke test', result)

    def test_slurm_omits_unwanted_fields(self):
        env = {
            'SLURM_JOB_ID': '12345',
            'SLURM_JOB_NAME': 'RunStata',
            'SLURM_JOB_PARTITION': 'slow',
            'SLURM_JOB_NODELIST': 'cbsuecco07',
            'SLURM_CPUS_PER_TASK': '8',
            'SLURM_CLUSTER_NAME': 'cbsueccosl01',
            'SLURMD_NODENAME': 'cbsuecco07',
        }
        with patch.dict(os.environ, env, clear=True):
            result = jac.compose_comment(status='started', slurm=True)
        for unwanted in ('Partition', 'Node(s)', 'CPUs per task', 'Cluster',
                         'Running on', 'slow', 'cbsuecco07', '8'):
            self.assertNotIn(unwanted, result)

    def test_slurm_falls_back_to_the_label_outside_a_job(self):
        with patch.dict(os.environ, {}, clear=True):
            result = jac.compose_comment(status='started', label='smoke test', slurm=True)
        self.assertEqual(result, '🚀 smoke test started')

    def test_slurm_context_is_kept_when_there_is_no_status_line(self):
        env = {'SLURM_JOB_ID': '590341', 'SLURM_JOB_NAME': 'RunStata',
               'SLURM_SUBMIT_DIR': '/home/lv39/t'}
        with patch.dict(os.environ, env, clear=True):
            result = jac.compose_comment(comment='Stata finished', slurm=True)
        self.assertEqual(
            result,
            'Stata finished\n\nSLURM job 590341 RunStata (directory: /home/lv39/t)',
        )

    def test_slurm_omitted_outside_a_job(self):
        with patch.dict(os.environ, {}, clear=True):
            result = jac.compose_comment(comment='hello', slurm=True)
        self.assertEqual(result, 'hello')

    def test_slurm_with_failure_orders_exit_code_before_directory(self):
        env = {
            'SLURM_JOB_ID': '12345',
            'SLURM_JOB_NAME': 'RunStata',
            'SLURM_SUBMIT_DIR': '/home/lv39/jira-slurm-test',
        }
        with patch.dict(os.environ, env, clear=True):
            result = jac.compose_comment(status='completed', exit_code=7, slurm=True)
        self.assertEqual(
            result,
            '❌ SLURM job 12345 RunStata failed (exit code 7) '
            '(directory: /home/lv39/jira-slurm-test)',
        )


class TestSlurmHelpers(unittest.TestCase):
    def test_slurm_label_combines_id_and_name(self):
        env = {'SLURM_JOB_ID': '12345', 'SLURM_JOB_NAME': 'RunStata'}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(jac.slurm_label('fallback'), 'SLURM job 12345 RunStata')

    def test_slurm_label_without_name(self):
        with patch.dict(os.environ, {'SLURM_JOB_ID': '12345'}, clear=True):
            self.assertEqual(jac.slurm_label('fallback'), 'SLURM job 12345')

    def test_slurm_label_falls_back_outside_a_job(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(jac.slurm_label('fallback'), 'fallback')

    def test_slurm_directory_suffix(self):
        with patch.dict(os.environ, {'SLURM_SUBMIT_DIR': '/a/b'}, clear=True):
            self.assertEqual(jac.slurm_directory_suffix(), ' (directory: /a/b)')

    def test_slurm_directory_suffix_empty_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(jac.slurm_directory_suffix(), '')


class TestResolveIssueKey(unittest.TestCase):
    def test_explicit_key_passes_through(self):
        self.assertEqual(jac.resolve_issue_key('AEAREP-100'), 'AEAREP-100')

    def test_auto_uses_jiraticket_environment_variable(self):
        with patch.dict(os.environ, {'jiraticket': 'AEAREP-200'}, clear=True):
            self.assertEqual(jac.resolve_issue_key('auto'), 'AEAREP-200')

    def _config_dir(self, content):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(os.path.join(directory.name, 'config.yml'), 'w') as handle:
            handle.write(content)
        return directory.name

    def test_auto_falls_back_to_config_yml(self):
        directory = self._config_dir('openicpsr: 123456\njiraticket: AEAREP-300\n')
        with patch.dict(os.environ, {'SLURM_SUBMIT_DIR': directory}, clear=True):
            self.assertEqual(jac.resolve_issue_key('auto'), 'AEAREP-300')

    def test_config_yml_is_found_in_a_parent_directory(self):
        directory = self._config_dir('jiraticket: AEAREP-301\n')
        nested = os.path.join(directory, 'sub', 'deeper')
        os.makedirs(nested)
        with patch.dict(os.environ, {'SLURM_SUBMIT_DIR': nested}, clear=True):
            self.assertEqual(jac.resolve_issue_key('auto'), 'AEAREP-301')

    def test_empty_config_value_yields_empty(self):
        directory = self._config_dir('jiraticket:\n')
        self.assertEqual(jac.ticket_from_config(os.path.join(directory, 'config.yml')), '')


class TestAddComment(unittest.TestCase):
    def _client(self):
        return FakeClient({
            'AEAREP-100': _issue(
                'AEAREP-100', 'Task', 'Some paper',
                subtasks=[('AEAREP-102', PART_B_TYPE, 'Prepare Part B')],
            ),
        })

    def test_posts_to_main_ticket_without_partb(self):
        client = self._client()
        with patch.object(jac, 'get_jira_client', return_value=client):
            target = jac.add_comment('aearep-100', 'hello')
        self.assertEqual(target, 'AEAREP-100')
        self.assertEqual(client.posted, [('AEAREP-100', 'hello')])

    def test_posts_to_part_b_subtask_with_partb(self):
        client = self._client()
        with patch.object(jac, 'get_jira_client', return_value=client):
            target = jac.add_comment('AEAREP-100', 'hello', partb=True)
        self.assertEqual(target, 'AEAREP-102')
        self.assertEqual(client.posted, [('AEAREP-102', 'hello')])

    def test_partb_falls_back_to_main_ticket(self):
        client = FakeClient({'AEAREP-100': _issue('AEAREP-100', 'Task', 'Some paper')})
        with patch.object(jac, 'get_jira_client', return_value=client):
            target = jac.add_comment('AEAREP-100', 'hello', partb=True)
        self.assertEqual(target, 'AEAREP-100')
        self.assertEqual(client.posted, [('AEAREP-100', 'hello')])

    def test_dry_run_posts_nothing(self):
        client = self._client()
        with patch.object(jac, 'get_jira_client', return_value=client):
            target = jac.add_comment('AEAREP-100', 'hello', partb=True, dry_run=True)
        self.assertEqual(target, 'AEAREP-102')
        self.assertEqual(client.posted, [])

    def test_dry_run_without_credentials_still_shows_the_comment(self):
        with patch.object(jac, 'get_jira_client', return_value=None):
            target = jac.add_comment('AEAREP-100', 'hello', partb=True, dry_run=True)
        self.assertEqual(target, 'AEAREP-100')

    def test_missing_credentials_is_not_fatal(self):
        with patch.object(jac, 'get_jira_client', return_value=None):
            self.assertEqual(jac.add_comment('AEAREP-100', 'hello'), '')

    def test_unresolvable_ticket_is_not_fatal(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(jac, 'find_config_yml', return_value=None):
                self.assertEqual(jac.add_comment('auto', 'hello'), '')

    def test_garbage_issue_key_is_rejected(self):
        with patch.object(jac, 'get_jira_client', side_effect=AssertionError):
            self.assertEqual(jac.add_comment('not-a-key-at-all', 'hello'), '')


class _StubJiraHandler(BaseHTTPRequestHandler):
    """Serves just enough of the Jira REST API to exercise RestClient."""

    ISSUE = TestNormalizeIssue.PAYLOAD

    def log_message(self, *args):  # keep the test output quiet
        pass

    def _send(self, code, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.server.seen.append(('GET', self.path, self.headers.get('Authorization')))
        if self.path.startswith('/rest/api/2/issue/AEAREP-10016'):
            self._send(200, self.ISSUE)
        else:
            self._send(404, {"errorMessages": ["Issue does not exist"]})

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
        self.server.seen.append(('POST', self.path, body))
        if '/AEAREP-10032/' in self.path or '/AEAREP-10016/' in self.path:
            self._send(201, {"id": "1"})
        else:
            self._send(401, {"errorMessages": ["Unauthorized"]})


class TestRestClient(unittest.TestCase):
    """Exercises the standard-library REST path used when `jira` is absent."""

    def setUp(self):
        self.server = HTTPServer(('127.0.0.1', 0), _StubJiraHandler)
        self.server.seen = []
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:{0}'.format(self.server.server_port)
        self.client = jac.RestClient('me@example.com', 'secret', server=self.url)

    def test_get_issue_parses_the_response(self):
        issue = self.client.get_issue('AEAREP-10016')
        self.assertEqual(issue['key'], 'AEAREP-10016')
        self.assertEqual(issue['issuetype'], 'Task')
        self.assertEqual(len(issue['subtasks']), 4)

    def test_get_issue_sends_basic_auth_and_requests_the_needed_fields(self):
        self.client.get_issue('AEAREP-10016')
        method, path, auth = self.server.seen[0]
        self.assertEqual(method, 'GET')
        self.assertIn('fields=summary,issuetype,parent,subtasks', path)
        expected = base64.b64encode(b'me@example.com:secret').decode('ascii')
        self.assertEqual(auth, 'Basic ' + expected)

    def test_add_comment_posts_the_body(self):
        self.client.add_comment('AEAREP-10032', 'hello from SLURM')
        method, path, body = self.server.seen[0]
        self.assertEqual(method, 'POST')
        self.assertEqual(path, '/rest/api/2/issue/AEAREP-10032/comment')
        self.assertEqual(body, {'body': 'hello from SLURM'})

    def test_http_error_message_includes_the_jira_detail(self):
        with self.assertRaises(RuntimeError) as caught:
            self.client.get_issue('AEAREP-999')
        self.assertIn('404', str(caught.exception))
        self.assertIn('Issue does not exist', str(caught.exception))

    def test_part_b_lookup_end_to_end_over_rest(self):
        self.assertEqual(
            jac.find_part_b_subtask(self.client, 'AEAREP-10016'), 'AEAREP-10032'
        )

    def test_add_comment_end_to_end_over_rest(self):
        with patch.object(jac, 'get_jira_client', return_value=self.client):
            target = jac.add_comment('AEAREP-10016', 'from the compute node', partb=True)
        self.assertEqual(target, 'AEAREP-10032')
        posts = [entry for entry in self.server.seen if entry[0] == 'POST']
        self.assertEqual(posts[0][1], '/rest/api/2/issue/AEAREP-10032/comment')
        self.assertEqual(posts[0][2], {'body': 'from the compute node'})


class TestParseArgs(unittest.TestCase):
    def test_flags_and_positionals(self):
        options = jac.parse_args(
            ['--partb', '--slurm', '--status', 'completed', '--exit-code', '2',
             'AEAREP-100', 'some text']
        )
        self.assertTrue(options['partb'])
        self.assertTrue(options['slurm'])
        self.assertEqual(options['status'], 'completed')
        self.assertEqual(options['exit_code'], 2)
        self.assertEqual(options['positional'], ['AEAREP-100', 'some text'])

    def test_backwards_compatible_two_positional_form(self):
        options = jac.parse_args(['AEAREP-100', 'Pipeline completed'])
        self.assertFalse(options['partb'])
        self.assertEqual(options['positional'], ['AEAREP-100', 'Pipeline completed'])

    def test_double_dash_ends_options(self):
        options = jac.parse_args(['--partb', '--', 'AEAREP-100', '--not-an-option'])
        self.assertTrue(options['partb'])
        self.assertEqual(options['positional'], ['AEAREP-100', '--not-an-option'])

    def test_repeated_env_file(self):
        options = jac.parse_args(['--env-file', 'a', '--env-file', 'b', 'AEAREP-1', 'x'])
        self.assertEqual(options['env_files'], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
