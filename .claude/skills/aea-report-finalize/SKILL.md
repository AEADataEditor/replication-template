---
name: aea-report-finalize
description: Use when finishing an AEA Data Editor replication review — the RA (or transparency-editor agent) has already filled out REPLICATION.md in an aearep-NNNN repo and it's time to run aea-parse-tags, write the SUMMARY, and double-check the replicator's findings before the editor approves. Triggers on requests like "finalize this report", "write the summary", "run the editor pass", "run aeareq", "run aea-parse-tags", "prepare this for approval", or being asked to review/finish a REPLICATION.md in an aearep-NNNN directory.
allowed-tools: Bash(git rev-parse *) Bash(git log *) Bash(git tag *) Bash(git merge-base *) Bash(git show *) Bash(grep *) Bash(head *) Bash(cut *) Bash(ls *) Bash(source *) Bash(python3 *) Bash(aea-parse-tags *)
---

# AEA Replication Report — Editor's Finishing Pass

You are acting as the AEA Data Editor's finishing pass on a replication
review. An RA (or an automated agent) has already run the replication code
and filled out `REPLICATION.md` — everything except `## SUMMARY`. Your job
mirrors what the human editor actually does: consolidate the `[REQUIRED]`/
`[SUGGESTED]` tags, independently sanity-check the RA's findings, and draft a
short, non-chatty summary. **You do not approve or publish anything** —
sign-off is a human action (see Restrictions).

Do not hard-code paths, ticket numbers, or canned language in your own
reasoning — derive everything (repo root, deposit directory, phrase
library) from the repo you're actually working in, since these drift across
repos and template versions.

**Whenever this skill needs to ask the user something** — confirming
whether to touch an already-approved repo (Step 1), a judgment call from the
verification pass (Step 3), or whether to force `aea-parse-tags` past a
missing marker (Step 4) — pose it as concrete, clickable options (e.g. via
`AskUserQuestion`), not a vague prose question waiting on free-text
approval. This applies whether the session is in a terminal or the VS Code
panel.

**Normal path vs. revision path**: Steps 2–6 below, on their own, are the
complete first-round finishing pass and match the LDI Lab's approver
guidance for an original (non-revision) report — see
[13-1-approving-issues-original.md](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-1-approving-issues-original.md).
A first-round case never touches anything marked "revision rounds only"
below. Revision rounds (detected in Step 1/1b) add extra requirements at
Steps 1c, 3, and 5, per
[12-jira-revision-guidance.md](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/12-jira-revision-guidance.md)
(replicator-facing) and
[13-2-approving-issues-revision.md](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-2-approving-issues-revision.md)
(approver-facing).

## Modes

By default this skill runs the full pass (Steps 0–6). If the user asks to
"just write the summary", "summarize the existing tags", "skip
verification", or otherwise invokes a **summary-only** mode, skip Step 3 (the
independent verification pass) entirely: go from Step 2 straight to Step 4,
treating whatever `[REQUIRED]`/`[SUGGESTED]` tags already exist in
`REPLICATION.md` as final. Do not add, remove, reinstate, or reiterate any
tag based on scan output, deposit files, logs, or judgment calls in this
mode — Step 5's SUMMARY and Step 4's checklist are built purely from tags
the RA (or a prior pass) already left in the document. Say explicitly in
Step 6 that verification was skipped, so the human editor knows this pass
didn't independently check the RA's work.

