---
name: aea-multi-agent-report-review
description: Orchestrates the AEA Data Editor finishing pass (aea-report-finalize) across several aearep-NNNN repos at once from their parent directory — readiness-gates each repo, dispatches one unattended background worker per ready repo, logs per-agent token usage, saves each worker's report, writes the decisions it could not make to a local AGENTS-FOLLOWUP.md per repo (updated after every answer) so the editor can resolve them interactively, there or in a per-repo session. Use this whenever the session is in a directory holding multiple aearep-* repos and the user wants to finalize, review, or "run the editor pass" on more than one of them — e.g. "run aea-report-finalize on all these folders", "finalize these reports in parallel", "batch editor pass", "do the finishing pass on every aearep repo here", "review all pending replication reports", even if they don't say "parallel" or "agents". For a single repo, use aea-report-finalize directly instead.
---

# AEA batch finishing pass (orchestrator)

You are the orchestrator in a session rooted at a **parent directory** that
holds several `aearep-NNNN` git repos. Workers run `aea-report-finalize` on one
repo each, unattended; you gate, dispatch, collect, and set up the
interactive follow-up. Workers return decisions instead of asking; the editor
answers them later, one repo at a time.

The per-repo skill's Restrictions apply to you and to every worker unchanged:
no commits, tags, pushes, approvals, `aeaready`, or Jira writes; no edits to
the generated appendices; no invented language or findings. The one
orchestrator action that commits (`50_merge-parts.sh`) needs the user's
explicit go-ahead per repo.

Set `SCRATCH` = the scratchpad directory from your system prompt. All run
artifacts go there unless the user names another place.

## Phase 0 — Preflight (cheap, in the orchestrator)

1. **Find repos and gate them.** Run the bundled read-only check
   (`<this-skill-dir>` = the base directory shown when this skill loaded):
   ```bash
   bash <this-skill-dir>/scripts/readiness.sh . | column -t -s$'\t'
   command -v aea-parse-tags
   ```
   Dispatch only `READY` and `READY-LEFTOVERS`. For the rest, don't spend a
   worker (an unfilled repo cost 66k tokens just to stop at Step 2):
   - `NEEDS-RA` → report "needs RA work (Part A / Findings)".
   - `NEEDS-MERGE` → offer to run `automations/50_merge-parts.sh` in that
     repo. It does `git rm` + `git commit`, so ask first; on yes, run it,
     rerun the gate, and dispatch if it now reads READY.
   - `FINALIZED`, `PENDING-FOLLOWUP`, `NO-REPORT` → report and skip; the
     user may override `PENDING-FOLLOWUP` explicitly.
   - `dirty=yes` → uncommitted RA edits will be mixed into the worker's
     `git diff`; mention it, don't block.
   - `aea-parse-tags` missing → stop; every worker would stop at Step 0.

   The script is a heuristic. If a status looks wrong, open the repo's
   `REPLICATION.md` head and `git log --oneline -5` before overriding it.

2. **Usage baseline.** You cannot read account usage yourself: the OAuth
   usage endpoint and the transcript store sit outside the project and those
   reads are blocked. Don't try to work around that. Ask the user to run
   `/usage` now and paste the result (and again at the end), or to explicitly
   authorize reading the transcript store. Record whatever you get, or "not
   captured", in the usage log (template: `references/file-templates.md` §1).
   Create the log now, with `date -Iseconds` as start time.

3. **Permissions.** Unattended workers stall on permission prompts (a
   previous run took ~14.7 h wall clock for 7–30 tool calls). Before
   dispatch, suggest the user either run in auto mode or pre-allow what the
   finalize skill uses: `aea-parse-tags`, read-only git (`log`, `show`,
   `diff`, `status`, `tag -l`, `rev-parse`, `merge-base`), `grep`/`find`/
   `head`/`ls`/`cut`, `sed -i` on `REPLICATION.md`, `python3
   tools/jira_get_info.py`, `python3 tools/jira_find_task_by_icpsr.py`.
   Offer to add these via the `update-config` skill; don't edit settings
   without a yes.

4. **Worker model.** The model is the user's choice. If not given, ask once
   (AskUserQuestion: sonnet / opus / fable / haiku). Also ask whether workers
   may start nested sub-agents (default: no; earlier workers never used them).

