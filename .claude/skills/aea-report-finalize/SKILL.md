---
name: aea-report-finalize
description: Use when finishing an AEA Data Editor replication review — REPLICATION.md in an aearep-NNNN repo is filled out except SUMMARY and it's time to consolidate tags, verify the RA's findings, and draft the summary before the editor approves. Triggers on "finalize this report", "write the summary", "run the editor pass", "run aea-parse-tags", "prepare this for approval", or being asked to review/finish a REPLICATION.md.
allowed-tools: Bash(git rev-parse *) Bash(git log *) Bash(git tag *) Bash(git merge-base *) Bash(git show *) Bash(grep *) Bash(head *) Bash(cut *) Bash(ls *) Bash(find *) Bash(source *) Bash(python3 *) Bash(aea-parse-tags *)
---

# AEA Replication Report — Editor's Finishing Pass

Role: editor's finishing pass. `REPLICATION.md` is filled except `## SUMMARY`.
Consolidate `[REQUIRED]`/`[SUGGESTED]` tags, sanity-check findings, draft the
summary. **Never approve, commit the approval, or publish** (Restrictions).

Derive repo root, deposit dir, phrase library, ticket from the repo; never
hard-code them. Ask the user for decisions via `AskUserQuestion` (clickable
options).

## Critical path — every time, in order

Long inputs push toward writing a plausible summary from memory. Don't.

1. Run `aea-parse-tags` (Step 4) before drafting. Write the SUMMARY from its
   checklists. Tool missing → stop (Step 0).
2. Read `sample-language-report.md` this session (Step 5). It is a lookup
   table, not background.
3. Copy tags and the decision sentence **verbatim**. Custom tag only when no
   predefined one fits (format in Step 3).
4. SUMMARY's last line verbatim from `template/original-REPLICATION.md`.
5. Run Step 5b; report it in Step 6.

## Modes

- **Rounds**: Steps 0–6 with no revision = first round
  ([LDI 13-1](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-1-approving-issues-original.md)).
  Revision found in Step 1 → read
  [references/revision-rounds.md](references/revision-rounds.md) (adds Steps
  1b/1c, extra work in Steps 3 and 5).
- **Summary-only** ("just write the summary", "skip verification"): skip
  Step 3, treat tags as final (no add/remove/reinstate), say in Step 6 that
  verification was skipped.

## Step 0 — Locate the repo

```bash
REPO_ROOT=$(git rev-parse --show-toplevel); cd "$REPO_ROOT"
ls -d [0-9]*/ 2>/dev/null   # openICPSR deposit dir
command -v aea-parse-tags
```

- No `REPLICATION.md` at `$REPO_ROOT` → stop.
- `aea-parse-tags` is the only consolidation tool. Not found → stop, tell the
  user it isn't installed. Don't search for or substitute another tool.

**Deposit dir is a partial copy.** `.gitignore` excludes data-like extensions
(`*.dta`, `*.csv`, `*.txt`, ~100 more); absence from the tree ≠ absence from
the deposit. Authority: `generated/manifest.txt`, the "Programs and data files
provided" appendix, `generated/{duplicate-files,large-file,zero-byte-files}-report.md`,
`generated/pii-summary.md`.

```bash
find [0-9]*/ -type f | wc -l; wc -l < generated/manifest.txt
```

Raise no finding/tag/question about a missing file unless the manifest says
it's missing.

## Step 1 — Gate: already approved? revision underway?

```bash
git log --oneline | grep -E '#comment (Approved\. )?Ready to submit'
```

- **No match** → first round → Step 2.
- **Match** → `LAST_APPROVAL_SHA` = most recent; look for later activity:

```bash
LAST_APPROVAL_SHA=$(git log --oneline | grep -E '#comment (Approved\. )?Ready to submit' | head -1 | cut -d' ' -f1)
git log --oneline "${LAST_APPROVAL_SHA}..HEAD"
git tag -l 'update*'
```

Revision evidence in that range: pipeline commits (`AEAREP-NNNN #comment
[skip ci] Adding code from <deposit-id>`, `... Adding generated files and
logs`, `[skip ci] Downloaded Jira attachments ...`, `[skip ci] Update of
tools`) or an `updateN` tag strictly descending from `LAST_APPROVAL_SHA`
(`git merge-base --is-ancestor $LAST_APPROVAL_SHA <tag>`, tag SHA ≠
`LAST_APPROVAL_SHA`).

