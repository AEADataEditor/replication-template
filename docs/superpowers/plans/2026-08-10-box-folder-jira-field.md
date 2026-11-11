# Jira-driven Box Folder ID Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the restricted-data Box download pipeline use a Box folder ID recorded on the Jira ticket ("Restricted data Box Folder ID") when present, fall back to the existing name-search when it isn't, persist a newly-discovered ID back into `config.yml`, and notify the ticket via a generalized comment-diff mechanism.

**Architecture:** Two small, independently-testable Python tool changes (`download_box_private.py` gets a direct-ID bypass, `jira_get_info.py` gets a new read keyword). Two shell changes: `automations/60_process_restricted_box.sh` becomes the pipeline-wired orchestrator (first as a pure refactor commit, then augmented with the Jira-aware logic), and `automations/70_publish_comment.sh` gains a generic `--config` mode that diffs and comments on `config.yml` changes. `bitbucket-pipelines.yml` step 8 is updated to call these.

**Tech Stack:** Python 3 (`boxsdk`, `jira` packages, already in `requirements.txt`), Bash, Bitbucket Pipelines YAML, `unittest`.

## Global Constraints

- Jira credentials: `JIRA_USERNAME`, `JIRA_API_KEY` (existing convention across all `tools/jira_*.py`).
- Box credentials: `BOX_FOLDER_PRIVATE`, `BOX_PRIVATE_KEY_ID`, `BOX_ENTERPRISE_ID`, etc. (existing convention in `download_box_private.py`).
- The "Restricted data Box Folder ID" Jira field holds a raw Box folder ID (a numeric string), not a URL.
- No Jira **writes** happen from `automations/60_process_restricted_box.sh` — only reads and `config.yml` writes. All Jira writes (comments) happen from `bitbucket-pipelines.yml` via `automations/70_publish_comment.sh`.
- Follow existing repo conventions: Jira tools live in `tools/jira_*.py` and are read via `os.environ.get('JIRA_USERNAME')` / `os.environ.get('JIRA_API_KEY')`, constructing `JIRA(server="https://aeadataeditors.atlassian.net", basic_auth=(...), options={'verify': True})`.
- Shell scripts in this repo are not covered by automated tests; verify them by tracing logic and running with stubbed dependencies, per `docs/superpowers/specs/2026-08-10-box-folder-jira-field-design.md`.

---

### Task 1: `download_box_private.py` — direct folder-ID bypass

**Files:**
- Modify: `tools/download_box_private.py`
- Test: `tools/test_download_box_private.py` (new)

**Interfaces:**
- Produces: new CLI flag `--target-folder-id ID` on `download_box_private.py`. When set, `args.target_folder_id` is a non-empty string and the `subfolder` search is skipped. In both the direct-ID and search paths, the resolved folder ID is printed to stdout as `BOX_FOLDER_ID=<id>` before download begins. This stdout marker is consumed by Task 5's `60_process_restricted_box.sh` changes.

- [ ] **Step 1: Write the failing tests**

Create `tools/test_download_box_private.py`:

```python
#!/usr/bin/env python3
"""Tests for download_box_private.py. Run: python3 tools/test_download_box_private.py"""
import argparse
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_box_private as dbp


class TestParseArgumentsTargetFolderId(unittest.TestCase):
    def _parse(self, argv):
        with patch.object(sys, "argv", ["download_box_private.py"] + argv):
            return dbp.parse_arguments()

    def test_target_folder_id_defaults_to_none(self):
        args = self._parse([
            "1234",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertIsNone(args.target_folder_id)

    def test_target_folder_id_is_captured(self):
        args = self._parse([
            "--target-folder-id", "555666",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertEqual(args.target_folder_id, "555666")

    def test_target_folder_id_makes_subfolder_optional(self):
        # No positional subfolder, no cwd/git-remote match expected to be needed
        # because --target-folder-id makes the subfolder argument moot.
        args = self._parse([
            "--target-folder-id", "555666",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertEqual(args.target_folder_id, "555666")


class TestResolveTargetFolderId(unittest.TestCase):
    """resolve_target_folder_id() centralizes the direct-ID vs search decision."""

    def test_direct_id_skips_search(self):
        client = MagicMock()
        result = dbp.resolve_target_folder_id(client, target_folder_id="555666", box_folder_id="999", subfolder=None)
        self.assertEqual(result, "555666")
        client.folder.assert_not_called()

    def test_search_used_when_no_target_folder_id(self):
        client = MagicMock()
        folder_items = MagicMock()
        folder_items.get_items.return_value = [
            MagicMock(type="folder", name="aearep-1234", id="42"),
        ]
        client.folder.return_value = folder_items

        result = dbp.resolve_target_folder_id(client, target_folder_id=None, box_folder_id="999", subfolder="1234")

        self.assertEqual(result, "42")

    def test_search_raises_when_subfolder_not_found(self):
        client = MagicMock()
        folder_items = MagicMock()
        folder_items.get_items.return_value = [
            MagicMock(type="folder", name="aearep-0000", id="42"),
        ]
        client.folder.return_value = folder_items

        with self.assertRaises(SystemExit):
            dbp.resolve_target_folder_id(client, target_folder_id=None, box_folder_id="999", subfolder="1234")

    def test_prints_box_folder_id_marker(self):
        client = MagicMock()
        buf = io.StringIO()
        with redirect_stdout(buf):
            dbp.resolve_target_folder_id(client, target_folder_id="555666", box_folder_id="999", subfolder=None)
        self.assertIn("BOX_FOLDER_ID=555666", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 test_download_box_private.py -v`
