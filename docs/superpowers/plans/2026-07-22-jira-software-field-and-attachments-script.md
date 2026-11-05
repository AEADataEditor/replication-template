# Jira Software-Used Automation + Attachments Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect the software used in a deposit from `04_list_program_files.sh`'s output and push newly-identified names into Jira's "Software used" field, and collapse the duplicated inline Jira-attachment download+commit logic in `bitbucket-pipelines.yml` into one reusable script.

**Architecture:** A data-driven extension/filename lookup (two CSVs) feeds a pure-logic resolver in `tools/jira_update_software.py`, which a thin `automations/26_update_jira_software.sh` wrapper invokes with a resolved Jira ticket and the deposit's `generated/programs-metadata.csv`. `.ipynb` files are resolved by inspecting their own kernel metadata, not by extension. Separately, `automations/30_download_jira_attachments.sh` is renamed to `automations/30_download_commit_jira_attachments.sh` and extended in place to also commit what it downloads, replacing two duplicated inline YAML blocks with one call each.

**Tech Stack:** Python 3 (stdlib `csv`/`json`/`argparse` + the existing `jira` package), Bash, `unittest` (stdlib — no new test dependency).

## Global Constraints

- Jira field: `customfield_10028`, display name "Software used", a *labels* array field (free-text, no fixed option list) on `https://aeadataeditors.atlassian.net`.
- Canonical software names already established by ~100 existing tickets: `Stata`, `MATLAB`, `R`, `SAS`, `Python`, `Dynare` — new values written by this feature must be capitalized the same way.
- Extension → software table (`tools/software-extensions.csv`), exact contents:
  ```
  extension,software
  ado,Stata
  do,Stata
  r,R
  rmd,R
  ox,Ox
  m,MATLAB
  py,Python
  sas,SAS
  jl,Julia
  f,Fortran
  f90,Fortran
  c,C/C++
  cpp,C/C++
  c++,C/C++
  h,C/C++
  nb,Mathematica
  fs,F#
  fsx,F#
  gss,GAUSS
  ```
  Deliberately absent: `sh`, `toml`, `yaml`, `yml`, `qmd`, `makefile` (no automatic mapping).
- Filename-override table (`tools/software-filenames.csv`), exact contents:
  ```
  filename,software
  Project.toml,Julia
  Manifest.toml,Julia
  ```
- `.ipynb` files are never looked up by extension — their language comes from the notebook's own `metadata.kernelspec.language` (falling back to `metadata.language_info.name`), mapped case-insensitively via `python`/`python3`→Python, `ir`/`r`→R, `julia`→Julia. Unrecognized/unreadable → not counted (never forced).
- Never write or run inline Python (`python3 -c "..."`) in `bitbucket-pipelines.yml` or in any shell script — this plan does not do it, and this constraint is also being added to `CLAUDE.md` for future work.
- Follow the existing `automations/NN_name.sh` (thin: argument/ticket resolution) + `tools/name.py` (real logic) pairing already used by `70_publish_comment.sh`→`jira_add_comment.py` and `30_download_commit_jira_attachments.sh`→`jira_download_attachments.py`. Never add a wrapper script whose only job is to call another script that already does the work — extend that script instead.
- No test harness exists anywhere in this repo today (`tests/`, `pytest`, etc. all absent) — new Python logic gets `unittest`-based tests colocated in `tools/`; new/changed shell scripts are verified manually (`bash -n` + a smoke run), matching the existing convention for `automations/*.sh`.

---

### Task 1: Lookup tables + pure resolution logic in `tools/jira_update_software.py`

**Files:**
- Create: `tools/software-extensions.csv`
- Create: `tools/software-filenames.csv`
- Create: `tools/jira_update_software.py` (partial: lookup loading, `.ipynb` detection, resolution, metadata CSV reading — no Jira/CLI yet)
- Test: `tools/test_jira_update_software.py`

**Interfaces:**
- Produces (used by Task 2 and by `automations/26_update_jira_software.sh` in Task 3):
  - `DEFAULT_EXT_LOOKUP: Path`, `DEFAULT_NAME_LOOKUP: Path` — module-level constants pointing at the two CSVs next to this file.
  - `load_csv_lookup(path: str | Path) -> dict[str, str]` — lower-cases the first CSV column as key.
  - `detect_ipynb_language(path: str | Path) -> str | None`
  - `resolve_software(filenames: list[str], project_dir: str | Path | None, ext_lookup: dict, name_lookup: dict) -> tuple[set[str], dict[str, int]]` — returns `(found_software, unmatched_counts_by_key)`.
  - `read_metadata_filenames(metadata_csv: str | Path) -> list[str]`