- **None** → finalized. **Stop**, tell the user, ask before touching anything.
- **Some** → revision round. Don't trust the repo's ticket references; follow
  `references/revision-rounds.md` (1b, 1c) before Step 2.

## Step 2 — Draft-readiness

```bash
grep -n '> INSTRUCTIONS:' REPLICATION.md
grep -n 'action items go here' REPLICATION.md
```

- `> INSTRUCTIONS:` remaining → draft unfinished; list their section headings
  and tell the user first.
- Note whether `-----action items go here------` exists (Step 4 needs it).
  Revision round: absence expected, don't flag.

## Step 2b — TRO check

```bash
find . -path "*/tro/tro-*.jsonld" -not -path "./.git/*"
```

No TRO → skip. TRO found → read [references/tro.md](references/tro.md) and
apply it here, in Step 5.4, and in Step 6.

## Step 3 — Independent verification

Skipped in summary-only mode. Read `## Findings`, `### Missing computational
requirements`, `### Tables and Figures`, `### In-Text Numbers`, `##
Classification`, `### Reason for incomplete reproducibility`, `## Replication
steps`. Cross-check:

1. **Embedded scan output** (`### PII Checks`, `#### File Paths Summary`,
   `Appendix: Candidate ... packages`, `Appendix: Possible PII`):
   - Packages — mechanical: likely-used, unlisted, no matching tag = gap; fix
     per "How to act".
   - PII — loose: false positives common; a missing tag often means a human
     dismissed it. Check `git log -p -- REPLICATION.md`; deliberately removed
     PII tags stay removed. Tag only never-addressed hits.
   - File/Windows paths — `NOTE` only; never an action item or in SUMMARY.
2. **Outputs in deposit dir** — spot-check a non-empty output exists for
   tables/figures marked reproduced, **only for tracked types**: `*.png`,
   `*.pdf`, `*.eps`, `*.tex`, `*.log` tracked; `*.txt` and data formats not
   (check `.gitignore`). Excluded types: confirm via `generated/manifest.txt`,
   judge content from `generated/` reports only.
3. **Replicator logs** (`logs/*.log`, cited in `## Replication steps`) —
   errors worked around but not recorded as "Bugs in code"; unresolved errors
   missing from Classification/Reason.
4. **Stated vs. actual requirements** — `## Stated computational
   requirements` / `### Missing computational requirements` vs. candidate-package
   tables.
