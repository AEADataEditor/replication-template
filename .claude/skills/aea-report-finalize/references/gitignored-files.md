# Retrieving gitignored deposit files

Read when Step 3.2 needs the *content* of a file the deposit's `.gitignore`
excludes (typically a `*.txt` table or a data format) and `generated/` reports
don't show it. Without the file, an exhibit can't be checked against the
manuscript, so fetching it is legitimate, but the download can be slow and the
editor may prefer to do it themselves.

1. **Ask first, every time**, with `AskUserQuestion`: name the files needed and
   why; options: you download / editor downloads / skip (report as
   unverifiable). Batch mode: report it as a numbered decision, don't download.
2. Download into a scratch directory outside the repo tree:
   ```bash
   python3 tools/download_openicpsr-private.py <projectID> <scratch dir>
   ```
   (`projectID` from `tools/resolve_project_id.sh`; credentials come from the
   environment, so if they are unset, stop and tell the editor.)
3. Extract without overwriting tracked files:
   ```bash
   unzip -n <scratch dir>/<zip> -d <deposit dir>
   ```
   The downloader itself skips extraction when the deposit dir already exists,
   which is why extraction is a separate step.
4. `git add -f` only the specific files you used as evidence, never the whole
   extraction (the rest is gitignored on purpose).
5. **Do not** use `tools/download_sivacor.py` for this: it clears the deposit
   folder, creates a branch and commits.

Note in Step 6 which files were fetched and which exhibits they let you check.