5. **Snapshots.** For each repo to dispatch:
   `mkdir -p "$SCRATCH/<REPO>" && cp <REPO>/REPLICATION.md "$SCRATCH/<REPO>/REPLICATION.orig.md"`.
   Per-repo subdirectories prevent workers overwriting each other's files.

Show the user the gate table, the dispatch list, and the model, then proceed
(one confirmation is enough).

## Phase 1 — Dispatch

Fill `references/worker-prompt.md` once per ready repo (absolute repo path,
repo name, `SCRATCH`, sub-agent rule). Send **all** `Agent` calls in a single
message, each with `run_in_background: true`, `model: <chosen>`, and a
description like `finalize aearep-NNNN`. Then tell the user what is running
and that results arrive as notifications; don't poll.

## Phase 2 — Collect (on each completion notification)

Do all of this immediately, per notification, before anything else — the
usage numbers exist only there, and the editor may open the repo at any time:

1. Append a row to the usage log: repo, model, outcome (status line from the
   report), number of open decisions, `subagent_tokens`, `tool_uses`,
   `duration_ms` (label it wall clock), sub-agents reported. Note that the
   orchestrator's own tokens aren't included.
2. Check `git -C <REPO> diff --stat`: the worker's substantive output (tags,
   consolidated action items, SUMMARY) must already be in `<REPO>/REPLICATION.md`.
   That file is the deliverable, not a scratchpad report. If the worker
   described edits that aren't in the diff, apply them now (mechanical ones
   only) or list them as decisions.
3. Write `<REPO>/AGENTS-FOLLOWUP.md` from the report
   (`references/file-templates.md` §2) and make sure it is excluded locally:
   `grep -qx AGENTS-FOLLOWUP.md <REPO>/.git/info/exclude || echo AGENTS-FOLLOWUP.md >> <REPO>/.git/info/exclude`.
   Workers can't write files outside the repo themselves; that is by design.

If a worker failed or returned no report, log the row anyway and note it.
When all are in, fill the Total row.

**`CLAUDE.md` is never edited by this skill** (neither the root `CLAUDE.md`
nor `.claude/CLAUDE.md`); both are committed with the review. The template
deploys `.claude/CLAUDE.md` with a permanent "if `AGENTS-FOLLOWUP.md` exists,
read it first" section (§3 of the templates). If a repo's `.claude/CLAUDE.md`
lacks it, tell the user: running `tools/update_tools.sh` in that repo brings
it in. Don't add it by hand.

## Phase 3 — Asking the decisions (orchestrator, optional)

If the user wants to answer decisions in this session:

- One repo at a time, at most 4 questions per `AskUserQuestion` call. Each
  question stands alone: repo, item id, evidence, options with the
  recommended one first. Offer **Defer** on every judgment call: some need
  the repo open in its own session for context, and the user may say so.
- **After every answer batch, before asking the next one, update that repo's
  `AGENTS-FOLLOWUP.md`**: write each answer as a **Decision** line (or
  "Deferred by the editor on <date>"), move closed items to Closed, and
  refresh the Status line. Never hold answers in memory to write at the end:
  the user may open the repo in another session at any moment, and a stale
  file makes that session ask settled questions again.
- Recording a decision is not applying it. Unless the user asks you to apply
  it here, leave the item `- [ ]` with its Decision line; the per-repo session
  applies it and ticks it.
- Free-text answers often carry a rule ("only [REQUIRED] tags contradict
  that NOTE"). Record it in the item, and if it generalizes, propose adding
  it to this skill's worker checks.
- If the user interrupts, stop asking and flush what you already have to the
  files first.

## Phase 4 — Final summary to the user

Use `references/file-templates.md` §4: one table row per repo (outcome,
decision sentence, open decisions, tokens, tool uses, wall clock), held-back
repos and what they need, the top cross-repo issues (anything raised in two
or more reports; these usually point at a template or pipeline fix in
`replication-template-development`), and absolute paths to the usage log,
and follow-up files. Ask for the after-run `/usage` paste if you
have a baseline, and add it to the log.

Keep the summary short; the details live in the reports.