Expected: `AttributeError: module 'download_box_private' has no attribute 'target_folder_id'` (or similar — `resolve_target_folder_id` doesn't exist yet, `--target-folder-id` isn't a recognized flag).

- [ ] **Step 3: Add `--target-folder-id` to argument parsing**

In `tools/download_box_private.py`, in `parse_arguments()` (after the `--output-dir` argument, around line 186), add:

```python
    parser.add_argument('--target-folder-id',
                        default=None,
                        help='Box folder ID to download from directly, bypassing the aearep-<subfolder> search entirely.')
```

- [ ] **Step 4: Extract the folder-resolution logic into `resolve_target_folder_id()`**

Replace the subfolder-resolution block inside `main()` (currently lines 392-420 — the `# Determine target folder ID` section through the `if not found:` block) with a call to a new top-level function. Add this function above `main()`, after `download_folder()`:

```python
def resolve_target_folder_id(client, target_folder_id, box_folder_id, subfolder):
    """
    Determine which Box folder ID to download from.

    If target_folder_id is given, it is used directly and no search is
    performed. Otherwise, box_folder_id's immediate children are searched
    for a folder matching "aearep-<subfolder>" (or bare <subfolder> as a
    fallback), matching the pre-existing search behavior.

    Prints "BOX_FOLDER_ID=<id>" to stdout once the ID is known, so callers
    can capture it regardless of which path was taken.

    Exits the process with status 1 if a search was required but no
    matching subfolder was found.
    """
    if target_folder_id:
        logger.info(f"Using explicit target folder ID: {target_folder_id}")
        print(f"BOX_FOLDER_ID={target_folder_id}")
        return target_folder_id

    resolved = box_folder_id
    if subfolder:
        bare = subfolder
        prefixed = bare if bare.startswith('aearep-') else f'aearep-{bare}'
        search_terms = [prefixed, bare] if prefixed != bare else [prefixed]

        logger.info(f"Looking for subfolder matching one of: {search_terms}")
        try:
            items = list(client.folder(folder_id=resolved).get_items())
            found = False
            for search_term in search_terms:
                for item in items:
                    if item.type == 'folder' and search_term in item.name:
                        resolved = item.id
                        logger.info(f"Found subfolder: {item.name} (ID: {item.id})")
                        found = True
                        break
                if found:
                    break
            if not found:
                logger.error(f"Subfolder matching {search_terms} not found. Exiting.")
                sys.exit(1)
        except BoxAPIException as e:
            logger.error(f"Error accessing Box folder: {e}")
            sys.exit(1)

    print(f"BOX_FOLDER_ID={resolved}")
    return resolved
```

Then in `main()`, replace the old inline block with:

```python
    target_folder_id = resolve_target_folder_id(
        client, args.target_folder_id, args.box_folder_id, args.subfolder
    )
```

Note: `args.subfolder` must become optional now that `--target-folder-id` can stand in for it. In `parse_arguments()`, the existing auto-detect fallback (cwd dirname / git remote) and the final "Check for required arguments" block only require `subfolder` indirectly (via `parser.error` if not found) — leave that logic as-is; it still runs and still tries to populate `args.subfolder` when missing, but it no longer matters when `--target-folder-id` is supplied. Add a guard right after the existing auto-detect block (after the `else:` branch that calls `parser.error(...)` around line 210) so that branch doesn't error out when `--target-folder-id` was given:

