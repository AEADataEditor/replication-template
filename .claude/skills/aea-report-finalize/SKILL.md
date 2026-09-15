---
name: aea-report-finalize
description: Use when finishing an AEA Data Editor replication review — REPLICATION.md in an aearep-NNNN repo is filled out except SUMMARY and it's time to consolidate tags, verify the RA's findings, and draft the summary before the editor approves. Triggers on "finalize this report", "write the summary", "run the editor pass", "run aeareq", "run aea-parse-tags", "prepare this for approval", or being asked to review/finish a REPLICATION.md.
allowed-tools: Bash(git rev-parse *) Bash(git log *) Bash(git tag *) Bash(git merge-base *) Bash(git show *) Bash(grep *) Bash(head *) Bash(cut *) Bash(ls *) Bash(source *) Bash(python3 *) Bash(aea-parse-tags *)
---

# AEA Replication Report — Editor's Finishing Pass

You are the editor's finishing pass. An RA (or agent) has run the code and
filled out `REPLICATION.md` except `## SUMMARY`. You consolidate the
`[REQUIRED]`/`[SUGGESTED]` tags, independently sanity-check the findings, and
draft a short summary. **You never approve, commit the approval, or publish** —
sign-off is a human action (see Restrictions).

Derive everything (repo root, deposit directory, phrase library, ticket
number) from the repo you're in; never hard-code paths, tickets, or canned
language.

Whenever you need a decision from the user, pose it as concrete clickable
options (`AskUserQuestion`), not free-text prose.

**Rounds.** Steps 0–6 with nothing marked *revision* is the complete
first-round pass ([LDI 13-1](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-1-approving-issues-original.md)).
If Step 1 finds a revision round, read
[references/revision-rounds.md](references/revision-rounds.md) before
continuing — it adds Steps 1b/1c and extra work in Steps 3 and 5.

**Summary-only mode.** If the user asks to "just write the summary", "skip
verification", etc.: skip Step 3 entirely, treat existing tags as final (add,
remove, reinstate, or reiterate nothing), and say in Step 6 that verification
was skipped.

## Step 0 — Locate the repo

```bash
REPO_ROOT=$(git rev-parse --show-toplevel); cd "$REPO_ROOT"
ls -d [0-9]*/ 2>/dev/null   # openICPSR deposit directory
```

Stop if `REPLICATION.md` is not at `$REPO_ROOT`.

**The deposit directory is a partial copy, by design.** `.gitignore` excludes
data-like extensions (`*.dta`, `*.csv`, `*.txt`, ~100 more). A file absent
from the working tree is **not** evidence it is absent from the deposit. The
authority is `generated/manifest.txt`, the "Programs and data files provided"
appendix, and the other `generated/` reports (`duplicate-files-report.md`,
`large-file-report.md`, `zero-byte-files-report.md`, `pii-summary.md`), all
produced against the complete deposit:

```bash
find [0-9]*/ -type f | wc -l; wc -l < generated/manifest.txt
```

Never raise a finding, tag, or question premised on a missing file unless the
manifest says it is missing.

## Step 1 — Gate: already approved? revision underway?

```bash
git log --oneline | grep -E '#comment (Approved\. )?Ready to submit'
```

**No match** → first round; go to Step 2.

**Match** → take the most recent as `LAST_APPROVAL_SHA` and look for activity
after it:

```bash
LAST_APPROVAL_SHA=$(git log --oneline | grep -E '#comment (Approved\. )?Ready to submit' | head -1 | cut -d' ' -f1)
git log --oneline "${LAST_APPROVAL_SHA}..HEAD"
git tag -l 'update*'
```