## Step 0 — Locate the repo and its parts

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"
ls -d [0-9]*/ 2>/dev/null   # the openICPSR numbered deposit directory
```

Confirm `REPLICATION.md` exists at `$REPO_ROOT`. If it doesn't, stop — this
isn't a replication-template repo, or you're in the wrong directory.

## Step 1 — Gate: is this already approved, and is a follow-up round underway?

```bash
git log --oneline | grep -E '#comment (Approved\. )?Ready to submit'
```

**No match** — never approved. This is a first-round case; proceed to Step 2.

**One or more matches** — take the most recent one as `LAST_APPROVAL_SHA`
(pre-approved for this skill — see frontmatter):

```bash
LAST_APPROVAL_SHA=$(git log --oneline | grep -E '#comment (Approved\. )?Ready to submit' | head -1 | cut -d' ' -f1)
```

and check for evidence of activity *after* it:

```bash
git log --oneline "${LAST_APPROVAL_SHA}..HEAD"
git tag -l 'update*'
```

Look for the pipeline's own automated markers in that post-approval range —
this is the real trail the tooling leaves behind when it re-runs for a
revision (concretely observed on `aearep-9147`): commits like
`AEAREP-NNNN #comment [skip ci] Adding code from <deposit-id>`,
`... Adding generated files and logs`, `[skip ci] Downloaded Jira
attachments for AEAREP-NNNN`, `[skip ci] Update of tools`, or an `updateN`
tag whose commit is a descendant of (not equal to) `LAST_APPROVAL_SHA`
(`git merge-base --is-ancestor $LAST_APPROVAL_SHA <tag>` confirms "after",
then check the tag's SHA isn't `LAST_APPROVAL_SHA` itself).

- **No such evidence** → genuinely finalized. **Stop.** Tell the user this
  repo already has an approval commit with nothing after it, and ask before
  touching it further.
- **Evidence found** → a revision round is in progress, not a finished case.
  Do **not** stop — but don't trust the repo's own ticket references for
  what to call "the current case." Continue to Step 1b before proceeding.

## Step 1b — Confirm the current ticket via Jira (only if Step 1 found a revision in progress)

AEA opens a **new Jira ticket for each revision round**, while the work
continues in the same physical repo — the repo's own history (`config.yml`'s
`jiraticket:` field, every commit message) keeps referencing the *original*
round's ticket forever and never mentions the new one. (Confirmed on
`aearep-9147`: every commit says `AEAREP-9147`, but its live revision round
is tracked under a different, higher-numbered ticket in Jira.) So once
Step 1 shows a revision is underway, find the ticket that's actually current:

```bash
[ -n "$JIRA_USERNAME" ] && [ -n "$JIRA_API_KEY" ] && echo "jira env OK"
```

If unset, try `source ~/.envvars` and recheck. If still unset, tell the user
Jira confirmation isn't possible and fall back to git-only evidence from
Step 1 — don't block on this, just note the limitation.

If credentials are available, find the openICPSR deposit ID for the current
round (`config.yml`'s `openicpsr:` field, the bare-digit deposit directory
at repo root, or the most recent `Adding code from <id>` commit), then:

```bash
python3 tools/jira_find_task_by_icpsr.py <deposit-id>
```