- [ ] **Step 1: Create the two lookup CSVs**

`tools/software-extensions.csv`:
```csv
extension,software
ado,Stata
do,Stata
r,R
rmd,R
ox,Ox
m,MATLAB
py,Python
sas,SAS
jl,Julia
f,Fortran
f90,Fortran
c,C/C++
cpp,C/C++
c++,C/C++
h,C/C++
nb,Mathematica
fs,F#
fsx,F#
gss,GAUSS
```

`tools/software-filenames.csv`:
```csv
filename,software
Project.toml,Julia
Manifest.toml,Julia
```

- [ ] **Step 2: Write the failing test file**

Create `tools/test_jira_update_software.py`:

```python
#!/usr/bin/env python3
"""Tests for jira_update_software.py. Run: python3 tools/test_jira_update_software.py"""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_update_software as jus


class TestLoadCsvLookup(unittest.TestCase):
    def test_loads_real_extension_table(self):
        lookup = jus.load_csv_lookup(jus.DEFAULT_EXT_LOOKUP)
        self.assertEqual(lookup["do"], "Stata")
        self.assertEqual(lookup["ado"], "Stata")
        self.assertEqual(lookup["py"], "Python")
        self.assertNotIn("sh", lookup)
        self.assertNotIn("toml", lookup)

    def test_loads_real_filename_table(self):
        lookup = jus.load_csv_lookup(jus.DEFAULT_NAME_LOOKUP)
        self.assertEqual(lookup["project.toml"], "Julia")
        self.assertEqual(lookup["manifest.toml"], "Julia")


class TestDetectIpynbLanguage(unittest.TestCase):
    def _write_notebook(self, metadata):
        fd, path = tempfile.mkstemp(suffix=".ipynb")
        with os.fdopen(fd, "w") as f:
            json.dump({"metadata": metadata, "cells": []}, f)
        return path

    def test_kernelspec_language(self):
        path = self._write_notebook({"kernelspec": {"language": "python"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "Python")
        finally:
            os.remove(path)

    def test_language_info_fallback(self):
        path = self._write_notebook({"language_info": {"name": "julia"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "Julia")
        finally:
            os.remove(path)

    def test_r_kernel(self):
        path = self._write_notebook({"kernelspec": {"language": "R"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "R")
        finally:
            os.remove(path)

    def test_unrecognized_language_returns_none(self):
        path = self._write_notebook({"kernelspec": {"language": "brainfuck"}})
        try:
            self.assertIsNone(jus.detect_ipynb_language(path))
        finally:
            os.remove(path)

    def test_missing_file_returns_none(self):
        self.assertIsNone(jus.detect_ipynb_language("/nonexistent/path.ipynb"))

    def test_malformed_json_returns_none(self):
        fd, path = tempfile.mkstemp(suffix=".ipynb")
        with os.fdopen(fd, "w") as f:
            f.write("not valid json{")
        try:
            self.assertIsNone(jus.detect_ipynb_language(path))
        finally:
            os.remove(path)


class TestResolveSoftware(unittest.TestCase):
    def setUp(self):
        self.ext_lookup = {"do": "Stata", "ado": "Stata", "py": "Python", "r": "R"}
        self.name_lookup = {"project.toml": "Julia", "manifest.toml": "Julia"}

    def test_basic_extension_mapping(self):
        found, unmatched = jus.resolve_software(
            ["./code/main.do", "./code/clean.py"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Stata", "Python"})
        self.assertEqual(unmatched, {})

    def test_filename_override_beats_extension(self):
        found, unmatched = jus.resolve_software(
            ["./Project.toml"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Julia"})

    def test_excluded_extension_is_unmatched(self):
        found, unmatched = jus.resolve_software(
            ["./run.sh"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"sh": 1})

    def test_dedup_across_files(self):
        found, unmatched = jus.resolve_software(
            ["./a.do", "./b.do", "./c.ado"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Stata"})

    def test_ipynb_without_project_dir_is_unmatched(self):
        found, unmatched = jus.resolve_software(
            ["./notebook.ipynb"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"ipynb": 1})

    def test_ipynb_with_project_dir_resolves_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            nb_path = Path(tmp) / "notebook.ipynb"
            nb_path.write_text(json.dumps({"metadata": {"kernelspec": {"language": "python"}}}))
            found, unmatched = jus.resolve_software(
                ["notebook.ipynb"], tmp, self.ext_lookup, self.name_lookup
            )
            self.assertEqual(found, {"Python"})
            self.assertEqual(unmatched, {})

    def test_no_extension_uses_basename_as_unmatched_key(self):
        found, unmatched = jus.resolve_software(
            ["./makefile"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"makefile": 1})


class TestReadMetadataFilenames(unittest.TestCase):
    def test_reads_filenames_skipping_header(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "lines"])
            writer.writerow(["./code/main.do", "120"])
            writer.writerow(["./code/clean.py", "45"])
        try:
            self.assertEqual(
                jus.read_metadata_filenames(path),
                ["./code/main.do", "./code/clean.py"],
            )
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tools/test_jira_update_software.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'jira_update_software'`

