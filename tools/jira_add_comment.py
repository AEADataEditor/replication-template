#!/usr/bin/env python3
"""
Post a comment to a Jira issue (optionally to its "Part B ..." sub-task).

Usage:
    python3 jira_add_comment.py [options] <issue-key|auto> [comment]

Arguments:
    issue-key   Jira issue key (e.g., AEAREP-8885 or aearep-8885).
                Use the literal string "auto" to resolve the ticket from the
                $jiraticket environment variable or from config.yml.
    comment     Comment text (Jira wiki markup supported). Optional when
                --status is given.

Options:
    --partb            Post to the "Part B ..." sub-task of <issue-key> instead
                       of to <issue-key> itself. If <issue-key> is already the
                       Part B sub-task, it is used as-is; if it is some other
                       sub-task, its parent's Part B sub-task is used. Falls
                       back to <issue-key> (with a warning) if no Part B
                       sub-task exists.
    --status STATUS    Prepend a standard status line. Known values:
                       "started", "completed", "failed"; anything else is used
                       verbatim.
    --exit-code N      Used with --status: a non-zero N turns "completed" into
                       "failed" and appends the exit code. Lets a single call
                       report both success and failure from a shell trap.
    --label TEXT       What --status is talking about (default: "Job"), e.g.
                       "SLURM job main.do". Ignored in favor of "SLURM job
                       <id> <name>" when --slurm is given and SLURM_JOB_ID is
                       set.
    --slurm            Fold the SLURM job ID, job name and submit directory
                       into the status line (e.g. "SLURM job 590340 main.do
                       completed (directory: /path/to/submit/dir)"). Without
                       --status the same context is added as a line of its own.
                       Silently omitted when not running under SLURM.
    --env-file PATH    Read credentials from PATH in addition to the default
                       locations (may be repeated).
    --dry-run          Resolve the target issue and print the comment that
                       would be posted, without posting it.
    --                 End of options; everything after it is positional.
    -h, --help         Show this help.

Output:
    Prints confirmation to stdout on success
    Prints warning to stderr on failure (non-fatal; always exits 0)

Credentials:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

    Looked up, in order of precedence:
      1. the process environment
      2. --env-file PATH (in the order given)
      3. ./.env
      4. ./.envvars
      5. ~/.envvars
      6. ~/envvars.txt
      7. ~/.env
    Files are parsed as simple KEY=value lines; a leading "export " and
    surrounding quotes are stripped, "#" comments and blank lines are ignored.

Dependencies:
    Uses the `jira` package when it is importable, and otherwise falls back to
    the Jira REST API over the standard library, so that the script also runs
    on machines (e.g. HPC compute nodes) where nothing has been pip-installed.
"""

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

try:
    from jira import JIRA
    _JIRA_LIB = True
except Exception:  # pragma: no cover - depends on the local install
    _JIRA_LIB = False

JIRA_SERVER = "https://aeadataeditors.atlassian.net"

# Sub-task issue type used for Part B work; matched case-insensitively on the
# issue type *name*, which in AEAREP is
# "Part B processing: run code or complete report".
PART_B_TYPE_PREFIX = "part b"

# Secondary match: some Part B sub-tasks carry a different issue type
# (e.g. "Author-generated reproducibility check") but say "Part B" in the
# summary ("Prepare Part B (SIVACOR)").
PART_B_SUMMARY_MARKER = "part b"

ISSUE_KEY_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*-\d+$')

ENV_KEYS = ('JIRA_USERNAME', 'JIRA_API_KEY')


# --------------------------------------------------------------------------
# Credentials
# --------------------------------------------------------------------------

def parse_env_file(path):
    """Parse a shell-style KEY=value file. Returns a dict (empty on any error)."""
    values = {}
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('export '):
                    line = line[len('export '):].strip()
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                if not key:
                    continue
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                values[key] = value
    except Exception:
        return {}
    return values


def candidate_env_files(extra_files=None):
    """Return the credential files to consult, in order of precedence."""
    home = os.path.expanduser('~')
    files = list(extra_files or [])
    files += [
        os.path.join('.', '.env'),
        os.path.join('.', '.envvars'),
        os.path.join(home, '.envvars'),
        os.path.join(home, 'envvars.txt'),
        os.path.join(home, '.env'),
    ]
    return files