(Prints nothing on missing credentials or no match; try `python3.12` if
`python3` isn't the right interpreter on this machine.) This returns the
**highest-numbered** — i.e. most current — Jira Task tracking that deposit
ID. Compare it against the ticket embedded in the repo's own history:

- **Same ticket** → the repo's history already reflects the current round;
  proceed normally, referring to it by its usual number.
- **Different, higher-numbered ticket** → *that* is the live ticket for this
  round. Use it — not the repo's own — anywhere you refer to "the current
  case" for the rest of this pass, including the final report (Step 6) and
  any reminder about what commit message the editor should eventually use
  for sign-off.

Then continue to Step 1c, treating this as an active revision round.

## Step 1c — Baseline the round-1 requests (revision rounds only)

Skip this step entirely for a first-round case.

Pull the exact text the previous round was approved with — this is the
authoritative record of what round 1 actually asked for, not what you
remember or infer from the current draft:

```bash
git show ${LAST_APPROVAL_SHA}:REPLICATION.md
```

Extract its `### Action Items (manuscript)` and `### Action Items
(openICPSR)` checklists as the round-1 baseline. You'll need this list in
Step 3 (to assess each item complete/incomplete against round-2 evidence)
and in Step 5 (to build the `### Previously` section).

## Step 2 — Draft-readiness check

```bash
grep -n '> INSTRUCTIONS:' REPLICATION.md
grep -n 'action items go here' REPLICATION.md
```

- If `> INSTRUCTIONS:` lines remain, the RA's draft isn't finished — list the
  section headings they fall under and tell the user before doing anything
  else.
- Note whether the `-----action items go here------` marker is present.
  `aea-parse-tags` refuses to run without it (unless forced) — you'll need
  this in Step 4.
- **If Step 1/1b established this is a revision round, a missing marker is
  expected, not a problem.** `aea-parse-tags` deletes the marker after every
  successful run, and round 1 already consumed it — it does not come back on
  its own for round 2+. Don't flag this as an RA drafting issue or ask the
  user why it's missing; just note it and move on to Step 4, which handles
  restoring it.

## Step 3 — Independent verification pass

Skip this entire step if the summary-only mode (see Modes, above) applies.

This is the part of the editor's job that catches what the RA missed: read
`REPLICATION.md`'s `## Findings`, `### Missing computational requirements`,
`### Tables and Figures`, `### In-Text Numbers`, `## Classification`,
`### Reason for incomplete reproducibility`, and `## Replication steps`
sections closely, then cross-check:

1. **Scan output already embedded in the report** (`### PII Checks`,
   `#### File Paths Summary`, the `Appendix: Candidate ... packages` tables,
   `Appendix: Possible PII`) — but the three kinds of scan output don't get
   the same treatment:
   - **Packages**: mechanical, same as before. A likely-used-but-unlisted
     package with no corresponding `[REQUIRED]`/`[SUGGESTED]` tag anywhere in
     the report is a gap the RA missed — fix it directly per "How to act on
     what you find," below.
   - **PII**: a *loose* requirement, not a mechanical one. A PII hit with no
     tag is not automatically a gap — PII scans throw false positives
     routinely, and a missing tag often means a human already looked at the
     hit and dismissed it. Check `git log -p -- REPLICATION.md` (or the
     document's own history/narrative) for whether a `[REQUIRED]` PII tag
     existed at some point and was deliberately removed. If it was removed,
     leave it removed — do **not** reinstate it just because the scan output
     still shows the hit. Only raise a fresh tag for a PII hit that has never
     been addressed at all.
   - **File paths / Windows paths** (`#### File Paths Summary`): this is a
     simple `NOTE`, never a `[REQUIRED]`/`[SUGGESTED]` action item. Don't add
     or restore an action-item tag for a path finding, and don't treat an
     untagged path hit as a gap. At most, mention it in the narrative as
     informational context — it never escalates to Action Items or the
     SUMMARY's issue list.
2. **Actual output in the numbered deposit directory** — for tables/figures
   the RA marked reproduced, spot check that a plausible output file exists
   (non-empty, sane modification time). A "Yes"/checked box with nothing to
   back it up is a red flag.
3. **Replicator log files** (`logs/*.log` or similar, and anything
   referenced in `## Replication steps`) — look for errors that were worked
   around but never turned into a "Bugs in code" finding, or unresolved
   errors that Classification/Reason-for-incomplete-reproducibility doesn't
   reflect.
4. **Stated vs. actual requirements** — compare `## Stated computational
   requirements` / `### Missing computational requirements` against the
   candidate-package scan tables for dependencies the RA didn't list.

**How to act on what you find:**
- Objective, mechanical gaps (a scan hit with zero matching tag anywhere in
  the doc) — fix directly: insert the standard tag text pulled from
  `sample-language-report.md` (see Step 5) into the right section — the
  relevant narrative section (e.g. `### Missing computational requirements`,
  `## Findings`), **never** into the `## Appendix: ...` section itself (see
  Restrictions — those are auto-generated and read-only).
- **Missing package/setup-program gap, specifically** (a scan hit for a
  package not covered by any provided setup code): this always touches
  `### Missing computational requirements`, and always needs *two* things
  together, never just one:
  1. The exact, verbatim `[REQUIRED]` setup-program tag for that language
     from the "Code" section of `sample-language-report.md` (e.g. the Stata
     "Please add a setup program that installs all Stata packages..." tag).
     Do **not** paraphrase it into a custom one-liner naming the specific
     package — the specifics (package name, which program needed it) go in
     a short, untagged explanation directly beneath the verbatim tag
     instead, limited to what's actually missing.
  2. The checklist in `### Missing computational requirements` itself must
     be left in the report with the relevant item(s) checked (and
     irrelevant/non-missing lines deleted) — never rely on the tag text
     alone as a substitute for the checklist.
  3. The standing `[REQUIRED] Please amend README to contain complete
     computational requirements.` tag from that same section must also be
     present alongside the setup-program tag — it's required whenever *any*
     computational requirement is missing, not just when the README section
     itself is the gap, and it is not interchangeable with the
     setup-program tag.
- Anything requiring judgment (a reproduction claim that looks unsupported,
  a classification that seems too generous/harsh) — do **not** silently
  edit. Surface it to the user as a specific, evidence-backed question
  ("RA marked Table 4 reproduced but `$DEPOSIT/Output/Tables/` has no file
  matching that name — worth a second look?").

**Format for any custom `[SUGGESTED]` tag you author** (here, and in the
revision-round reiteration below) — this applies to a genuinely novel gap
with no predefined tag in `sample-language-report.md`; a missing
package/setup-program gap already has a predefined verbatim tag, see above,
and should never be paraphrased into one of these instead: keep the tagged
line itself a short, generic one-liner. `aea-parse-tags` pulls that exact
line into the Action Items checklist, and Step 5's SUMMARY draws only from
that same line — a long or over-specific tag line makes the checklist and
SUMMARY verbose. Put the specifics (which scan hit, which file, which
package, why) in a plain, untagged paragraph directly beneath it, separated
by one blank line:

```
- [SUGGESTED] Review candidate package dependencies not listed in requirements.

  The scan detected `haven` (R) used in `analysis/clean.R` but not listed
  under `### Stated computational requirements`.
```

**Revision rounds only** — also assess the Step 1c baseline: for each
round-1 `[REQUIRED]`/`[SUGGESTED]` item, check the same evidence you're
already gathering above (embedded scan output, deposit files, logs, current
`## Findings`) to decide complete or incomplete. This is expected to be
messy — **it's normal for round 1's `## SUMMARY` to already look
inconsistent with what the RA found this round**; nobody touches SUMMARY
between rounds, so don't treat the mismatch itself as a finding, just work
from the current evidence. For anything you judge **incomplete**, make sure
a fresh `[REQUIRED]`/`[SUGGESTED]` tag for it exists somewhere in the
current draft (reiterating it) — add one yourself if the RA didn't, using
the round-1 text as a starting point. This is the mechanical rule from
12-jira-revision-guidance.md ("items the authors did not adequately address
[are reiterated] as new `[REQUIRED]` tags"), not a judgment call, so apply
it directly. Keep your complete/incomplete determination and one-line
reasoning per item — you'll need it in Step 5.

## Step 4 — Consolidate tags with `aea-parse-tags`

From `$REPO_ROOT`:

```bash
aea-parse-tags
```

`aea-parse-tags` (Python, `pip install`-ed from the `editor-scripts` repo,
v0.3.13+) is the replacement for the old bash `aeareq` script — same job,
consolidate `[REQUIRED]`/`[SUGGESTED]` tags into the Action Items
checklists, but it now does in one pass what this skill previously had to
do by hand afterward:

- **Skips tags already present in `### Action Items (manuscript)`**
  (e.g. the two standing response-letter / returning-proofs `[REQUIRED]`
  lines) instead of sweeping duplicates into the deposit checklist.
- **Routes each tag by its `{{ CATEGORY destination }}` marker**
  (`m` → manuscript checklist, `d` or no marker → deposit checklist,
  `both` → both) — reading the marker straight from the tag line, not from
  a manual scan of the file.
- **Orders each checklist by priority tier** (`CRITICAL`, `CODE`, `FILES`,
  `METADATA`, from `sample-language-report.md`'s "Priority order for Action
  Items" section — unmarked tags default to the lowest tier), with
  `[REQUIRED]` before `[SUGGESTED]` as a tiebreak within a tier.
- **Strips every `{{ ... }}` marker** from the final checklist text.
- **Removes any remaining `> INSTRUCTION(S)` lines** (like `aeaclean`).

Because of this, the manual routing/reordering/marker-stripping work this
skill used to require after running `aeareq` is no longer needed — just run
`aea-parse-tags` and check its output.

- **If Step 2 flagged this as an expected revision-round marker absence**:
  just restore it yourself — re-insert the literal line
  `-----action items go here------` at the end of the
  `### Action Items (openICPSR)` section (matching the template's original
  placement), then re-run `aea-parse-tags` normally. This is a mechanical,
  known-cause fix, not a judgment call — no need to ask the user or use
  `force`.
- **If the marker is missing for any other reason** (e.g. a first-round
  draft where it shouldn't be missing at all): that's unexpected — ask the
  user whether to restore the marker or run `aea-parse-tags force` (or
  `--force`/`-f`), rather than guessing. Don't force it unilaterally, since
  forcing skips a real safety check.
- Report back the deposit/manuscript tag counts it prints.

**Spot-check the routing** rather than redoing it by hand: skim both
checklists afterward and confirm nothing manuscript-only ended up only in
the deposit list (or vice versa) and that the priority order looks sane.
`aea-parse-tags` only sees markers actually present on a tag line — a
custom tag you or the RA wrote directly in `REPLICATION.md` with no
`{{ CATEGORY }}` marker at all silently falls to the deposit checklist and
the lowest priority tier by default; if that placement looks wrong for a
specific custom tag, add the appropriate marker to the tag line yourself
and re-run, rather than manually reordering the generated checklist.

**Revision-round ordering**: run `aea-parse-tags` before writing the
`### Previously` section (Step 5) is still the sensible order to work in,
though it's no longer load-bearing the way it was under `aeareq` — the old
script matched the raw substring `SUGGESTED` anywhere in a line, so a
historical `> [We SUGGESTED] ...` record from a prior round could get
mistaken for a fresh ask; `aea-parse-tags` instead requires the literal
bracket form `[SUGGESTED]`/`[REQUIRED]`/`[STRONGLY SUGGESTED]`, which
`[We SUGGESTED]` does not match, so it no longer misfires on that text.

## Step 5 — Draft the SUMMARY

Read the phrase library in the current repo — `sample-language-report.md` at
the repo root, or `template/sample-language-report.md` — for the current
canned language and the "Decisions" catalog. Do not rely on memorized
phrasing; this file is the source of truth and can change.

Structure, calibrated against real approved summaries (AEAREP-8010,
AEAREP-8434 — both ~150–220 words, no filler):

1. **Opening**: "Thank you for your replication archive." (or "revised
   replication archive" on a second/later round).
2. **1–2 short paragraphs**: what was/wasn't reproduced, then the remaining
   `[REQUIRED]` items grouped *thematically* in polite imperative prose
   (code/bugs, data citations & access, README completeness, RCT/IRB, PII,
   deposit metadata) — don't restate every checklist line individually, just
   the substance grouped sensibly. Fold in `[SUGGESTED]` items as a brief
   "please also consider..." aside if there are any. **Stay generic here —
   name categories of issues ("some bugs", "duplicate files"), not specifics**
   (file names, function names, exact root causes). Those specifics already
   live in the Action Items checklist entries (Step 4's dedup/priority pass)
   and the `## Findings`/`### Missing computational requirements` narrative — the SUMMARY
   is a cover note, not a second copy of the detail (confirmed against the
   editor's own simplification on `aearep-9752`: a first-draft SUMMARY
   listing specific file paths and package names was cut down to two
   sentences naming only the issue categories).
3. **One bolded decision sentence**, picked from the "Decisions" section of
   `sample-language-report.md` based on the report's `## Classification`
   checkbox and whether `[REQUIRED]` items remain (full reproduction + no
   requireds → acceptance language; requireds remain → conditional-accept
   language; partial/failed reproduction → the stronger "look forward to
   reviewing again" language).
4. Only append boilerplate notes (e.g. the SIVACOR pilot `[NOTE]`) if they
   apply to this case — check the phrase library, don't include by default.
5. **End the SUMMARY with the fixed closing sentence, word for word:**
   "In assessing compliance with our [Data and Code Availability
   Policy](https://www.aeaweb.org/journals/policies/data-code), we have
   identified the following issues, which we ask you to address:" — this is
   the transition into the Action Items lists and must always be the last
   line of `## SUMMARY`, immediately before `### Action Items (manuscript)`.
   Don't hardcode it from memory here either: read it off
   `template/original-REPLICATION.md` in the current repo (the frozen,
   per-repo copy of the blank template — same line, right after the
   `> INSTRUCTION: KEEP the next line AS-IS...` comment) so you're using
   this repo's actual current wording, not a remembered one. This applies
   even when you're otherwise replacing the SUMMARY wholesale (see the
   revision-round note below) — never drop it, paraphrase it, or fold it
   into your own prose.

**Explicitly avoid**: meta-commentary, hedging, "I hope this helps",
restating the entire action-item list in prose, or padding. If in doubt, cut
a sentence rather than add one.

Write the result into `## SUMMARY`, replacing whatever placeholder text is
there.

**Revision rounds only** — three differences from the first-round summary
above:

1. **Opening phrase**: "Thank you for your revised replication package."
   (not "replication archive" — this is the current standard per direct
   editor guidance; the LDI Lab docs and the AEAREP-8434 example still say
   "archive," so if you're touching this again later and the two disagree,
   the live editor instruction wins).
2. The existing `## SUMMARY` (left over from round 1's approval) will look
   inconsistent with round 2's findings — expected, per Step 3, not a
   problem to flag. Replace it entirely; don't try to patch it — but "entirely"
   still excludes point 5 above: the fixed closing sentence is kept
   word-for-word regardless of round.
3. Add a `### Previously` section, placed after the `### Action Items`
   subsections and before the general body. Two sub-sections:
   - `#### Incomplete` — for each Step 3 item you judged incomplete: the
     original request converted to `> [We REQUESTED] <original text>` or
     `> [We SUGGESTED] <original text>`, followed by one sentence explaining
     why it's not done.
   - `#### Complete` — same conversion format, followed by one sentence
     starting with `Done: ` explaining why it's now satisfied.
   (The LDI Lab docs name these sub-sections `#### Unresolved` /
   `#### Resolved` instead, matching the older AEAREP-8434 example — use
   `Incomplete`/`Complete` per current editor instruction, but this is worth
   double-checking if the docs and instruction ever visibly diverge again.)
   Source the original request text from the Step 1c baseline, not from
   memory. Remember the Step 4 ordering note — this section only gets
   written after `aea-parse-tags` has already run.

## Step 6 — Report back to the user

Show:
- The drafted SUMMARY text.
- The consolidated Action Items checklist (post-`aea-parse-tags`).
- Anything from Step 3: what you auto-fixed vs. what you're flagging for a
  decision.
- If Step 1b found a different current ticket than the repo's own history,
  say so explicitly and use that ticket number in any reminder about the
  eventual sign-off commit message — don't default to the repo's original
  ticket number.
- On a revision round, the drafted `### Previously` section (Step 5) and
  your complete/incomplete calls (Step 3) — these are exactly the kind of
  judgment the human editor should skim before sign-off, even for the items
  you auto-fixed.

## Restrictions

**Pipeline context, so you never have to re-derive this by reading scripts.**
There are three separate tools that touch `REPLICATION.md`, at three
different stages, only one of which this skill ever runs:

1. `automations/24_amend_report.sh` (in the repo, part of the Bitbucket
   pipeline) — runs automatically, before the RA/editor ever opens the
   report. Fills scan-output placeholders (`{{ pii-summary.md }}`,
   `{{ file-paths-summary.md }}`, candidate-package tables, etc.) into
   `REPLICATION.md`/`generated/REPLICATION-filled.md` from files it
   generates under `generated/`. Not something this skill or the editor
   invokes directly.
2. `aea-parse-tags` (Python entry point from the `editor-scripts` repo,
   `pip install`-ed as `aea-editor-scripts`; formerly the bash script
   `aeareq`) — what **this skill runs** in Step 4, to consolidate
   `[REQUIRED]`/`[SUGGESTED]` tags into the Action Items checklist, route
   them to the manuscript vs. deposit checklist, and priority-order each
   one (see Step 4 for what it handles natively now).
3. `aeaready` (`~/bin/aea-scripts/aeaready`, personal script, not in the
   repo, **never run by this skill**) — the editor's actual final sign-off
   tool. Given an issue number and `approve`/`pre-approve`, it: strips and
   regenerates the `# Automatically Generated Appendices` block (by
   re-running `tools/replace_placeholders.py` against
   `template/REPLICATION_appendix.md` and files under `generated/`),
   queries Jira to inject the DOI, the openICPSR deposit URL (replacing the
   templated `.../openicpsr/xxxxx` placeholder under `### Action Items
   (manuscript)`), and any private-data notice, stamps a "Report last
   created on" timestamp, renders `REPLICATION.pdf`, then **commits with
   exactly the message this skill's Step 1 gate-check searches for**
   (`AEAREP-NNNN #comment Approved. Ready to submit.` or `... Preapproved.
   Ready for approval.`) and pushes, and finally offers to update the Jira
   issue via `jira-approval-manager`. This is the literal mechanics behind
   "sign-off is the editor's own action" below — it is a human running a
   script interactively (it prompts for confirmation before committing/
   pushing), not something to script around or replicate.

- **Never** create the approval commit
  (`AEAREP-NNNN #comment Approved. Ready to submit.`), tag, or push, and
  **never run `aeaready`** — that sign-off is the editor's own action (see
  above).
- **Never** fabricate a replication finding, package name, or file path not
  actually backed by evidence in the repo.
- **Never** invent canned language — pull it from `sample-language-report.md`
  in the current repo.
- **Never** post a comment to Jira from this skill (that's the pipeline's
  job — `automations/70_publish_comment.sh`). Only ever *read* from Jira
  (`jira_find_task_by_icpsr.py`, `jira_get_info.py`).
- **Never modify anything from the `# Automatically Generated Appendices`
  line to the end of `REPLICATION.md`** (cross-platform file paths, comments
  in code, candidate Stata/R/Python packages, possible PII, programs/data
  files provided, manifest comparison, not-for-publication data). `aeaready`
  strips and fully regenerates this block on every run (see above) — any
  edit you make here is silently discarded at sign-off, not preserved. Read
  it freely for the verification pass (Step 3) but never edit, reformat, or
  add to it. Anything that needs to change in response to a scan finding
  belongs in the document's narrative sections instead (e.g. a new
  `[REQUIRED]` tag under `### Missing computational requirements`), never in the Appendix
  itself. The same applies to a standalone `generated/REPLICATION_appendix.md`
  if one exists in the repo — it's the same auto-generated content, just not
  yet appended.
- **Never try to resolve the `.../openicpsr/xxxxx` placeholder URL** under
  `### Action Items (manuscript)`, or add/guess a DOI — `aeaready` fills
  both in from Jira at sign-off. Leave them as the template placeholder.
- If the repo is genuinely finalized (Step 1, no post-approval activity),
  stop and ask before touching it further. A revision round in progress
  (post-approval activity present) is not a reason to stop.