- [ ] **Step 4: Write the minimal implementation**

Create `tools/jira_update_software.py`:

```python
#!/usr/bin/env python3
"""
Detect the software used in a deposit from a programs-metadata.csv (produced
by automations/04_list_program_files.sh) and update a Jira issue's
"Software used" field (customfield_10028) with any newly-identified names.

Usage:
    python3 jira_update_software.py <issue-key> <metadata-csv> [--project-dir DIR] [--yes]
    python3 jira_update_software.py -h|--help

Arguments:
    issue-key      Jira issue key (e.g., AEAREP-9354). Bare numbers are
                    expanded to AEAREP-<n>.
    metadata-csv    Path to generated/programs-metadata[.tag].csv.

Options:
    --project-dir DIR   Root directory the metadata CSV's paths are relative
                        to. Required to inspect .ipynb kernel language;
                        without it, notebooks are left unmatched.
    --lookup-ext CSV    Override the extension->software table (default:
                        software-extensions.csv next to this script).
    --lookup-name CSV   Override the filename->software table (default:
                        software-filenames.csv next to this script).
    --yes               Apply the update to Jira. Without this flag, the
                        script only prints what it would do (dry run).

Environment Variables Required (only when --yes is passed):
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Output:
    Prints detected software and any unmatched files (by extension) to
    stdout. Exit code 0 on success (including a no-op dry run), 1 on error.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
SOFTWARE_FIELD = "customfield_10028"

DEFAULT_EXT_LOOKUP = Path(__file__).resolve().parent / "software-extensions.csv"
DEFAULT_NAME_LOOKUP = Path(__file__).resolve().parent / "software-filenames.csv"

IPYNB_LANGUAGE_MAP = {
    "python": "Python",
    "python3": "Python",
    "r": "R",
    "ir": "R",
    "julia": "Julia",
}


def load_csv_lookup(path):
    """Load a two-column CSV (key,value) into a dict keyed by lower-cased first column."""
    lookup = {}
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if not row:
                continue
            key, value = row[0], row[1]
            lookup[key.strip().lower()] = value.strip()
    return lookup


def detect_ipynb_language(path):
    """Return the canonical software name for a notebook's kernel language, or None."""
    try:
        with open(path, encoding="utf-8") as f:
            notebook = json.load(f)
    except (OSError, ValueError):
        return None

    metadata = notebook.get("metadata", {}) if isinstance(notebook, dict) else {}
    lang = None
    kernelspec = metadata.get("kernelspec")
    if isinstance(kernelspec, dict):
        lang = kernelspec.get("language")
    if not lang:
        language_info = metadata.get("language_info")
        if isinstance(language_info, dict):
            lang = language_info.get("name")
    if not lang:
        return None
    return IPYNB_LANGUAGE_MAP.get(str(lang).strip().lower())


def resolve_software(filenames, project_dir, ext_lookup, name_lookup):
    """
    Resolve a list of relative file paths (as found in programs-metadata.csv)
    to canonical software names.

    Returns (found: set[str], unmatched: dict[str, int]) where unmatched
    counts files that could not be mapped, keyed by extension (or basename
    when there is no extension).
    """
    found = set()
    unmatched = {}

    def record_unmatched(key):
        unmatched[key] = unmatched.get(key, 0) + 1

    for rel_path in filenames:
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        basename = os.path.basename(rel_path)
        base_lower = basename.lower()
        ext = Path(basename).suffix.lstrip(".").lower()

        if base_lower in name_lookup:
            found.add(name_lookup[base_lower])
            continue

        if ext == "ipynb":
            lang = detect_ipynb_language(Path(project_dir) / rel_path) if project_dir is not None else None
            if lang:
                found.add(lang)
            else:
                record_unmatched("ipynb")
            continue

        if ext in ext_lookup:
            found.add(ext_lookup[ext])
            continue

        record_unmatched(ext if ext else base_lower)

    return found, unmatched


def read_metadata_filenames(metadata_csv):
    """Read the filename column of a generated/programs-metadata.csv file."""
    filenames = []
    with open(metadata_csv, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header: filename,lines
        for row in reader:
            if row:
                filenames.append(row[0])
    return filenames
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tools/test_jira_update_software.py -v`
Expected: all tests PASS (`OK` summary line).

