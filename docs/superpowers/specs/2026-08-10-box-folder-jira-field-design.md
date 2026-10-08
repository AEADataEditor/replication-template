# Design: Jira-driven Box folder ID for the restricted-data download pipeline

Date: 2026-08-10

## Problem

The `8-download-box-manifest` Bitbucket pipeline step locates the restricted-data
Box folder by searching for a subfolder named `aearep-<repository_name>` under
the shared Box parent folder (`BOX_FOLDER_PRIVATE`). This search is fragile
(naming mismatches, folders moved/renamed) and duplicates information: Jira has
a "Restricted data Box Folder ID" custom field intended to record the folder
directly.

The pipeline step also does not currently resolve a `jiraticket`, unlike most
other steps.

## Goals

- If the current ticket's "Restricted data Box Folder ID" field is filled in,
  download from that folder ID directly, skipping the name search.
- If it is empty, keep the existing name-search behavior, then persist the
  folder ID that was found so it doesn't have to be searched for again.
- Notify the ticket when this happens, including a reminder to verify
  "Agreement signed" is correctly filled out (a field that is not otherwise
  touched by this flow, and is easy to forget when a Box folder is being
  fixed).
- Bring `bitbucket-pipelines.yml` step 8 in line with the repo's convention of
  calling into `automations/*.sh` rather than inlining multi-line logic in the
  YAML.

## Non-goals

- Changing how `BOX_FOLDER_PRIVATE` (the parent Box folder) is configured.
- Touching `automations/60_process_restricted_box.sh` behavior for anything
  other than what's described here (e.g. no new manifest logic).
- Building a general Jira-field-write tool. Only `config.yml` is written by
  the script; the one Jira write this feature needs (the comment) goes through
  the existing comment-posting path.

## Two-stage rollout

**Stage 1 (separate commit):** Refactor pipeline step 8 so its three inline
script lines move into `automations/60_process_restricted_box.sh`, with no
behavior change. This corrects a pre-existing convention violation before new
logic is layered on top of it, and keeps that diff reviewable on its own.

**Stage 2 (separate commit):** Add the Jira-field-aware folder resolution,
`config.yml` persistence, and comment notification described below.

## Design

### `tools/download_box_private.py`

Add `--target-folder-id ID`. When given, downloading starts directly from that
Box folder ID — the `aearep-<subfolder>` search is skipped entirely (the
`subfolder` positional argument becomes optional and is ignored if
`--target-folder-id` is present).

In both the direct-ID path and the existing search path, print
`BOX_FOLDER_ID=<id>` to stdout immediately before `download_folder()` is
called, once the target ID is finally known. This gives the caller a single,
stable way to learn which folder ID was actually used, regardless of which
path was taken.

### `tools/jira_get_info.py`

Add keyword `boxfolderid`, reading the "Restricted data Box Folder ID" field.
Same shape as the existing `openicpsr` / `mcid` keyword handlers: returns the
stripped string value, or empty string if unset. Documented in both the
module docstring and `print_help()`.

### `automations/60_process_restricted_box.sh`

New signature: `60_process_restricted_box.sh <repository_name> [directory=restricted] [tag=directory]`.

Stage 1 body (parity with current pipeline step 8):
1. `download_box_private.py "$repository_name" --output-dir "$directory"`
2. `automations/00_unpack_zip.sh "$directory"`
3. `automations/02_create_manifest.sh "$directory" "$tag"`

Stage 2 adds, before step 1:
1. Resolve `jiraticket`: env var → `config.yml` → openICPSR-directory
   detection, matching the fallback chain already duplicated in
   `26_update_jira_software.sh` and `70_publish_comment.sh`.
2. If a ticket was resolved, run
   `tools/jira_get_info.py "$jiraticket" boxfolderid`.
   - **Non-empty result:** download via
     `download_box_private.py --target-folder-id "$box_folder_id" --output-dir "$directory"`.
   - **Empty result (or no ticket resolved):** download via
     `download_box_private.py "$repository_name" --output-dir "$directory"`
     as today, capture its `BOX_FOLDER_ID=` stdout line, and write that value
     into `config.yml` as a new `boxfolderid:` key (added with the same
     sed-if-present-else-append approach used elsewhere for config.yml keys).

