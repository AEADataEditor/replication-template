# Worker prompt template

Fill the `<...>` placeholders and send one copy per ready repo as the `prompt`
of a background `Agent` call. Keep the wording: each line answers a failure
seen in an earlier run.

---

You are running the editor's finishing pass on ONE AEA replication repo,
unattended. Nobody will answer questions while you work.

Repo: `<ABS_REPO_PATH>` (`<REPO>`)
Your scratch area: `<SCRATCHPAD>/<REPO>/` — use only this subdirectory for
temporary files, never the scratchpad root (other workers share it).

## Setup
1. `cd <ABS_REPO_PATH>` before any git or tool command; the session is rooted
   in the parent directory, and the skill's commands assume the repo root.
2. Skills in sub-repos are not loaded for you. Read
   `<ABS_REPO_PATH>/.claude/skills/aea-report-finalize/SKILL.md` and the
   files in its `references/` by absolute path, then follow that skill,
   Steps 0–6, including its Restrictions.
3. A pre-edit copy of REPLICATION.md is at
   `<SCRATCHPAD>/<REPO>/REPLICATION.orig.md` (made by the orchestrator).
   `git diff REPLICATION.md` is the authoritative record of your edits.

## Non-interactive mode (overrides the skill's "ask the user")
The skill tells you to ask via AskUserQuestion. Do not ask. Instead:
- Make only the edits the skill itself labels mechanical (checkbox
  normalization, `None.` vs Classification fix, standard tag for a scan hit,
  setup-program tag trio, `aea-parse-tags` run, singular→plural rewrites of
  consolidated lines, `{{ }}` stripping, verbatim fixes from Step 5b) and draft
  the SUMMARY.
- Everything else the skill would ask about becomes a numbered decision
  (D1, D2, …) in your report, each with: question, evidence (file:line,
  quotes, counts), options, and your recommendation listed first.
- If a gate in Steps 0–2 says stop, stop and report why; don't work around it.
- If the decision sentence depends on an open decision, say which.

## Hard limits (from aea-report-finalize, unchanged)
Never commit, tag, push, approve, or run `aeaready`. Never write to Jira (read
only via `tools/jira_get_info.py` / `tools/jira_find_task_by_icpsr.py`). Never
edit from `# Automatically Generated Appendices` to the end of REPLICATION.md,
nor `generated/REPLICATION_appendix.md`. Never resolve the `openicpsr/xxxxx`
placeholder or add a DOI. Never fabricate findings, packages, paths, or canned
language. Edit no file in the repo other than REPLICATION.md.

## Things to check (report them; fix only if the skill calls the fix mechanical)
These recurred across repos in earlier runs:
- PII tag wording from the pipeline ("Our scanner identified possible PII…",
  `automations/24_amend_report.sh`) differs from `sample-language-report.md`.
- IRB tag from the template says "IRB approval"; the library says "ethics
  approval".
- Data-citation and IRB-footnote tags often lack `{{ METADATA m }}` and land
  in the openICPSR list instead of the manuscript list. Check routing after
  `aea-parse-tags`.
- Older templates have a "trusted third-party" box instead of "trusted
  verification system" (see the skill's `references/tro.md`).
- `### Reason for incomplete reproducibility` vs Findings vs the live Jira
  field is the most frequent judgment call; always report all three.
- Template leftovers: example images (`template/dog.jpg`, `template/odie.jpg`),
  the BLS example data source, truncated or placeholder paragraphs.
- `[NOTE] openICPSR metadata is sufficient.` is contradicted only by
  `[REQUIRED]` metadata tags. `[SUGGESTED]` metadata tags are optional and
  coexist with that NOTE; do not flag the combination.

## Sub-agents
<EITHER: "Do not start sub-agents." OR: "You may delegate narrow read-only
checks to a <MODEL> sub-agent. If you do, list each one in the Usage section
with the tokens, tool uses and duration from its completion notice.">

## Output: your final message IS the report
Do not write the report to a file (the harness refuses report files from
sub-agents, and shell-redirect workarounds are not wanted). Return it as your
final text in exactly this shape; the orchestrator saves it.

```
# <REPO>: editor finishing pass report
Status: finished | stopped at Step N (reason)
Ticket / MC number / title; R&R override applies? (yes/no, why)
Decision sentence used (and which decisions it depends on)

## Gates (Steps 0, 1, 2, 2b)
## Step 5b result
## Drafted SUMMARY (verbatim, as written into REPLICATION.md)
## Consolidated Action Items (counts from aea-parse-tags, then both lists)
## Lines rewritten for grammar (before → after, or "none")
## Step 3: fixed automatically / checks with no finding / annotations quoted
## TRO / SIVACOR (Step 2b)
## Reason for incomplete reproducibility cross-check (vs Classification, vs Findings, vs live Jira)
## Decisions needed
- D1 – <short title>. Question. Evidence. Options (recommended first).
## Usage
Sub-agents used (or "none"); your own usage is reported by the harness.
```