- [ ] **Step 6: Commit**

```bash
git add tools/software-extensions.csv tools/software-filenames.csv tools/jira_update_software.py tools/test_jira_update_software.py
git commit -m "feat: add software-detection lookup tables and resolver"
```

---

### Task 2: Jira integration + CLI in `tools/jira_update_software.py`

**Files:**
- Modify: `tools/jira_update_software.py` (append CLI/Jira logic to the file created in Task 1)
- Modify: `tools/test_jira_update_software.py` (append test classes)

**Interfaces:**
- Consumes: everything produced in Task 1 (`load_csv_lookup`, `detect_ipynb_language`, `resolve_software`, `read_metadata_filenames`, `DEFAULT_EXT_LOOKUP`, `DEFAULT_NAME_LOOKUP`, `SOFTWARE_FIELD`, `JIRA_SERVER`).
- Produces (used by `automations/26_update_jira_software.sh` in Task 3):
  - `normalize_issue_key(key: str) -> str`
  - `get_jira_client() -> JIRA | None`
  - `update_software_field(jira, issue_key: str, new_software: set[str]) -> tuple[bool, set[str], set[str]]` — `(updated, final_set, added)`.
  - `main(argv: list[str] | None = None) -> int` — CLI entry point; exit code convention: 0 success (including no-op dry run), 1 on error.

- [ ] **Step 1: Append the failing tests**

Append to `tools/test_jira_update_software.py` (before the `if __name__ == "__main__":` line):

```python
from unittest.mock import MagicMock


class TestNormalizeIssueKey(unittest.TestCase):
    def test_bare_number_gets_prefixed(self):
        self.assertEqual(jus.normalize_issue_key("9603"), "AEAREP-9603")

    def test_prefixed_key_is_uppercased(self):
        self.assertEqual(jus.normalize_issue_key("train-2000"), "TRAIN-2000")

    def test_already_correct_key_unchanged(self):
        self.assertEqual(jus.normalize_issue_key("AEAREP-9603"), "AEAREP-9603")


class TestUpdateSoftwareField(unittest.TestCase):
    def _mock_issue(self, current_labels):
        issue = MagicMock()
        setattr(issue.fields, jus.SOFTWARE_FIELD, current_labels)
        return issue

    def test_adds_new_software_to_empty_field(self):
        jira = MagicMock()
        issue = self._mock_issue([])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata"})

        self.assertTrue(updated)
        self.assertEqual(final_set, {"Stata"})
        self.assertEqual(added, {"Stata"})
        issue.update.assert_called_once_with(fields={jus.SOFTWARE_FIELD: ["Stata"]})

    def test_unions_with_existing_and_dedupes(self):
        jira = MagicMock()
        issue = self._mock_issue(["Stata"])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata", "Python"})

        self.assertTrue(updated)
        self.assertEqual(final_set, {"Stata", "Python"})
        self.assertEqual(added, {"Python"})
        issue.update.assert_called_once_with(fields={jus.SOFTWARE_FIELD: ["Python", "Stata"]})

    def test_no_update_when_nothing_new(self):
        jira = MagicMock()
        issue = self._mock_issue(["Stata", "Python"])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata"})

        self.assertFalse(updated)
        self.assertEqual(added, set())
        issue.update.assert_not_called()


class TestMain(unittest.TestCase):
    def _write_metadata(self, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "lines"])
            for row in rows:
                writer.writerow(row)
        return path

    def test_dry_run_without_yes_returns_0_and_makes_no_jira_call(self):
        path = self._write_metadata([["./code/main.do", "10"]])
        try:
            rc = jus.main([ "AEAREP-1", path])
            self.assertEqual(rc, 0)
        finally:
            os.remove(path)

    def test_missing_metadata_csv_returns_1(self):
        rc = jus.main(["AEAREP-1", "/nonexistent/metadata.csv"])
        self.assertEqual(rc, 1)

    def test_yes_without_credentials_returns_1(self):
        path = self._write_metadata([["./code/main.do", "10"]])
        old_user = os.environ.pop("JIRA_USERNAME", None)
        old_key = os.environ.pop("JIRA_API_KEY", None)
        try:
            rc = jus.main(["AEAREP-1", path, "--yes"])
            self.assertEqual(rc, 1)
        finally:
            os.remove(path)
            if old_user is not None:
                os.environ["JIRA_USERNAME"] = old_user
            if old_key is not None:
                os.environ["JIRA_API_KEY"] = old_key

    def test_no_software_detected_returns_0(self):
        path = self._write_metadata([["./config.yaml", "5"]])
        try:
            rc = jus.main(["AEAREP-1", path])
            self.assertEqual(rc, 0)
        finally:
            os.remove(path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tools/test_jira_update_software.py -v`
