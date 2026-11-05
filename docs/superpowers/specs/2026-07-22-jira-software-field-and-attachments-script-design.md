# Design: Jira "Software used" field automation + Jira attachments script extraction

Date: 2026-07-22

## Background

`automations/04_list_program_files.sh` already identifies program files by
extension and writes `generated/programs-list.txt`, `generated/programs-summary.txt`,
and `generated/programs-metadata.csv` (filename,lines). Nothing currently
uses that output to populate Jira.

Separately, `bitbucket-pipelines.yml` has two duplicated inline blocks (lines
281-284 in pipeline `1-populate-from-icpsr`, and 550-553 in
`w-big-populate-from-icpsr`) that download Jira attachments and commit them.
An unused script, `automations/30_download_jira_attachments.sh`, already
does the download half but not the commit half, and isn't wired into the
pipeline.

## Goal 1: Populate Jira "Software used" from identified program files

### Jira field

`customfield_10028`, display name "Software used", schema type
`com.atlassian.jira.plugin.system.customfieldtypes:labels` (an array of
free-text label strings with instance-wide autocomplete memory — not a
constrained select list). Confirmed via live query against
`aeadataeditors.atlassian.net`.

Existing values in use (sampled from 100 tickets with the field set):
`Stata` (78), `MATLAB` (23), `R` (18), `SAS` (14), `Python` (7), `Dynare` (4),
plus a couple of stray lowercase variants (`Matlab`, `python`). New values
written by this automation must follow the capitalized canonical form.

### Extension → software lookup table

New file: `tools/software-extensions.csv` (two columns: `extension,software`,
no header... actually include header `extension,software` for readability).
Human-editable, loaded at runtime — no lookup logic hardcoded in Python
beyond "read this CSV".

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

Deliberately absent (no automatic mapping — build/orchestration/config
files, not analysis software; `04_list_program_files.sh` tracks them for
other reasons but they say nothing about "software used"): `sh`, `toml`,
`yaml`, `yml`, `qmd`, `makefile`.

### Filename-specific overrides

New file: `tools/software-filenames.csv` (two columns: `filename,software`),
matched against the file's basename case-insensitively, checked **before**
falling back to the extension table:

```
filename,software
Project.toml,Julia
Manifest.toml,Julia
```

This lets specific, unambiguous filenames resolve even when their extension
alone (`.toml`) is too generic to map deterministically.

### `.ipynb` special case

`.ipynb` is not in the extension table. `tools/jira_update_software.py`
opens each `.ipynb` file found in the deposit directory as JSON and reads
`metadata.kernelspec.language` (falling back to
`metadata.language_info.name` if absent), mapping the result
(`python`→Python, `r`→R, `julia`→Julia, etc., case-insensitive) to the
canonical name. If the notebook can't be parsed or no language can be
determined, that file contributes nothing — it is not forced into a guess.

### Resolution algorithm (per file in `generated/programs-metadata.csv`)

1. If basename matches `tools/software-filenames.csv` (case-insensitive) → use that software.
2. Else if extension is `.ipynb` → inspect the notebook JSON as above.
3. Else if extension matches `tools/software-extensions.csv` → use that software.
4. Else → excluded/indeterminate, not included, but logged to stdout for visibility (so the tables can be extended later).

Result: a deduplicated set of canonical software names actually observed in
this deposit.

### Script pair

- `tools/jira_update_software.py <issue-key> <metadata-csv> [--lookup-ext CSV] [--lookup-name CSV] [--project-dir DIR] [--yes]`
  - Resolves software names as above (needs `--project-dir` to locate and
    open `.ipynb` files referenced in the metadata CSV — paths in that CSV
    are relative to the unpacked deposit directory).
  - Fetches the issue's current `customfield_10028` value.
  - Computes the union of existing + newly detected names (dedup).
  - If the union is a strict superset of the existing value, updates the
    issue; otherwise makes no API write.
  - Prints a summary: software found, software newly added, files that
    matched no rule (indeterminate/excluded), grouped by extension, to
    stdout for pipeline log visibility.
  - Follows the credential/connection conventions already used by
    `tools/jira_sync_fields.py` / `tools/jira_download_attachments.py`
    (`JIRA_USERNAME` / `JIRA_API_KEY` env vars, same server constant).