Revision evidence is the pipeline's own markers in that range: commits like
`AEAREP-NNNN #comment [skip ci] Adding code from <deposit-id>`, `... Adding
generated files and logs`, `[skip ci] Downloaded Jira attachments ...`,
`[skip ci] Update of tools`, or an `updateN` tag that is a strict descendant
of `LAST_APPROVAL_SHA` (`git merge-base --is-ancestor $LAST_APPROVAL_SHA
<tag>` and the tag's SHA ≠ `LAST_APPROVAL_SHA`).

- **No evidence** → genuinely finalized. **Stop**; tell the user and ask
  before touching anything.
- **Evidence** → revision round. Do not stop, but do not trust the repo's own
  ticket references either — follow `references/revision-rounds.md` (Steps 1b,
  1c) before Step 2.

## Step 2 — Draft-readiness check

```bash
grep -n '> INSTRUCTIONS:' REPLICATION.md
grep -n 'action items go here' REPLICATION.md
```

- `> INSTRUCTIONS:` lines remaining → the draft isn't finished. List the
  section headings they fall under and tell the user before doing anything else.
- Note whether the `-----action items go here------` marker is present;
  Step 4 needs it. On a revision round its absence is expected (round 1
  consumed it) — don't flag it, Step 4 restores it.

## Step 3 — Independent verification pass

(Skipped in summary-only mode.)

Read `## Findings`, `### Missing computational requirements`, `### Tables and
Figures`, `### In-Text Numbers`, `## Classification`, `### Reason for
incomplete reproducibility`, `## Replication steps`, then cross-check:

1. **Embedded scan output** (`### PII Checks`, `#### File Paths Summary`,
   `Appendix: Candidate ... packages`, `Appendix: Possible PII`). Three
   different standards:
   - **Packages** — mechanical: a likely-used-but-unlisted package with no
     matching tag anywhere is a gap; fix per "How to act" below.
   - **PII** — loose: scans throw false positives, and a missing tag often
     means a human dismissed the hit. Check `git log -p -- REPLICATION.md`;
     a PII tag that was deliberately removed stays removed. Only tag a hit
     that has never been addressed.
   - **File paths / Windows paths** — a `NOTE` only. Never an action item,
     never in the SUMMARY; at most narrative context.
2. **Output in the deposit directory** — for tables/figures marked
   reproduced, spot-check a plausible non-empty output file exists — **but
   only for file types the repo tracks.** Check `.gitignore` first: graphics
   and typeset output (`*.png`, `*.pdf`, `*.eps`, `*.tex`, `*.log`) are
   tracked; `*.txt` and all data formats are not. For excluded types confirm
   presence via `generated/manifest.txt` and judge content only from the
   `generated/` reports.
3. **Replicator logs** (`logs/*.log`, anything cited in `## Replication
   steps`) — errors worked around but never recorded as a "Bugs in code"
   finding; unresolved errors not reflected in Classification/Reason.
4. **Stated vs. actual requirements** — `## Stated computational
   requirements` / `### Missing computational requirements` against the
   candidate-package tables.
5. **`### Reason for incomplete reproducibility`** — a checkbox restatement
   of what Classification and Findings establish. Check in this order:
   1. **Classification vs. `None.`** (mechanical): full reproduction ⇔
      `None.` is the only box checked. Anything less ⇒ `None.` unchecked and
      at least one substantive reason checked.
   2. **Findings vs. substantive reasons** (both directions): every
      documented issue (bug worked around, code that didn't run, missing
      file/dependency, inaccessible data…) has its box checked, and every
      checked box has a documented issue behind it.
   3. **Jira** — read the live `Reason for Failure to be Fully Reproduced`
      field (same credential gate as `references/revision-rounds.md`
      Step 1b; if unset, skip and note the limitation):
      ```bash
      python3 tools/jira_get_info.py <ticket> reasonforfailure
      ```
      Empty output = nothing checked. Compare on substance, not exact
      string — see the option mapping in
      [references/pipeline-context.md](references/pipeline-context.md).
      Two Jira options (`Reproduced in a previous round`, `ZIP file only -
      returned`) have no `REPLICATION.md` counterpart; never flag their
      absence. **You cannot fix Jira** — surface any mismatch in Step 6.

**How to act on what you find:**

- **Mechanical gap** (scan hit with no matching tag) — fix directly: insert
  the standard tag from `sample-language-report.md` into the relevant
  narrative section (`### Missing computational requirements`, `## Findings`),
  **never** into an `## Appendix` section.
- **Missing package / setup program** — three things, always together, in
  `### Missing computational requirements`:
  1. the verbatim `[REQUIRED]` setup-program tag for that language from the
     "Code" section of `sample-language-report.md` — never paraphrased into a
     custom one-liner; specifics (package, which program) go in a short
     untagged line beneath it;
  2. the section's checklist kept, with missing items checked and
     non-missing lines deleted (the one checklist you prune — Hygiene §1);
  3. the standing `[REQUIRED] Please amend README to contain complete
     computational requirements.` tag — required whenever any requirement is
     missing; not interchangeable with the setup-program tag.
- **Classification vs. `None.` contradiction** — fix directly (check/uncheck
  `None.`); don't guess which substantive reason applies — that's the next
  bullet.
- **Findings vs. substantive reason mismatch** — judgment: ask, naming the
  specific box and evidence.
- **`REPLICATION.md` vs. Jira mismatch** — never edit either side; alert in
  Step 6 naming the options that disagree.
- **Anything else requiring judgment** (unsupported reproduction claim,
  classification too generous/harsh) — ask with evidence ("RA marked Table 4
  reproduced but `$DEPOSIT/Output/Tables/` has no matching file — worth a
  second look?"). Never silently edit.
- **Freehand human annotations** (`@name:`, `QUESTION:`/`TODO:`/`CHECK:`, an
  RA aside) — never delete. They are not `{{ }}` markers or `> INSTRUCTION`
  lines; a person wrote them. Quote verbatim in Step 6 and let the user
  decide, even if the content is already reflected in a checkbox or tag (say
  so, still ask).

**Custom `[SUGGESTED]` tag format** (only for a gap with no predefined tag):
a short generic tagged line — `aea-parse-tags` lifts that exact line into the
checklist and the SUMMARY draws from it — then a blank line and an untagged
paragraph with the specifics:

```
- [SUGGESTED] Review candidate package dependencies not listed in requirements.

  The scan detected `haven` (R) used in `analysis/clean.R` but not listed
  under `### Stated computational requirements`.
```

*Revision rounds:* also assess the Step 1c baseline — see
`references/revision-rounds.md`.

## Step 4 — Consolidate tags with `aea-parse-tags`

From `$REPO_ROOT`, run `aea-parse-tags` (Python, from `editor-scripts`,
v0.3.13+). In one pass it: skips tags already in `### Action Items
(manuscript)`; routes each tag by its `{{ CATEGORY destination }}` marker
(`m` → manuscript, `d`/none → deposit, `both` → both); orders each checklist
by tier (`CRITICAL`, `CODE`, `FILES`, `METADATA`; unmarked = lowest) with
`[REQUIRED]` before `[SUGGESTED]`; strips `{{ }}` from the generated
checklist; removes remaining `> INSTRUCTION(S)` lines.

- **Marker missing, revision round** — re-insert the literal line
  `-----action items go here------` at the end of `### Action Items
  (openICPSR)` and rerun. Mechanical; don't ask, don't force.
- **Marker missing, any other reason** — unexpected: ask whether to restore
  it or run `aea-parse-tags force`. Never force unilaterally.
- Report the deposit/manuscript tag counts it prints.

**Spot-check routing**: nothing manuscript-only landed only in the deposit
list (or vice versa), priority order looks sane. A custom tag with no marker
falls to deposit/lowest tier; if that's wrong, add the marker to the tag line
and rerun — don't hand-reorder the generated checklist.

**Then strip leftover markers** (Hygiene §3) — mandatory before Step 6.

*Revision rounds:* run this before writing `### Previously` (Step 5).

## Step 5 — Draft the SUMMARY

Read the phrase library — `sample-language-report.md` at repo root or
`template/sample-language-report.md` — including its "Decisions" catalog.
Never rely on memorized phrasing.

Target ~150–220 words, no filler:

1. **Opening**: "Thank you for your replication archive." (revision rounds:
   see `references/revision-rounds.md`).
2. **1–2 short paragraphs**: what was/wasn't reproduced, then remaining
   `[REQUIRED]` items grouped thematically in polite imperative prose
   (code/bugs, data citations & access, README, RCT/IRB, PII, metadata); fold
   `[SUGGESTED]` items into a brief "please also consider…" aside. **Name
   categories, not specifics** — no file names, function names, or root
   causes; those live in the checklist and Findings.
3. **One bolded decision sentence** from the "Decisions" section, chosen by
   `## Classification` and whether `[REQUIRED]` items remain (full + none →
   acceptance; requireds remain → conditional-accept; partial/failed →
   "look forward to reviewing again").
   **R&R override**: if the Jira ticket title starts with "Invitation to
   Review..." or its `MCStatus` is `RR`, always use "**We look forward to
   reviewing the final replication package again after conditional
   acceptance.**" — never the "after modifications" or "Conditional on
   making the requested changes…" language, regardless of classification.
4. Boilerplate notes (e.g. the SIVACOR pilot `[NOTE]`) only if they apply.
5. **Last line, word for word**, read from `template/original-REPLICATION.md`
   (right after `> INSTRUCTION: KEEP the next line AS-IS...`): "In assessing
   compliance with our [Data and Code Availability
   Policy](https://www.aeaweb.org/journals/policies/data-code), we have
   identified the following issues, which we ask you to address:". It must
   immediately precede `### Action Items (manuscript)`. Never drop,
   paraphrase, or fold it into prose — even when replacing the SUMMARY
   wholesale.

No meta-commentary, hedging, or restating the checklist. In doubt, cut.
Write the result into `## SUMMARY`, replacing the placeholder.

## Report hygiene — every edit in Steps 2–5

Any edit not listed as mechanical in Step 3 or these rules is a judgment
call: surface it in Step 6, don't make it. `{{ }}` markers and `> INSTRUCTION`
lines are the **only** text you may remove without asking.

### 1. Never delete unchecked checklist items

Checklists are fixed menus; unchecked lines show what was considered and
rejected. Check what applies, leave every other line unchecked — in
`## General`, `## RCT`, `## Ethics/IRB Approval`, `## Stated computational
requirements`, `### Analysis Data Files`, `### In-Text Numbers`,
`## Classification`, `### Reason for incomplete reproducibility`, and every
other checklist. Three exceptions, each stated in the template's own
`> INSTRUCTIONS:` line — never infer one:

- whole sections the template says to delete when inapplicable (e.g.
  `### Experimental/Survey instructions`);
- `### Missing computational requirements` when requirements are complete:
  replace the whole section with "None";
- `### Missing computational requirements` when incomplete: check the
  missing items and delete the non-missing lines — this list becomes the
  author's to-do list, so an unchecked `Stata` line reads as a claim.

### 2. Checkboxes are exactly `[x]` / `[ ]`

`[ x]`, `[x ]`, `[  ]` render as literal text. Normalizing is mechanical —
do it without asking:

```bash
sed -i -E 's/\[ x\]/[x]/g; s/\[x \]/[x]/g' REPLICATION.md
```

Every checkbox line must start with `- ` (or nested `  - `).

### 3. Strip every `{{ ... }}` marker

This rule covers the `{{ }}` token only (freehand annotations: Step 3).
Markers are routing aids for `aea-parse-tags`, never author-facing.
`aea-parse-tags` leaves them on tag lines it skips — notably the standing
`[REQUIRED] {{ METADATA m }}` lines under `### Action Items (manuscript)`.
After Step 4:

```bash
grep -n '{{' REPLICATION.md
sed -i -E 's/(> \[(REQUIRED|SUGGESTED|STRONGLY SUGGESTED)\]) \{\{ [^}]*\}\} /\1 /g' REPLICATION.md
grep -n '{{' REPLICATION.md   # must be empty
```

## Step 6 — Report back

Show:
- the drafted SUMMARY;
- the consolidated Action Items checklists;
- Step 3: what you auto-fixed vs. what needs a decision (including quoted
  human annotations);
- the `### Reason for incomplete reproducibility` cross-check, in order:
  vs. Classification (and any `None.` fix), vs. Findings (mismatches
  flagged), and — **always stated explicitly, even when clean** — vs. the
  live Jira field, naming any discrepancy as an alert for the operator;
- *revision rounds*: the current ticket if it differs from the repo's own
  (use it in any sign-off reminder), the drafted `### Previously` section,
  and your complete/incomplete calls.

## Restrictions

- **Never** create the approval commit (`AEAREP-NNNN #comment Approved.
  Ready to submit.`), tag, push, or run `aeaready` — sign-off is the editor's
  own action (mechanics in `references/pipeline-context.md`).
- **Never** fabricate a finding, package name, or file path not backed by
  evidence in the repo.
- **Never** invent canned language — use `sample-language-report.md`.
- **Never** write to Jira (no comments, no `.update()`); only read via
  `jira_find_task_by_icpsr.py` / `jira_get_info.py`.
- **Never modify anything from `# Automatically Generated Appendices` to the
  end of `REPLICATION.md`**, nor a standalone `generated/REPLICATION_appendix.md`
  — `aeaready` regenerates it at sign-off, discarding edits. Read it freely;
  respond to scan findings in the narrative sections instead.
- **Never** resolve the `.../openicpsr/xxxxx` placeholder URL or add/guess a
  DOI — `aeaready` fills both from Jira.
- Finalized repo (Step 1, no post-approval activity): stop and ask. A
  revision in progress is not a reason to stop.