def get_credentials(extra_files=None):
    """
    Resolve (username, api_key) from the environment or credential files.

    The process environment wins; each file may supply whatever is still
    missing. Returns (None, None) if either value cannot be found.
    """
    found = {}
    for key in ENV_KEYS:
        value = os.environ.get(key)
        if value:
            found[key] = value

    for path in candidate_env_files(extra_files):
        if all(key in found for key in ENV_KEYS):
            break
        if not os.path.isfile(path):
            continue
        values = parse_env_file(path)
        for key in ENV_KEYS:
            if key not in found and values.get(key):
                found[key] = values[key]

    if all(key in found for key in ENV_KEYS):
        return found['JIRA_USERNAME'], found['JIRA_API_KEY']
    return None, None


# --------------------------------------------------------------------------
# Jira clients
# --------------------------------------------------------------------------

def _normalize_issue(fields, key):
    """Reduce a Jira issue payload to the handful of fields we care about."""
    subtasks = []
    for sub in (fields.get('subtasks') or []):
        sub_fields = sub.get('fields') or {}
        subtasks.append({
            'key': sub.get('key', ''),
            'summary': (sub_fields.get('summary') or ''),
            'issuetype': ((sub_fields.get('issuetype') or {}).get('name') or ''),
        })
    parent = fields.get('parent') or {}
    return {
        'key': key,
        'summary': fields.get('summary') or '',
        'issuetype': ((fields.get('issuetype') or {}).get('name') or ''),
        'parent': parent.get('key') or None,
        'subtasks': subtasks,
    }