- `automations/26_update_jira_software.sh <project-dir> [tag]`
  - Resolves the Jira ticket the same way `automations/70_publish_comment.sh`
    does (env var `$jiraticket` → `config.yml` → openICPSR-style directory
    detection), resolves the metadata CSV path
    (`generated/programs-metadata$suffix.csv`, matching the `$tag` suffix
    convention from `04_list_program_files.sh`), and calls
    `tools/jira_update_software.py`.
  - Non-fatal: if no ticket, no metadata CSV, or the Python call fails, logs
    a warning and exits 0 so it never breaks the pipeline.

### Pipeline wiring

Insert `./automations/26_update_jira_software.sh $projectID` immediately
before the final `./automations/70_publish_comment.sh ... completed` call
in:
- `1-populate-from-icpsr` (before current line 287)
- `w-big-populate-from-icpsr` (before current line 557)

At that point in both pipelines, `$projectID` is unpacked and
`generated/programs-metadata.csv` already exists from step 04, so both
required inputs are present.

## Goal 2: Extract Jira attachment download+commit into one script

Rename `automations/30_download_jira_attachments.sh` →
`automations/30_download_commit_jira_attachments.sh`, and extend it in
place (no new wrapper script) to, after a successful non-`--list` download:

```
git add -f *.pdf *.docx 2>/dev/null || true
git diff --cached --quiet || git commit -m "[skip ci] Downloaded Jira attachments for $JIRA_TICKET"
```

using the same `JIRA_TICKET` value the script already resolves from
`config.yml`. `--list` and `--filter` behavior is unchanged; commit is
skipped in `--list` mode.

`bitbucket-pipelines.yml` changes: replace the 4-line inline block at
281-284 and the identical duplicate at 550-553, each with:

```
- ./automations/30_download_commit_jira_attachments.sh
```

## Coding conventions to add to CLAUDE.md

New "Coding Conventions" section:

- Keep `bitbucket-pipelines.yml` steps as short calls into
  `automations/*.sh`; push substantive logic out of the YAML and into a
  script.
- When an automation needs real logic beyond argument/ticket resolution and
  shell plumbing (API calls, parsing, data transforms), pair a thin
  `automations/NN_name.sh` with a `tools/name.py` that does the actual
  work — mirrors `70_publish_comment.sh`→`jira_add_comment.py`,
  `30_download_commit_jira_attachments.sh`→`jira_download_attachments.py`,
  `26_update_jira_software.sh`→`jira_update_software.py`. Don't add a
  wrapper script whose only job is to call another script that already does
  the work — extend that script instead.
- Never write or run inline Python (`python3 -c "..."`) in the pipeline
  YAML or in shell scripts, under any circumstances. Always a proper file
  under `tools/`. (Note: `bitbucket-pipelines.yml` currently has several
  pre-existing `python3 -c "..."` snippets for Zenodo-ID URL parsing that
  violate this rule — out of scope for this change, flagged for a future
  cleanup pass.)

## Testing

- `tools/jira_update_software.py`: unit-testable resolution logic (given a
  metadata CSV + fixture `.ipynb` files, does it produce the expected
  software set?) without hitting the real Jira API — Jira calls isolated
  behind a thin client wrapper so they can be mocked/skipped.
- `automations/26_update_jira_software.sh` and
  `automations/30_download_commit_jira_attachments.sh`: manual/CI smoke
  test only (matches existing convention — no test harness for the other
  `automations/*.sh` scripts).

## Out of scope

- Fixing the pre-existing inline `python3 -c` snippets elsewhere in
  `bitbucket-pipelines.yml`.
- Any change to `REPLICATION.md`'s own "Software Requirements" checklist —
  this only touches the Jira field.
- Determining software from file *content* beyond the `.ipynb` kernel
  metadata case (e.g., sniffing shebangs).