Expected: FAIL with `AttributeError: module 'jira_update_software' has no attribute 'normalize_issue_key'` (and similar for the other new names).

- [ ] **Step 3: Append the implementation**

Append to `tools/jira_update_software.py`:

```python
def normalize_issue_key(key):
    """Expand a bare issue number to AEAREP-<n>; uppercase any other key as-is."""
    key = key.strip()
    if key.isdigit():
        return f"AEAREP-{key}"
    return key.upper()


def get_jira_client():
    """Initialize and return an authenticated Jira client, or None if creds/connection fail."""
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_api_key = os.environ.get("JIRA_API_KEY")

    if not jira_username or not jira_api_key:
        print("Error: JIRA_USERNAME and JIRA_API_KEY environment variables must be set", file=sys.stderr)
        return None

    from jira import JIRA

    try:
        return JIRA(server=JIRA_SERVER, basic_auth=(jira_username, jira_api_key), options={"verify": True})
    except Exception as e:
        print(f"Error: Failed to connect to Jira: {e}", file=sys.stderr)
        return None


def update_software_field(jira, issue_key, new_software):
    """
    Union new_software into the issue's current Software used labels and
    update Jira only if that grows the set.

    Returns (updated: bool, final_set: set[str], added: set[str]).
    """
    issue = jira.issue(issue_key)
    current = getattr(issue.fields, SOFTWARE_FIELD, None) or []
    current_set = set(current)
    union = current_set | set(new_software)
    added = union - current_set
    if added:
        issue.update(fields={SOFTWARE_FIELD: sorted(union)})
    return bool(added), union, added


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jira_update_software.py",
        description="Detect software used from a programs-metadata.csv and update Jira's 'Software used' field.",
    )
    parser.add_argument("issue_key")
    parser.add_argument("metadata_csv")
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Root directory the metadata CSV paths are relative to (needed to inspect .ipynb kernel language)",
    )
    parser.add_argument("--lookup-ext", default=str(DEFAULT_EXT_LOOKUP))
    parser.add_argument("--lookup-name", default=str(DEFAULT_NAME_LOOKUP))
    parser.add_argument("--yes", action="store_true", help="Apply the update to Jira (default is a dry run)")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.metadata_csv):
        print(f"Error: metadata CSV not found: {args.metadata_csv}", file=sys.stderr)
        return 1

    ext_lookup = load_csv_lookup(args.lookup_ext)
    name_lookup = load_csv_lookup(args.lookup_name)
    filenames = read_metadata_filenames(args.metadata_csv)

    found, unmatched = resolve_software(filenames, args.project_dir, ext_lookup, name_lookup)

    print(f"Software detected: {', '.join(sorted(found)) or '(none)'}")
    if unmatched:
        print("Files not mapped to any software (indeterminate/excluded), by extension:")
        for key, count in sorted(unmatched.items()):
            print(f"  {key}: {count} file(s)")

    if not found:
        print("No software detected; nothing to update.")
        return 0

    if not args.yes:
        print("Dry run (pass --yes to apply). Would add to Jira's Software used field:", ", ".join(sorted(found)))
        return 0

    jira = get_jira_client()
    if jira is None:
        return 1

    issue_key = normalize_issue_key(args.issue_key)

    try:
        updated, final_set, added = update_software_field(jira, issue_key, found)
    except Exception as e:
        print(f"Error: Failed to update {issue_key}: {e}", file=sys.stderr)
        return 1

    if updated:
        print(f"Updated {issue_key} Software used: added {', '.join(sorted(added))} (now: {', '.join(sorted(final_set))})")
    else:
        print(f"{issue_key} Software used already contains all detected software; no update needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tools/test_jira_update_software.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/jira_update_software.py tools/test_jira_update_software.py
git commit -m "feat: add Jira update + CLI to jira_update_software.py"
```

---

### Task 3: `automations/26_update_jira_software.sh` wrapper + pipeline wiring for the software field

**Files:**
- Create: `automations/26_update_jira_software.sh`
- Modify: `bitbucket-pipelines.yml`