class RestClient:
    """Minimal Jira REST v2 client built on the standard library only."""

    FIELDS = 'summary,issuetype,parent,subtasks'

    def __init__(self, username, api_key, server=JIRA_SERVER):
        self.server = server.rstrip('/')
        token = base64.b64encode(
            '{0}:{1}'.format(username, api_key).encode('utf-8')
        ).decode('ascii')
        self.headers = {
            'Authorization': 'Basic ' + token,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _request(self, method, path, payload=None):
        url = self.server + path
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        for name, value in self.headers.items():
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as error:
            # Jira puts the useful part ("Issue does not exist", "Unauthorized")
            # in the response body, which str(HTTPError) does not show.
            detail = ''
            try:
                detail = error.read().decode('utf-8', errors='replace').strip()
            except Exception:
                pass
            raise RuntimeError(
                "HTTP {0} from {1}{2}".format(
                    error.code, path.split('?')[0], ': ' + detail[:300] if detail else ''
                )
            )
        return json.loads(body) if body else {}

    def get_issue(self, issue_key):
        payload = self._request(
            'GET', '/rest/api/2/issue/{0}?fields={1}'.format(issue_key, self.FIELDS)
        )
        return _normalize_issue(payload.get('fields') or {}, payload.get('key', issue_key))

    def add_comment(self, issue_key, comment):
        self._request(
            'POST', '/rest/api/2/issue/{0}/comment'.format(issue_key), {'body': comment}
        )


class LibraryClient:
    """Client backed by the `jira` package, matching RestClient's interface."""

    FIELDS = RestClient.FIELDS

    def __init__(self, username, api_key, server=JIRA_SERVER):
        self.jira = JIRA(
            server=server,
            basic_auth=(username, api_key),
            options={'verify': True},
        )

    def get_issue(self, issue_key):
        issue = self.jira.issue(issue_key, fields=self.FIELDS)
        return _normalize_issue(issue.raw.get('fields') or {}, issue.key)

    def add_comment(self, issue_key, comment):
        self.jira.add_comment(issue_key, comment)


def get_jira_client(extra_files=None):
    """Return an authenticated client, or None if credentials are unavailable."""
    username, api_key = get_credentials(extra_files)
    if not username or not api_key:
        return None

    if _JIRA_LIB:
        try:
            return LibraryClient(username, api_key)
        except Exception as exc:
            print(
                "Warning: jira library client failed ({0}), falling back to REST".format(exc),
                file=sys.stderr,
            )
    try:
        return RestClient(username, api_key)
    except Exception:
        return None


# --------------------------------------------------------------------------
# Ticket resolution
# --------------------------------------------------------------------------

def find_config_yml(start_dir=None, levels=4):
    """Look for config.yml in start_dir and up to `levels` parent directories."""
    current = os.path.abspath(start_dir or os.environ.get('SLURM_SUBMIT_DIR') or '.')
    for _ in range(levels + 1):
        candidate = os.path.join(current, 'config.yml')
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def ticket_from_config(path):
    """Read the `jiraticket:` value out of a config.yml. Returns '' if absent."""
    if not path:
        return ""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as handle:
            for line in handle:
                match = re.match(r'^\s*jiraticket\s*:\s*(.*?)\s*$', line)
                if match:
                    return match.group(1).strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def resolve_issue_key(issue_key):
    """
    Turn the issue-key argument into a real key.

    "auto" (or an empty argument) resolves from $jiraticket, then from the
    nearest config.yml. Returns '' when nothing can be resolved.
    """
    if issue_key and issue_key.strip().lower() != 'auto':
        return issue_key.strip()

    candidate = (os.environ.get('jiraticket') or os.environ.get('JIRATICKET') or '').strip()
    if candidate:
        return candidate

    return ticket_from_config(find_config_yml())


def _is_part_b(issuetype, summary):
    """True when an issue type (preferred) or summary marks this as Part B."""
    if (issuetype or '').strip().lower().startswith(PART_B_TYPE_PREFIX):
        return True
    return PART_B_SUMMARY_MARKER in (summary or '').strip().lower()


def _issue_number(key):
    """Numeric part of an issue key, for picking the newest of several matches."""
    match = re.search(r'-(\d+)$', key or '')
    return int(match.group(1)) if match else -1


def find_part_b_subtask(client, issue_key):
    """
    Find the "Part B ..." sub-task associated with issue_key.

    Returns the sub-task key, or '' when there is none (the caller then falls
    back to issue_key itself). Handles being handed the Part B sub-task
    directly, or a sibling sub-task of the same parent.
    """
    try:
        issue = client.get_issue(issue_key)
    except Exception as exc:
        print(
            "Warning: could not read {0} to locate its Part B sub-task: {1}".format(issue_key, exc),
            file=sys.stderr,
        )
        return ""

    # Already the Part B sub-task (match on issue type only: a parent ticket
    # can easily mention "Part B" in its summary).
    if (issue['issuetype'] or '').strip().lower().startswith(PART_B_TYPE_PREFIX):
        return issue['key']

    parent_issue = issue
    if issue['parent']:
        try:
            parent_issue = client.get_issue(issue['parent'])
        except Exception as exc:
            print(
                "Warning: could not read parent {0}: {1}".format(issue['parent'], exc),
                file=sys.stderr,
            )
            return ""

    # Prefer an issue-type match; only then fall back to the summary marker.
    for matcher in (
        lambda s: (s['issuetype'] or '').strip().lower().startswith(PART_B_TYPE_PREFIX),
        lambda s: _is_part_b(s['issuetype'], s['summary']),
    ):
        matches = [s['key'] for s in parent_issue['subtasks'] if matcher(s) and s['key']]
        if matches:
            return sorted(matches, key=_issue_number)[-1]

    return ""


# --------------------------------------------------------------------------
# Comment composition
# --------------------------------------------------------------------------

STATUS_MARKERS = {
    'started': ('🚀', 'started'),
    'completed': ('✅', 'completed'),
    'failed': ('❌', 'failed'),
}


def status_line(status, exit_code=None, label=None):
    """Build the leading status line for --status."""
    status = (status or '').strip().lower()
    if exit_code is not None and status == 'completed':
        status = 'completed' if exit_code == 0 else 'failed'

    emoji, verb = STATUS_MARKERS.get(status, ('ℹ️', status))
    line = "{0} {1} {2}".format(emoji, label or 'Job', verb)
    if exit_code is not None and exit_code != 0:
        line += " (exit code {0})".format(exit_code)
    return line


def slurm_label(default_label=None):
    """
    'SLURM job <id> <name>' when running under SLURM, else default_label
    unchanged.
    """
    job_id = os.environ.get('SLURM_JOB_ID')
    if not job_id:
        return default_label
    job_name = os.environ.get('SLURM_JOB_NAME') or ''
    return "SLURM job {0} {1}".format(job_id, job_name).strip() if job_name \
        else "SLURM job {0}".format(job_id)


def slurm_directory_suffix():
    """' (directory: ...)' when SLURM_SUBMIT_DIR is set, else ''."""
    directory = os.environ.get('SLURM_SUBMIT_DIR')
    return " (directory: {0})".format(directory) if directory else ""


def compose_comment(comment=None, status=None, exit_code=None, label=None, slurm=False):
    """Assemble the comment body from the status line, free text, and context."""
    parts = []
    if status:
        line = status_line(status, exit_code, slurm_label(label) if slurm else label)
        if slurm:
            line += slurm_directory_suffix()
        parts.append(line)
    if comment:
        parts.append(comment)
    if slurm and not status:
        # Without --status there is no line to fold the job context into, so
        # give it one of its own rather than dropping it silently.
        context = slurm_label(None)
        if context:
            parts.append(context + slurm_directory_suffix())
    return "\n\n".join(part for part in parts if part)


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def add_comment(issue_key, comment, partb=False, extra_files=None, dry_run=False):
    """
    Post `comment` to `issue_key`, or to its Part B sub-task when partb is set.

    Never raises and never fails the caller: problems are reported on stderr.
    Returns the key actually commented on, or '' when nothing was posted.
    """
    issue_key = resolve_issue_key(issue_key)
    if not issue_key:
        print("Warning: no Jira ticket given or resolvable, skipping comment", file=sys.stderr)
        return ""

    issue_key = issue_key.upper()
    if not ISSUE_KEY_RE.match(issue_key):
        print("Warning: '{0}' is not a Jira issue key, skipping comment".format(issue_key),
              file=sys.stderr)
        return ""

    client = get_jira_client(extra_files)
    if not client:
        if dry_run:
            # Still show the plumbing (ticket + comment body) so that a caller
            # can be tested on a machine without credentials.
            print("Would post to {0} (credentials unavailable, Part B sub-task "
                  "not resolved):".format(issue_key))
            print(comment)
            return issue_key
        print("Warning: Jira credentials not available, skipping comment", file=sys.stderr)
        return ""

    target = issue_key
    if partb:
        part_b = find_part_b_subtask(client, issue_key)
        if part_b:
            target = part_b.upper()
        else:
            print(
                "Warning: no Part B sub-task found for {0}, commenting on it directly".format(
                    issue_key),
                file=sys.stderr,
            )

    if dry_run:
        print("Would post to {0}:".format(target))
        print(comment)
        return target

    try:
        client.add_comment(target, comment)
        print("Jira comment posted to {0}".format(target))
        return target
    except Exception as exc:
        print("Warning: Could not post Jira comment to {0}: {1}".format(target, exc),
              file=sys.stderr)
        return ""


def usage(stream=sys.stderr):
    print("Usage: jira_add_comment.py [--partb] [--status STATUS] [--exit-code N] "
          "[--label TEXT] [--slurm] [--env-file PATH] [--dry-run] "
          "<issue-key|auto> [comment]", file=stream)
    print("Environment: JIRA_USERNAME, JIRA_API_KEY "
          "(or ./.env, ./.envvars, ~/.envvars, ~/envvars.txt, ~/.env)", file=stream)


def parse_args(argv):
    """Parse the command line by hand (argparse would eat leading '-' comments)."""
    options = {
        'partb': False,
        'status': None,
        'exit_code': None,
        'label': None,
        'slurm': False,
        'env_files': [],
        'dry_run': False,
        'positional': [],
    }
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == '--':
            options['positional'].extend(argv[index + 1:])
            break
        if argument in ('-h', '--help'):
            usage(sys.stdout)
            sys.exit(0)
        elif argument == '--partb':
            options['partb'] = True
        elif argument == '--slurm':
            options['slurm'] = True
        elif argument == '--dry-run':
            options['dry_run'] = True
        elif argument in ('--status', '--exit-code', '--label', '--env-file'):
            index += 1
            if index >= len(argv):
                print("Error: {0} needs a value".format(argument), file=sys.stderr)
                usage()
                sys.exit(1)
            value = argv[index]
            if argument == '--status':
                options['status'] = value
            elif argument == '--label':
                options['label'] = value
            elif argument == '--env-file':
                options['env_files'].append(value)
            else:
                try:
                    options['exit_code'] = int(value)
                except ValueError:
                    print("Error: --exit-code needs an integer", file=sys.stderr)
                    sys.exit(1)
        elif argument.startswith('--'):
            print("Error: unknown option {0}".format(argument), file=sys.stderr)
            usage()
            sys.exit(1)
        else:
            options['positional'].append(argument)
        index += 1
    return options


def main():
    options = parse_args(sys.argv[1:])
    positional = options['positional']

    if not positional:
        usage()
        sys.exit(1)

    issue_key = positional[0]
    free_text = positional[1] if len(positional) > 1 else None

    if free_text is None and not options['status']:
        usage()
        sys.exit(1)

    comment = compose_comment(
        comment=free_text,
        status=options['status'],
        exit_code=options['exit_code'],
        label=options['label'],
        slurm=options['slurm'],
    )
    if not comment:
        print("Warning: empty comment, nothing to post", file=sys.stderr)
        return

    add_comment(
        issue_key,
        comment,
        partb=options['partb'],
        extra_files=options['env_files'],
        dry_run=options['dry_run'],
    )


if __name__ == '__main__':
    main()