```python
    # If subfolder not provided, try to extract from current directory name
    if not args.subfolder and not args.target_folder_id:
        current_dir = os.path.basename(os.getcwd())
        match = re.match(r'^aearep-(\d+)$', current_dir)
        if match:
            args.subfolder = match.group(1)
            logger.info(f"Auto-detected subfolder '{args.subfolder}' from current directory '{current_dir}'")
        else:
            logger.info(f"Current directory '{current_dir}' does not match pattern 'aearep-NNNN', trying git remote...")
            repo_number = get_repo_name_from_git_remote()
            if repo_number:
                args.subfolder = repo_number
                logger.info(f"Auto-detected subfolder '{args.subfolder}' from git remote")
            else:
                parser.error(f"SUBFOLDER argument not provided and could not auto-detect from directory name or git remote")
```

(This replaces the existing `if not args.subfolder:` block — the only change is the added `and not args.target_folder_id` guard on the outer condition.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tools && python3 test_download_box_private.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/download_box_private.py tools/test_download_box_private.py
git commit -m "$(cat <<'EOF'
Add --target-folder-id bypass to download_box_private.py

Lets a caller download directly from a known Box folder ID, skipping
the aearep-<subfolder> name search. Prints BOX_FOLDER_ID=<id> so
callers can capture whichever ID was actually used.
EOF
)"
```

---

### Task 2: `jira_get_info.py` — `boxfolderid` keyword

**Files:**
- Modify: `tools/jira_get_info.py`
- Test: `tools/test_jira_get_info.py` (new)

**Interfaces:**
- Produces: `get_info_from_jira(issue_key, keyword='boxfolderid')` returns the "Restricted data Box Folder ID" field value (stripped string, or `""`). CLI: `python3 jira_get_info.py <issue-key> boxfolderid`. Consumed by Task 5.

- [ ] **Step 1: Write the failing test**

Create `tools/test_jira_get_info.py`:

```python
#!/usr/bin/env python3
"""Tests for jira_get_info.py. Run: python3 tools/test_jira_get_info.py"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_get_info as jgi


class TestGetBoxFolderId(unittest.TestCase):
    FIELD_MAP = {"Restricted data Box Folder ID": "customfield_99999"}

    def _issue(self, value):
        issue = MagicMock()
        setattr(issue.fields, "customfield_99999", value)
        return issue

    def test_returns_stripped_value_when_present(self):
        issue = self._issue("  123456  ")
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "123456")

    def test_returns_empty_string_when_none(self):
        issue = self._issue(None)
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "")

    def test_returns_empty_string_when_blank(self):
        issue = self._issue("   ")
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "")

    def test_returns_empty_string_when_field_unmapped(self):
        issue = self._issue("123456")
        self.assertEqual(jgi.get_box_folder_id(issue, {}), "")


class TestKeywordRouting(unittest.TestCase):
    def test_boxfolderid_keyword_is_routed(self):
        field_map = TestGetBoxFolderId.FIELD_MAP
        issue = MagicMock()
        setattr(issue.fields, "customfield_99999", "654321")

        jira = MagicMock()
        jira.issue.return_value = issue
        jira.fields.return_value = [
            {"name": "Restricted data Box Folder ID", "id": "customfield_99999"}
        ]

        with unittest.mock.patch.object(jgi, "get_jira_client", return_value=jira):
            result = jgi.get_info_from_jira("AEAREP-1", "boxfolderid")

        self.assertEqual(result, "654321")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools && python3 test_jira_get_info.py -v`
Expected: `AttributeError: module 'jira_get_info' has no attribute 'get_box_folder_id'`

- [ ] **Step 3: Implement `get_box_folder_id()` and wire it into the keyword dispatch**

In `tools/jira_get_info.py`, add this function after `get_openicpsr_project_number()` (after line 253):

```python
def get_box_folder_id(issue, field_map):
    """
    Get Restricted data Box Folder ID from JIRA issue.

    Returns:
        Box folder ID if found, empty string otherwise
    """
    box_folder_id = get_field_value(issue, field_map, 'Restricted data Box Folder ID')

    if box_folder_id and str(box_folder_id).strip():
        return str(box_folder_id).strip()

    return ""
```

In `get_info_from_jira()`, add a branch (after the `replicationurl` branch, before `else:`):

```python
        elif keyword_lower == 'boxfolderid':
            return get_box_folder_id(issue, field_map)
```

Update the module docstring's `Keywords:` list (near the top of the file) and `print_help()`'s `Available Keywords:` list to include:

```
    boxfolderid  - Restricted data Box Folder ID
```

Update the two "Available keywords: ..." strings (in `print_help()` and in `main()`'s usage error message) to append `, boxfolderid`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools && python3 test_jira_get_info.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/jira_get_info.py tools/test_jira_get_info.py
git commit -m "$(cat <<'EOF'
Add boxfolderid keyword to jira_get_info.py

Reads the "Restricted data Box Folder ID" field so callers can check
whether a ticket already has a known Box folder before falling back
to name-based search.
EOF
)"
```

---

### Task 3: Stage 1 — move pipeline step 8's logic into `automations/60_process_restricted_box.sh` (parity refactor)

**Files:**
- Modify: `automations/60_process_restricted_box.sh` (full rewrite)
- Modify: `bitbucket-pipelines.yml:420-422`

**Interfaces:**
- Produces: `automations/60_process_restricted_box.sh <repository_name> [directory=restricted] [tag=directory]` — behaves exactly as pipeline step 8 currently does inline (download by name, unpack, create manifest). No Jira/`config.yml` awareness yet — that's Task 5.

This task intentionally changes *only* where the logic lives, not what it does, so the diff is easy to review on its own (per the design doc's two-stage rollout).

- [ ] **Step 1: Rewrite `automations/60_process_restricted_box.sh`**

Replace the entire file with:

```bash
#!/bin/bash
#set -ev

# 60_process_restricted_box.sh
# Downloads files from the restricted Box folder and runs the 02 manifest
# creation code. This is the script wired into the "8-download-box-manifest"
# Bitbucket pipeline step.
#
# Usage: 60_process_restricted_box.sh <repository_name> [directory] [tag]
#   repository_name - Numeric part of the aearep-NNNN repo name, used to
#                      find the matching subfolder on Box (e.g. 1234 for
#                      aearep-1234).
#   directory        - Directory where restricted data are downloaded to and
#                       read from (defaults to 'restricted').
#   tag              - Optional tag for output files (defaults to directory name).
#
# Environment Variables Required:
#   BOX_FOLDER_PRIVATE    - Box folder ID to download from
#   BOX_PRIVATE_KEY_ID    - Box JWT public key ID
#   BOX_ENTERPRISE_ID     - Box enterprise ID
#   BOX_PRIVATE_JSON      - Base64 encoded Box config JSON (optional, alternative to config file)

repository_name="${1:?Usage: $0 <repository_name> [directory] [tag]}"
directory=${2:-restricted}
tag=${3:-$directory}

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PYTHON_CMD="python"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "ERROR: No suitable Python installation found"
    exit 1
fi

echo "=== Processing restricted Box folder ==="
echo "Repository: $repository_name"
echo "Directory: $directory"
echo "Tag: $tag"

echo "Step 1: Downloading files from restricted Box folder (searching by name)..."
$PYTHON_CMD tools/download_box_private.py "$repository_name" --output-dir "$directory"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to download files from Box"
    exit 1
fi

echo "Step 2: Unpacking downloaded files..."
bash automations/00_unpack_zip.sh "$directory"

echo "Step 3: Running manifest creation..."
bash automations/02_create_manifest.sh "$directory" "$tag"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create manifest for directory '$directory'"
    exit 1
fi

echo "=== Successfully processed restricted data ==="
echo "Directory processed: $directory"
echo "Tag used: $tag"
```

- [ ] **Step 2: Verify the script's shell syntax**

Run: `bash -n automations/60_process_restricted_box.sh`
Expected: no output (syntax OK).

- [ ] **Step 3: Trace the script against the pipeline's current inline commands**

Confirm line-by-line that this reproduces pipeline step 8's current three commands (`python3 ./tools/download_box_private.py $repository_name`, `./automations/00_unpack_zip.sh restricted`, `./automations/02_create_manifest.sh restricted restricted`) when called as `automations/60_process_restricted_box.sh $repository_name` (directory/tag default to `restricted`). This is a manual read-through, not an automated check — note in the task tracker that this was confirmed.

- [ ] **Step 4: Update `bitbucket-pipelines.yml` step 8 to call the script**

In `bitbucket-pipelines.yml`, replace lines 420-422:

```yaml
            - python3 ./tools/download_box_private.py $repository_name
            - ./automations/00_unpack_zip.sh  restricted
            - ./automations/02_create_manifest.sh restricted restricted
```

with:

```yaml
            - ./automations/60_process_restricted_box.sh $repository_name
```

- [ ] **Step 5: Validate the YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('bitbucket-pipelines.yml'))"`
Expected: no output/no exception (valid YAML). (If `pyyaml` isn't installed, run `pip install -q pyyaml` first.)

- [ ] **Step 6: Commit**

```bash
git add automations/60_process_restricted_box.sh bitbucket-pipelines.yml
git commit -m "$(cat <<'EOF'
Wire 8-download-box-manifest through automations/60_process_restricted_box.sh

Moves the pipeline step's inline download/unpack/manifest commands into
the automations script, matching the repo convention of keeping
pipeline YAML thin. No behavior change — this is a pure refactor ahead
of adding Jira-aware folder resolution.
EOF
)"
```

---

### Task 4: `automations/70_publish_comment.sh` — generic `--config` mode

**Files:**
- Modify: `automations/70_publish_comment.sh`

**Interfaces:**
- Produces: `70_publish_comment.sh --config [pipeline-name] [extra-message]`. Posts a Jira comment containing the `git diff -- config.yml` output (wrapped in a `{code}` block) plus `extra-message` if given, and only if the diff is non-empty. No-ops (exit 0, no comment) when `config.yml` has no uncommitted diff. Consumed by Task 6 (pipeline wiring).

- [ ] **Step 1: Rewrite `automations/70_publish_comment.sh`**

Replace the whole file with:

```bash
#!/bin/bash
# 70_publish_comment.sh
# Post a status comment to the Jira issue associated with this repository,
# or (with --config) post a comment describing uncommitted config.yml changes.
# Ticket resolved in order: $jiraticket env var → config.yml → openICPSR directory detection.
#
# Usage:
#   70_publish_comment.sh [pipeline-name] [status]
#   70_publish_comment.sh --config [pipeline-name] [extra-message]
#
#   pipeline-name  Optional. Name of the Bitbucket custom pipeline (e.g., "1-populate-from-icpsr").
#                  No Bitbucket built-in variable exposes this; pass it explicitly from the pipeline.
#   status         Optional. Status of the pipeline: "started" or "completed" (default: "completed").
#   --config       Post a comment with the current uncommitted `git diff -- config.yml`
#                  instead of a status message. No-ops if there is no diff. Useful
#                  after any pipeline step that may have modified config.yml.
#   extra-message  Optional (only with --config). Extra text appended below the diff,
#                  e.g. a reminder tied to what changed.

_config_mode=""
if [ "$1" = "--config" ]; then
    _config_mode="true"
    shift
fi

_pipeline="${1:-}"

# Detect Python command
if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "70_publish_comment: no Python 3 found, skipping Jira notification"
    exit 0
fi

_jira="${jiraticket:-}"
echo "70_publish_comment: jiraticket from environment: '${_jira}'"

# Fall back to config.yml
if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "70_publish_comment: jiraticket from config.yml: '${_jira}'"
    else
        echo "70_publish_comment: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

# Fall back to directory-based lookup
if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "70_publish_comment: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "70_publish_comment: jiraticket from lookup: '${_jira}'"
    else
        echo "70_publish_comment: no openICPSR directory found"
    fi
fi

if [ -z "$_jira" ]; then
    echo "70_publish_comment: no Jira ticket found, skipping comment"
    exit 0
fi

if [ -n "$_config_mode" ]; then
    _extra_message="${2:-}"
    _diff=$(git diff -- config.yml)
    if [ -z "$_diff" ]; then
        echo "70_publish_comment: no uncommitted config.yml changes, skipping comment"
        exit 0
    fi
    _comment="config.yml updated:
{code}${_diff}{code}"
    if [ -n "$_extra_message" ]; then
        _comment="${_comment}

${_extra_message}"
    fi
    echo "70_publish_comment: posting config.yml diff comment to ${_jira}"
    $PYTHON_CMD tools/jira_add_comment.py "$_jira" "$_comment" || true
    exit 0
fi

_status="${2:-completed}"

case "$_status" in
    started)
        _emoji="🚀"
        _verb="started"
        ;;
    completed)
        _emoji="✅"
        _verb="completed"
        ;;
    *)
        _emoji="ℹ️"
        _verb="$_status"
        ;;
esac

_url="https://bitbucket.org/$BITBUCKET_WORKSPACE/$BITBUCKET_REPO_SLUG/pipelines/results/$BITBUCKET_BUILD_NUMBER"
echo "70_publish_comment: posting ${_verb} comment to ${_jira}"
$PYTHON_CMD tools/jira_add_comment.py "$_jira" \
    "${_emoji} Bitbucket Pipeline ${_pipeline} ${_verb}. Build [#$BITBUCKET_BUILD_NUMBER|$_url]." || true

exit 0
```

- [ ] **Step 2: Verify shell syntax**

Run: `bash -n automations/70_publish_comment.sh`
Expected: no output.

- [ ] **Step 3: Manually verify the `--config` no-op path**

```bash
cd /tmp && rm -rf publish-comment-test && mkdir publish-comment-test && cd publish-comment-test
git init -q
mkdir tools automations
cp /path/to/repo/tools/parse_yaml.sh tools/
cp /path/to/repo/automations/70_publish_comment.sh automations/
printf 'jiraticket: AEAREP-1\n' > config.yml
git add -A && git commit -q -m init
jiraticket=AEAREP-1 bash automations/70_publish_comment.sh --config test-pipeline
```

(Replace `/path/to/repo` with the actual worktree path.) Expected output ends with `70_publish_comment: no uncommitted config.yml changes, skipping comment` and the script does not attempt to call `jira_add_comment.py` (since there's no diff, it exits before that call — confirm by absence of any "posting config.yml diff comment" line).

- [ ] **Step 4: Manually verify the `--config` diff path (with a stub `jira_add_comment.py`)**

In the same throwaway directory:

```bash
mkdir tools 2>/dev/null
cat > tools/jira_add_comment.py <<'EOF'
#!/usr/bin/env python3
import sys
print("STUB CALLED WITH:", sys.argv[1:])
EOF
sed -i 's/^jiraticket:.*/jiraticket: AEAREP-1/' config.yml
echo 'boxfolderid: 555666' >> config.yml
jiraticket=AEAREP-1 bash automations/70_publish_comment.sh --config test-pipeline "Please verify Agreement signed."
```

Expected: a line starting `70_publish_comment: posting config.yml diff comment to AEAREP-1`, followed by `STUB CALLED WITH: ['AEAREP-1', 'config.yml updated:\n{code}...{code}\n\nPlease verify Agreement signed.']` showing the diff and extra message were included. Clean up: `cd / && rm -rf /tmp/publish-comment-test`.

- [ ] **Step 5: Commit**

```bash
git add automations/70_publish_comment.sh
git commit -m "$(cat <<'EOF'
Add --config mode to 70_publish_comment.sh

Posts a Jira comment containing the uncommitted `git diff -- config.yml`
(no-op if there is none), reusable by any pipeline step that modifies
config.yml, not just the Box folder ID lookup.
EOF
)"
```

---

### Task 5: Stage 2 — Jira-aware folder resolution in `automations/60_process_restricted_box.sh`

**Files:**
- Modify: `automations/60_process_restricted_box.sh`
- Modify: `config.yml`

**Interfaces:**
- Consumes: `tools/jira_get_info.py <issue-key> boxfolderid` (Task 2), `tools/download_box_private.py --target-folder-id ID` and its `BOX_FOLDER_ID=<id>` stdout marker (Task 1).
- Produces: the script now resolves `jiraticket`, checks the Jira field, and — only when it had to fall back to search — writes the discovered ID into a `boxfolderid:` key in `config.yml`. No Jira writes.

- [ ] **Step 1: Add the `boxfolderid:` key to `config.yml`**

In `config.yml`, add a new line after `jiraticket:`:

```yaml
openicpsr: 
osf:
dataverse:
zenodo:
jiraticket:
boxfolderid:
mcid: 
main:
stata18version: 2024-09-04
limitsize: 100
```

(Only the `boxfolderid:` line is new, inserted immediately after `jiraticket:`.)

- [ ] **Step 2: Augment `automations/60_process_restricted_box.sh`**

Replace the "Step 1: Downloading files..." block (the block added in Task 3, starting at `echo "Step 1: Downloading files from restricted Box folder (searching by name)..."` and ending at the `fi` that closes its error check) with:

```bash
_jira="${jiraticket:-}"
echo "60_process_restricted_box: jiraticket from environment: '${_jira}'"

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "60_process_restricted_box: jiraticket from config.yml: '${_jira}'"
    else
        echo "60_process_restricted_box: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "60_process_restricted_box: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "60_process_restricted_box: jiraticket from lookup: '${_jira}'"
    else
        echo "60_process_restricted_box: no openICPSR directory found"
    fi
fi

_box_folder_id=""
if [ -n "$_jira" ]; then
    _box_folder_id=$($PYTHON_CMD tools/jira_get_info.py "$_jira" boxfolderid 2>/dev/null || true)
    echo "60_process_restricted_box: boxfolderid from Jira ${_jira}: '${_box_folder_id}'"
fi

if [ -n "$_box_folder_id" ]; then
    echo "Step 1: Downloading files using known Box folder ID from Jira ($_box_folder_id)..."
    $PYTHON_CMD tools/download_box_private.py --target-folder-id "$_box_folder_id" --output-dir "$directory"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to download files from Box"
        exit 1
    fi
else
    echo "Step 1: Downloading files from restricted Box folder (searching by name)..."
    _download_output=$($PYTHON_CMD tools/download_box_private.py "$repository_name" --output-dir "$directory")
    _download_status=$?
    echo "$_download_output"
    if [ $_download_status -ne 0 ]; then
        echo "ERROR: Failed to download files from Box"
        exit 1
    fi
    _found_folder_id=$(echo "$_download_output" | grep '^BOX_FOLDER_ID=' | tail -1 | cut -d= -f2)
    if [ -n "$_found_folder_id" ] && [ -n "$_jira" ]; then
        echo "60_process_restricted_box: recording discovered Box folder ID '$_found_folder_id' in config.yml"
        if grep -q '^boxfolderid:' config.yml; then
            sed -i "s|^boxfolderid:.*|boxfolderid: ${_found_folder_id}|" config.yml
        else
            echo "boxfolderid: ${_found_folder_id}" >> config.yml
        fi
    fi
fi
```

- [ ] **Step 3: Verify shell syntax**

Run: `bash -n automations/60_process_restricted_box.sh`
Expected: no output.

- [ ] **Step 4: Manually verify the direct-ID path with stubbed tools**

```bash
cd /tmp && rm -rf box-script-test && mkdir box-script-test && cd box-script-test
mkdir tools automations generated
cp /path/to/repo/tools/parse_yaml.sh tools/
cp /path/to/repo/automations/60_process_restricted_box.sh automations/
printf 'jiraticket: AEAREP-1\nboxfolderid:\n' > config.yml

cat > tools/jira_get_info.py <<'EOF'
#!/usr/bin/env python3
print("999888")
EOF
cat > tools/download_box_private.py <<'EOF'
#!/usr/bin/env python3
import sys
print("STUB download_box_private.py called with:", sys.argv[1:], file=sys.stderr)
assert "--target-folder-id" in sys.argv, "expected direct-ID path"
assert "999888" in sys.argv, "expected the Jira-provided folder id"
EOF
cat > automations/00_unpack_zip.sh <<'EOF'
#!/bin/bash
echo "STUB unpack: $1"
EOF
cat > automations/02_create_manifest.sh <<'EOF'
#!/bin/bash
echo "STUB manifest: $1 $2"
EOF

jiraticket=AEAREP-1 bash automations/60_process_restricted_box.sh 1234 restricted restricted
echo "exit status: $?"
```

Expected: `boxfolderid from Jira AEAREP-1: '999888'`, then `Step 1: Downloading files using known Box folder ID from Jira (999888)...`, the stub's assertions pass silently, and the script prints `=== Successfully processed restricted data ===` with `exit status: 0`. `config.yml`'s `boxfolderid:` line stays empty (direct-ID path never writes it).

- [ ] **Step 5: Manually verify the search-fallback path writes `config.yml`**

In the same directory, reset for the fallback case:

```bash
printf 'jiraticket: AEAREP-1\nboxfolderid:\n' > config.yml

cat > tools/jira_get_info.py <<'EOF'
#!/usr/bin/env python3
# empty output = field not set
EOF
cat > tools/download_box_private.py <<'EOF'
#!/usr/bin/env python3
import sys
print("STUB download_box_private.py called with:", sys.argv[1:], file=sys.stderr)
assert "--target-folder-id" not in sys.argv, "expected search path, not direct-ID"
print("BOX_FOLDER_ID=777444")
EOF

jiraticket=AEAREP-1 bash automations/60_process_restricted_box.sh 1234 restricted restricted
echo "exit status: $?"
grep '^boxfolderid:' config.yml
```

Expected: `boxfolderid from Jira AEAREP-1: ''`, then `Step 1: Downloading files from restricted Box folder (searching by name)...`, then `BOX_FOLDER_ID=777444` echoed back, then `60_process_restricted_box: recording discovered Box folder ID '777444' in config.yml`, `exit status: 0`, and `grep '^boxfolderid:' config.yml` prints `boxfolderid: 777444`. Clean up: `cd / && rm -rf /tmp/box-script-test`.

- [ ] **Step 6: Commit**

```bash
git add automations/60_process_restricted_box.sh config.yml
git commit -m "$(cat <<'EOF'
Resolve Box folder ID from Jira before falling back to name search

automations/60_process_restricted_box.sh now resolves jiraticket and
checks the "Restricted data Box Folder ID" field. When set, it's used
directly; when empty, the existing name-search runs and the discovered
ID is recorded in config.yml's new boxfolderid key. No Jira writes
happen here -- that stays in the pipeline (see 70_publish_comment.sh
--config).
EOF
)"
```

---

### Task 6: Wire the config-change comment into pipeline step 8

**Files:**
- Modify: `bitbucket-pipelines.yml:404-426` (step `8-download-box-manifest`)

**Interfaces:**
- Consumes: `automations/70_publish_comment.sh --config` (Task 4).

- [ ] **Step 1: Update step 8 in `bitbucket-pipelines.yml`**

Current state after Task 3 (lines 404-424, prior to this task's edit):

```yaml
    8-download-box-manifest: #name of this pipeline
      - variables:          #list variable names under here
          - name: repository_name
      - step:
          image: python:3.12
          name: Download Box and create manifests
          caches:
            - pip
          script:
            - if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
            - chmod a+rx ./automations/*.sh
            - . ./tools/parse_yaml.sh
            - eval $(parse_yaml config.yml)
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; else echo "openICPSRID not set"; fi
            - chmod a+rx ./automations/*.sh
            - ./automations/70_publish_comment.sh 8-download-box-manifest started
            - ./automations/60_process_restricted_box.sh $repository_name
            - git add -f generated/*
            - git commit -m "[skip ci] Downloaded Box files and created manifests"
            - git push
            - ./automations/70_publish_comment.sh 8-download-box-manifest completed
```

Replace the `- git add -f generated/*` line and the two lines after it with:

```yaml
            - ./automations/70_publish_comment.sh --config 8-download-box-manifest "Please verify that 'Agreement signed' is correctly filled out."
            - git add -f generated/* config.yml
            - git commit -m "[skip ci] Downloaded Box files and created manifests"
            - git push
```

So the full script block becomes:

```yaml
          script:
            - if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
            - chmod a+rx ./automations/*.sh
            - . ./tools/parse_yaml.sh
            - eval $(parse_yaml config.yml)
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; else echo "openICPSRID not set"; fi
            - chmod a+rx ./automations/*.sh
            - ./automations/70_publish_comment.sh 8-download-box-manifest started
            - ./automations/60_process_restricted_box.sh $repository_name
            - ./automations/70_publish_comment.sh --config 8-download-box-manifest "Please verify that 'Agreement signed' is correctly filled out."
            - git add -f generated/* config.yml
            - git commit -m "[skip ci] Downloaded Box files and created manifests"
            - git push
            - ./automations/70_publish_comment.sh 8-download-box-manifest completed
```

Note: `eval $(parse_yaml config.yml)` (already present, line 416) populates `jiraticket` as a shell variable before `60_process_restricted_box.sh` runs, so the script's own env-var check picks it up without needing an explicit `export jiraticket` — Bitbucket Pipelines steps run their `script:` lines in the same shell, and `60_process_restricted_box.sh` is invoked via `./automations/...` (a child process), so `jiraticket` **does** need to be exported for the script to see it via `${jiraticket:-}`. Add `export jiraticket` immediately after the `eval $(parse_yaml config.yml)` line:

```yaml
            - eval $(parse_yaml config.yml)
            - export jiraticket
```

- [ ] **Step 2: Validate the YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('bitbucket-pipelines.yml'))"`
Expected: no output/no exception.

- [ ] **Step 3: Re-confirm the whole step 8 block reads correctly end to end**

Read back `bitbucket-pipelines.yml` lines 404-428 and confirm the sequence is: install deps, chmod, parse+eval config.yml, export jiraticket, resolve openICPSRID, started-comment, run 60_process_restricted_box.sh, config-diff comment, commit+push generated/* and config.yml, completed-comment. This is a manual read-through — note in the task tracker that this was confirmed.

- [ ] **Step 4: Commit**

```bash
git add bitbucket-pipelines.yml
git commit -m "$(cat <<'EOF'
Notify Jira when 8-download-box-manifest updates config.yml

Posts the config.yml diff (e.g. a newly-discovered Box folder ID)
via 70_publish_comment.sh --config, with a reminder to verify
'Agreement signed', and commits config.yml alongside the generated
manifest.
EOF
)"
```

---

## Post-implementation check

After all six tasks: run the full Python test suite once more to confirm nothing regressed.

```bash
cd tools && python3 -m pytest test_jira_update_software.py test_download_box_private.py test_jira_get_info.py -v
```

Expected: all tests across all three files PASS.