**Interfaces:**
- Consumes: `tools/jira_update_software.py`'s CLI (`<issue-key> <metadata-csv> --project-dir DIR --yes`), and `tools/jira_find_task_by_icpsr.py` (existing, unchanged) for the directory-based ticket fallback.
- Produces: a pipeline step callable as `./automations/26_update_jira_software.sh $projectID` (tag argument optional, matching `04_list_program_files.sh`'s `$tag` convention).

- [ ] **Step 1: Create the wrapper script**

Create `automations/26_update_jira_software.sh`:

```bash
#!/bin/bash
# 26_update_jira_software.sh
# Detect software used (Stata, R, Python, etc.) from the program files listed
# by 04_list_program_files.sh, and add any newly-identified software to the
# Jira issue's "Software used" field (customfield_10028). Never removes
# existing values.
#
# Ticket resolved in order: $jiraticket env var -> config.yml -> openICPSR directory detection.
#
# Usage: 26_update_jira_software.sh <project-dir> [tag]
#   project-dir  Directory the deposit was unpacked into (used to inspect .ipynb kernel language).
#   tag          Optional. Matches the $tag suffix used by 04_list_program_files.sh, if any.

_project_dir="${1:-}"
_tag="${2:-}"

if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "26_update_jira_software: no Python 3 found, skipping"
    exit 0
fi

_suffix=""
[ -z "$_tag" ] || _suffix=".$_tag"
_metadata="generated/programs-metadata${_suffix}.csv"

if [ ! -f "$_metadata" ]; then
    echo "26_update_jira_software: $_metadata not found, skipping"
    exit 0
fi

_jira="${jiraticket:-}"
echo "26_update_jira_software: jiraticket from environment: '${_jira}'"

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "26_update_jira_software: jiraticket from config.yml: '${_jira}'"
    else
        echo "26_update_jira_software: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "26_update_jira_software: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "26_update_jira_software: jiraticket from lookup: '${_jira}'"
    else
        echo "26_update_jira_software: no openICPSR directory found"
    fi
fi

if [ -z "$_jira" ]; then
    echo "26_update_jira_software: no Jira ticket found, skipping"
    exit 0
fi

$PYTHON_CMD tools/jira_update_software.py "$_jira" "$_metadata" --project-dir "$_project_dir" --yes || \
    echo "26_update_jira_software: Warning - failed to update Software used field"

exit 0
```

- [ ] **Step 2: Verify script syntax**

Run: `bash -n automations/26_update_jira_software.sh`
Expected: no output (syntax OK).

- [ ] **Step 3: Smoke-test the no-ticket, no-metadata paths**

Run:
```bash
chmod +x automations/26_update_jira_software.sh
cd /tmp && mkdir -p smoke26 && cd smoke26 && bash /home/vilhuber/Workspace/Github/replication-template-development/automations/26_update_jira_software.sh someproject
```
Expected output: `26_update_jira_software: generated/programs-metadata.csv not found, skipping` (the metadata-CSV check runs before ticket resolution, and there's no `generated/` dir in the empty temp dir), exit code 0.

Run: `cd /home/vilhuber/Workspace/Github/replication-template-development && rm -rf /tmp/smoke26`

- [ ] **Step 4: Wire the script into `bitbucket-pipelines.yml`**

In pipeline `1-populate-from-icpsr`, find this line (currently line 286, immediately before the final publish-comment call):

```yaml
            - git push && git push --tags
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr completed
```

Replace with:

```yaml
            - git push && git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr completed
```

In pipeline `w-big-populate-from-icpsr`, find this line (currently immediately before that pipeline's final publish-comment call):

```yaml
            - git status
            - git push
            - git push --tags
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr completed
```

Replace with:

```yaml
            - git status
            - git push
            - git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr completed
```

- [ ] **Step 5: Validate the YAML still parses**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('bitbucket-pipelines.yml')); print('OK')"`
Expected: `OK`
(This is an ad hoc terminal check to validate the edit, not code added to the repo — no inline Python is being written into any file.)

- [ ] **Step 6: Commit**

```bash
git add automations/26_update_jira_software.sh bitbucket-pipelines.yml
git commit -m "feat: wire Software-used Jira field update into the populate pipelines"
```

---

### Task 4: Rename and extend the Jira attachments script; collapse the duplicated inline YAML

**Files:**
- Rename: `automations/30_download_jira_attachments.sh` → `automations/30_download_commit_jira_attachments.sh`
- Modify: `automations/30_download_commit_jira_attachments.sh` (add commit step)
- Modify: `docs/tools/jira/96-90-jira_download_attachments.md` (references to the renamed script)
- Modify: `bitbucket-pipelines.yml` (both inline blocks)

**Interfaces:**
- Produces: `automations/30_download_commit_jira_attachments.sh [--list] [--filter PATTERN]` — same CLI as before, now also commits any downloaded `*.pdf`/`*.docx` (skipped in `--list` mode or when nothing changed).

- [ ] **Step 1: Rename the script**

```bash
git mv automations/30_download_jira_attachments.sh automations/30_download_commit_jira_attachments.sh
```

- [ ] **Step 2: Add the commit step to the renamed script**

In `automations/30_download_commit_jira_attachments.sh`, update the header comment and add commit logic. Replace:

```bash
#!/bin/bash
#
# Download Jira attachments for the current case
#
# Usage: bash automations/30_download_jira_attachments.sh [--list] [--filter PATTERN]
#
# Reads the Jira ticket from config.yml and downloads all attachments
# to the repository root directory with their original filenames.
#
# Options:
#   --list              List attachments without downloading
#   --filter PATTERN    Only download files matching PATTERN (e.g., ".pdf", "manuscript")
#
# Environment:
#   JIRA_USERNAME   - Jira email address (required)
#   JIRA_API_KEY    - Jira API token (required)
#
# Examples:
#   bash automations/30_download_jira_attachments.sh
#   bash automations/30_download_jira_attachments.sh --list
#   bash automations/30_download_jira_attachments.sh --filter manuscript
#   bash automations/30_download_jira_attachments.sh --filter form
```

with:

```bash
#!/bin/bash
#
# Download Jira attachments for the current case and commit them
#
# Usage: bash automations/30_download_commit_jira_attachments.sh [--list] [--filter PATTERN]
#
# Reads the Jira ticket from config.yml and downloads all attachments
# to the repository root directory with their original filenames, then
# (unless --list was given) git-adds and commits any *.pdf/*.docx files.
#
# Options:
#   --list              List attachments without downloading or committing
#   --filter PATTERN    Only download files matching PATTERN (e.g., ".pdf", "manuscript")
#
# Environment:
#   JIRA_USERNAME   - Jira email address (required)
#   JIRA_API_KEY    - Jira API token (required)
#
# Examples:
#   bash automations/30_download_commit_jira_attachments.sh
#   bash automations/30_download_commit_jira_attachments.sh --list
#   bash automations/30_download_commit_jira_attachments.sh --filter manuscript
#   bash automations/30_download_commit_jira_attachments.sh --filter form
```

Then replace the help text block:

```bash
        -h|--help)
            echo "Usage: $0 [--list] [--filter PATTERN]"
            echo ""
            echo "Download Jira attachments for the current case."
            echo ""
            echo "Options:"
            echo "  --list              List attachments without downloading"
            echo "  --filter PATTERN    Only download files matching PATTERN"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --list"
            echo "  $0 --filter manuscript"
            exit 0
            ;;
```

with:

```bash
        -h|--help)
            echo "Usage: $0 [--list] [--filter PATTERN]"
            echo ""
            echo "Download Jira attachments for the current case and commit them."
            echo ""
            echo "Options:"
            echo "  --list              List attachments without downloading or committing"
            echo "  --filter PATTERN    Only download files matching PATTERN"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --list"
            echo "  $0 --filter manuscript"
            exit 0
            ;;
```

Then replace the final block that runs the Python script:

```bash
# Run the Python script
cd "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/jira_download_attachments.py" "${ARGS[@]}"
```

with:

```bash
# Run the Python script
cd "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/jira_download_attachments.py" "${ARGS[@]}"

# Commit whatever was downloaded (skip in --list mode; nothing to commit there)
if [[ -z "${LIST_ONLY}" ]]; then
    git add -f *.pdf *.docx 2>/dev/null || true
    git diff --cached --quiet || git commit -m "[skip ci] Downloaded Jira attachments for ${JIRA_TICKET}"
fi
```

- [ ] **Step 3: Verify script syntax**

Run: `bash -n automations/30_download_commit_jira_attachments.sh`
Expected: no output (syntax OK).

- [ ] **Step 4: Smoke-test `--help` and `--list` still work**

Run: `bash automations/30_download_commit_jira_attachments.sh --help`
Expected: usage text mentioning `30_download_commit_jira_attachments.sh`, exit code 0.

- [ ] **Step 5: Update the doc page's script references**

In `docs/tools/jira/96-90-jira_download_attachments.md`, replace every occurrence of `automations/30_download_jira_attachments.sh` with `automations/30_download_commit_jira_attachments.sh` (9 occurrences: 4 in the "As a standalone script" usage block, 4 in the "Common usage patterns" block, 1 in the "Related files" list). Also update the "Related files" bullet's description. Replace:

```markdown
- [30_download_jira_attachments.sh](https://github.com/aeaDataEditor/replication-template/blob/master/automations/30_download_jira_attachments.sh) - Automation wrapper script
```

with:

```markdown
- [30_download_commit_jira_attachments.sh](https://github.com/aeaDataEditor/replication-template/blob/master/automations/30_download_commit_jira_attachments.sh) - Automation wrapper script (downloads attachments and commits them)
```

- [ ] **Step 6: Replace both inline pipeline blocks with a single call**

In pipeline `1-populate-from-icpsr` (the "Commit everything back" step), find:

```yaml
            - ./automations/20_commit_code.sh config.yml notag
            # Download Jira attachments (manuscript and form)
            - if [ ! -z "$jiraticket" ]; then python3 tools/jira_download_attachments.py "$jiraticket" --output-dir . --verbose || echo "Warning - Failed to download Jira attachments"; fi
            - if [ ! -z "$jiraticket" ]; then git add -f *.pdf *.docx  2>/dev/null || true; fi
            - git diff --cached --quiet || git commit -m "[skip ci] Downloaded Jira attachments for $jiraticket"
            - git status
            - git push && git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr completed
```

Replace with:

```yaml
            - ./automations/20_commit_code.sh config.yml notag
            - ./automations/30_download_commit_jira_attachments.sh
            - git status
            - git push && git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr completed
```

In pipeline `w-big-populate-from-icpsr`, find:

```yaml
            - ./automations/20_commit_code.sh config.yml notag
            # Download Jira attachments (manuscript and form)
            - if [ ! -z "$jiraticket" ]; then python3 tools/jira_download_attachments.py "$jiraticket" --output-dir . --verbose || echo "Warning - Failed to download Jira attachments"; fi
            - if [ ! -z "$jiraticket" ]; then git add -f *.pdf *.docx  2>/dev/null || true; fi
            - git diff --cached --quiet || git commit -m "[skip ci] Downloaded Jira attachments for $jiraticket"
            - git status
            - git push
            - git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr completed
```

Replace with:

```yaml
            - ./automations/20_commit_code.sh config.yml notag
            - ./automations/30_download_commit_jira_attachments.sh
            - git status
            - git push
            - git push --tags
            - ./automations/26_update_jira_software.sh $projectID
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr completed
```

- [ ] **Step 7: Validate the YAML still parses**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('bitbucket-pipelines.yml')); print('OK')"`
Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add automations/30_download_commit_jira_attachments.sh docs/tools/jira/96-90-jira_download_attachments.md bitbucket-pipelines.yml
git commit -m "refactor: fold Jira attachment commit into 30_download_commit_jira_attachments.sh"
```

Note: `git mv` in Step 1 already staged the rename; this final `git add`/`commit` captures the content changes made on top of it in the same commit.

---

### Task 5: Document the coding conventions in `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:** None (documentation only).

- [ ] **Step 1: Add a "Coding Conventions" section**

In `CLAUDE.md`, after the `## Repository Context` section (end of file), append:

```markdown

## Coding Conventions

- Keep `bitbucket-pipelines.yml` steps short: call into `automations/*.sh` rather than writing multi-line inline logic in the YAML.
- When an automation needs real logic beyond argument/ticket resolution and shell plumbing (API calls, parsing, data transforms), pair a thin `automations/NN_name.sh` (resolves arguments/the Jira ticket, calls the tool) with a `tools/name.py` that does the actual work. Examples: `70_publish_comment.sh`->`jira_add_comment.py`, `30_download_commit_jira_attachments.sh`->`jira_download_attachments.py`, `26_update_jira_software.sh`->`jira_update_software.py`. Don't add a wrapper script whose only job is to call another script that already does the work - extend that script instead.
- Never write or run inline Python (`python3 -c "..."`) in the pipeline YAML or in shell scripts, under any circumstances. Always put it in a proper file under `tools/`. (Note: `bitbucket-pipelines.yml` currently has several pre-existing `python3 -c "..."` snippets for Zenodo-ID URL parsing that violate this rule - out of scope for prior changes, flagged for a future cleanup pass.)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: record automations/tools pairing and no-inline-Python conventions"
```

---

## Final Verification

- [ ] Run the full test suite once more: `python3 tools/test_jira_update_software.py -v` — all PASS.
- [ ] `bash -n automations/26_update_jira_software.sh && bash -n automations/30_download_commit_jira_attachments.sh` — no output.
- [ ] `python3 -c "import yaml; yaml.safe_load(open('bitbucket-pipelines.yml')); print('OK')"` — prints `OK`.
- [ ] `grep -rn "30_download_jira_attachments" bitbucket-pipelines.yml automations/ docs/tools/jira/96-90-jira_download_attachments.md` — no matches (all renamed).
- [ ] `git log --oneline -6` shows the five feature/docs commits from this plan.