5. **`### Reason for incomplete reproducibility`** — must restate
   Classification + Findings. In order:
   1. *Classification vs. `None.`* (mechanical): full reproduction ⇔ `None.`
      is the only box checked. Otherwise `None.` unchecked + ≥1 substantive
      reason checked.
   2. *Findings vs. reasons* (both ways): every documented issue (workaround
      bug, code that didn't run, missing file/dependency, inaccessible data)
      has its box; every checked box has a documented issue.
   3. *Jira*: read the live field (credential gate as in
      `references/revision-rounds.md` Step 1b; unset → skip, note it):
      ```bash
      python3 tools/jira_get_info.py <ticket> reasonforfailure
      ```
      Empty = nothing checked. Compare on substance; option mapping in
      [references/pipeline-context.md](references/pipeline-context.md). Two
      Jira-only options (`Reproduced in a previous round`, `ZIP file only -
      returned`) — never flag absence. **Can't fix Jira**; surface mismatch in
      Step 6.

**How to act:**

- **Mechanical gap** (scan hit, no tag) → insert the standard tag from
  `sample-language-report.md` into `### Missing computational requirements`
  or `## Findings`, **never** an `## Appendix`.
- **Missing package/setup program** → all three, in `### Missing
  computational requirements`:
  1. verbatim `[REQUIRED]` setup-program tag for the language ("Code"
     section of `sample-language-report.md`); specifics (package, program) in
     a short untagged line beneath;
  2. section checklist kept: missing items checked, non-missing lines deleted
     (the one checklist you prune — Hygiene §1);
  3. standing `[REQUIRED] Please amend README to contain complete
     computational requirements.` (needed whenever any requirement is
     missing; not interchangeable with the setup-program tag).
- **Classification vs. `None.`** → fix directly; don't guess the substantive
  reason.
- **Findings vs. reason mismatch** → ask, naming box and evidence.
- **REPLICATION.md vs. Jira mismatch** → edit neither; alert in Step 6 naming
  disagreeing options.
- **Other judgment** (unsupported reproduction claim, classification too
  generous/harsh) → ask with evidence ("RA marked Table 4 reproduced but
  `$DEPOSIT/Output/Tables/` has no matching file"). Never silently edit.
- **Freehand human annotations** (`@name:`, `QUESTION:`/`TODO:`/`CHECK:`, RA
  asides) → never delete (not `{{ }}` or `> INSTRUCTION`). Quote verbatim in
  Step 6, let the user decide, even if already reflected elsewhere.

**Custom `[SUGGESTED]` tag** (no predefined tag fits): short generic tagged
line (`aea-parse-tags` lifts this exact line), blank line, untagged specifics:

```
- [SUGGESTED] Review candidate package dependencies not listed in requirements.

  The scan detected `haven` (R) used in `analysis/clean.R` but not listed
  under `### Stated computational requirements`.
```

Revision rounds: also assess the Step 1c baseline (`references/revision-rounds.md`).

## Step 4 — Consolidate with `aea-parse-tags`

Run from `$REPO_ROOT` (`editor-scripts` v0.3.13+). It: skips tags already in
`### Action Items (manuscript)`; routes by `{{ CATEGORY destination }}`
(`m` → manuscript, `d`/none → deposit, `both` → both); orders by tier
(`CRITICAL`, `CODE`, `FILES`, `METADATA`; unmarked lowest), `[REQUIRED]` before
`[SUGGESTED]`; strips `{{ }}` from the generated checklist; removes
`> INSTRUCTION(S)` lines.

- **Marker missing, revision round** → re-insert `-----action items go
  here------` at end of `### Action Items (openICPSR)`, rerun. Don't ask.
- **Marker missing otherwise** → ask: restore, or `aea-parse-tags force`.
  Never force unilaterally.
- Report the deposit/manuscript tag counts it prints.
- **Spot-check routing**: nothing manuscript-only in the deposit list (or
  vice versa); priority order sane. Unmarked custom tag lands deposit/lowest;
  if wrong, add the marker to the tag line and rerun — don't hand-reorder.
- Then strip leftover markers (Hygiene §3) — mandatory before Step 6.
- Revision rounds: before writing `### Previously`.

## Step 5 — Draft the SUMMARY

Read `sample-language-report.md` (repo root or `template/`), incl. "Decisions".
Never use memorized phrasing. Target ~150–220 words, no filler.

1. **Opening**: "Thank you for your replication archive." (revision: see
   `references/revision-rounds.md`).
2. **1–2 short paragraphs**: what was/wasn't reproduced; remaining
   `[REQUIRED]` items grouped thematically, polite imperative (code/bugs, data
   citations & access, README, RCT/IRB, PII, metadata); `[SUGGESTED]` folded
   into a brief "please also consider…". **Categories, not specifics** — no
   file/function names or root causes.
3. **One bolded decision sentence** from "Decisions", by `## Classification`
   and whether `[REQUIRED]` remain: full + none → acceptance; requireds
   remain → conditional-accept; partial/failed → "look forward to reviewing
   again".
   **R&R override**: Jira title starts "Invitation to Review..." or `MCStatus`
   = `RR` → always "**We look forward to reviewing the final replication
   package again after conditional acceptance.**" — never "after
   modifications" / "Conditional on making the requested changes…".
4. Boilerplate notes (e.g. SIVACOR pilot `[NOTE]`) only if applicable. TRO
   deposit → "trusted verification system" wording from
   `sample-language-report.md`.
5. **Last line, verbatim**, from `template/original-REPLICATION.md` (after
   `> INSTRUCTION: KEEP the next line AS-IS...`): "In assessing compliance
   with our [Data and Code Availability
   Policy](https://www.aeaweb.org/journals/policies/data-code), we have
   identified the following issues, which we ask you to address:". Must
   immediately precede `### Action Items (manuscript)`. Never drop,
   paraphrase, or fold into prose, even when replacing the SUMMARY wholesale.

No meta-commentary, hedging, or checklist restatement. In doubt, cut. Write
into `## SUMMARY`, replacing the placeholder.

## Step 5b — Verbatim self-check

Before Step 6, check mechanically:

1. Every non-custom `[REQUIRED]`/`[SUGGESTED]` line occurs character for
   character in `sample-language-report.md`:
   ```bash
   grep -F -c -- "<tag text>" sample-language-report.md
   ```
   0 → paraphrased/invented: replace with library text, or reformat as a
   custom `[SUGGESTED]` tag (Step 3).
2. Decision sentence is in "Decisions"; last line matches
   `template/original-REPLICATION.md`.
3. SUMMARY names categories only (Step 5.2).

Fix failures, then report in Step 6.

## Report hygiene — every edit in Steps 2–5

Edits not listed as mechanical in Step 3 or here are judgment calls: surface
in Step 6. `{{ }}` markers and `> INSTRUCTION` lines are the **only** text
removable without asking.

### 1. Never delete unchecked checklist items

Checklists are fixed menus; unchecked lines show what was rejected. Check what
applies, leave the rest — in `## General`, `## RCT`, `## Ethics/IRB Approval`,
`## Stated computational requirements`, `### Analysis Data Files`, `###
In-Text Numbers`, `## Classification`, `### Reason for incomplete
reproducibility`, all others. Exceptions (each stated in the template's own
`> INSTRUCTIONS:` line — never infer one):

- whole sections the template says to delete when inapplicable (e.g. `###
  Experimental/Survey instructions`);
- `### Missing computational requirements`, requirements complete → replace
  whole section with "None";
- same section, incomplete → check missing items, delete non-missing lines
  (it becomes the author's to-do list; an unchecked `Stata` reads as a claim).

### 2. Checkboxes are exactly `[x]` / `[ ]`

`[ x]`, `[x ]`, `[  ]` render literally. Normalize without asking:

```bash
sed -i -E 's/\[ x\]/[x]/g; s/\[x \]/[x]/g' REPLICATION.md
```

Every checkbox line starts with `- ` (or nested `  - `).

### 3. Strip every `{{ ... }}` marker

`{{ }}` token only (annotations: Step 3). `aea-parse-tags` leaves markers on
tag lines it skips, e.g. standing `[REQUIRED] {{ METADATA m }}` under `###
Action Items (manuscript)`. After Step 4:

```bash
grep -n '{{' REPLICATION.md
sed -i -E 's/(> \[(REQUIRED|SUGGESTED|STRONGLY SUGGESTED)\]) \{\{ [^}]*\}\} /\1 /g' REPLICATION.md
grep -n '{{' REPLICATION.md   # must be empty
```

## Step 6 — Report back

Show:
- Step 5b result (fixed, or "clean");
- drafted SUMMARY;
- consolidated Action Items checklists;
- Step 3: auto-fixed vs. needs decision (incl. quoted annotations);
- Step 2b: TRO found?, Part B generated?, "trusted verification system" box
  state;
- `### Reason for incomplete reproducibility` cross-check, in order: vs.
  Classification (and any `None.` fix), vs. Findings (mismatches), and —
  **always explicit, even if clean** — vs. live Jira field (discrepancies as
  operator alert);
- revision rounds: current ticket if it differs from the repo's (use in any
  sign-off reminder), drafted `### Previously`, complete/incomplete calls.

## Restrictions

- **Never** create the approval commit (`AEAREP-NNNN #comment Approved. Ready
  to submit.`), tag, push, or run `aeaready` — editor-only
  (`references/pipeline-context.md`).
- **Never** fabricate findings, package names, or paths.
- **Never** invent canned language; use `sample-language-report.md`.
- **Never** write to Jira; read only via `jira_find_task_by_icpsr.py` /
  `jira_get_info.py`.
- **Never** modify anything from `# Automatically Generated Appendices` to
  end of `REPLICATION.md`, nor `generated/REPLICATION_appendix.md` (`aeaready`
  regenerates it). Read freely; respond in narrative sections.
- **Never** resolve the `.../openicpsr/xxxxx` placeholder URL or add/guess a
  DOI (`aeaready` fills both from Jira).
- Finalized repo (Step 1, no post-approval activity): stop and ask. Revision
  in progress is not a reason to stop.