No Jira **writes** happen in this script — only the read of `boxfolderid`,
and normal file/Box operations. This keeps all Jira communication in the
pipeline YAML, consistent with how the rest of the pipeline is organized.

### `automations/70_publish_comment.sh`

Add a `--config` mode: `70_publish_comment.sh --config [pipeline-name] [extra-message]`.

Behavior:
1. Resolve `jiraticket` using the script's existing fallback chain (no
   change).
2. Run `git diff -- config.yml`. If the diff is empty, exit 0 without
   posting anything — this makes the mode a safe no-op to call
   unconditionally from any pipeline step that may or may not have touched
   `config.yml`, not just this one.
3. If non-empty, post a comment containing the diff wrapped in a Jira
   `{code}` block, with `extra-message` appended below it if provided.

This generalizes the existing single-purpose comment script rather than
adding a parallel one-off script, and is written so other pipeline steps that
modify `config.yml` can reuse it later.

### `bitbucket-pipelines.yml`

Step 8 (`8-download-box-manifest`):
- Replace the three inline lines (`download_box_private.py`,
  `00_unpack_zip.sh`, `02_create_manifest.sh`) with
  `./automations/60_process_restricted_box.sh $repository_name`.
- After that call and before the existing `git add -f generated/*` /
  commit / push, add:
  ```
  ./automations/70_publish_comment.sh --config 8-download-box-manifest \
      "Please verify that 'Agreement signed' is correctly filled out."
  ```
- Extend the `git add -f` to also include `config.yml`, so a newly
  discovered folder ID gets committed alongside the generated manifest.

### `config.yml`

New optional key `boxfolderid:`, alongside the existing `openicpsr:`,
`zenodo:`, etc. Left blank normally; populated only when the script had to
fall back to the name search.

## Data flow summary

```
step 8 YAML
  -> resolve jiraticket is NOT done in YAML; it happens inside the script
  -> automations/60_process_restricted_box.sh $repository_name
       -> resolves jiraticket itself
       -> reads Jira boxfolderid field
       -> [field set]   download --target-folder-id
       -> [field empty] download by name search, write discovered id to config.yml
       -> unpack, create manifest
  -> automations/70_publish_comment.sh --config ...   (comments only if config.yml changed)
  -> git add -f generated/* config.yml; commit; push
  -> automations/70_publish_comment.sh 8-download-box-manifest completed   (existing, unchanged)
```

## Error handling

- If `jiraticket` cannot be resolved at all, the script falls back to the
  current name-search behavior unconditionally (same as if the ticket had no
  value in the field) — the feature degrades to today's behavior rather than
  failing the pipeline.
- If the Jira read (`jira_get_info.py boxfolderid`) fails or credentials are
  missing, it prints nothing (existing tool behavior for all keywords), which
  is treated the same as "empty" — fall back to search.
- If `download_box_private.py --target-folder-id` is given an ID that doesn't
  exist, it fails the same way the existing code fails on a bad
  `BOX_FOLDER_PRIVATE`/search miss (Box API error surfaces, non-zero exit).
  No special-casing is added to auto-retry via search on a bad ID — a
  Jira-recorded ID that no longer resolves is a data problem to fix in Jira,
  not silently paper over.

## Testing

- `tools/test_jira_update_software.py` establishes the pattern for testing
  Jira-touching tools in this repo (mocking the `jira` client). A parallel
  `tools/test_download_box_private.py` will cover `--target-folder-id`
  handling and the `BOX_FOLDER_ID=` stdout line, and `jira_get_info.py`'s
  `boxfolderid` keyword gets a unit test alongside its existing keyword tests
  (there currently are none for `jira_get_info.py` — this will be the first;
  keep it narrowly scoped to the new keyword rather than backfilling
  coverage for the whole file).
- `automations/60_process_restricted_box.sh` and `70_publish_comment.sh --config`
  are shell orchestration over already-tested pieces; verified by manual
  dry-run (mocked/fake Jira responses) rather than new shell test
  infrastructure, consistent with how the other `automations/*.sh` scripts in
  this repo are validated.
