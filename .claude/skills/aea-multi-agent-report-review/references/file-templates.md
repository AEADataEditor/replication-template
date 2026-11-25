# File templates

Contents: 1. Usage log · 2. AGENTS-FOLLOWUP.md · 3. Permanent CLAUDE.md
section (upstream) · 4. Final summary to the user

## 1. Usage log — `<SCRATCHPAD>/usage-log.md`

Create in Phase 0, before dispatch. Add a row the moment each completion
notification arrives (the numbers exist only in that notification).

```markdown
# Usage log: aea-report-finalize multi-agent run

- Started: <ISO timestamp from `date -Iseconds`>
- Orchestrator: <model> (main session). Workers: <model>, one per repo, launched in parallel.
- Account usage before: <pasted `/usage` output, or "not captured (reason)">
- Account usage after: <pasted `/usage` output, or "not captured (reason)">
- Per-agent figures are from each completion notification (`subagent_tokens`,
  `tool_uses`, `duration_ms`). They exclude the orchestrator's own tokens.
- Duration is wall-clock from dispatch to completion and includes time waiting
  on permission prompts; tool-use counts indicate actual work.

## Not dispatched
| Repo | Readiness status | Reason |
|---|---|---|

## Workers
| Repo | Model | Outcome | Decisions open | Tokens | Tool uses | Duration (ms) | Sub-agents |
|---|---|---|---|---|---|---|---|
| **Total** | | | **<sum>** | **<sum>** | **<sum>** | | |

## Follow-up tasks
| Task | Model | Tokens | Tool uses | Duration (ms) |
|---|---|---|---|---|
```

Outcome examples: "Finished: 4 deposit + 2 manuscript items; conditional
accept (depends on D1–D4)", "Stopped at Step 1: already finalized".
Sub-agents: "none", or each nested agent with its own reported usage.

## 2. `<REPO>/AGENTS-FOLLOWUP.md` (local, excluded via `.git/info/exclude`)

Written in Phase 2 as soon as the worker's notification arrives, and updated
after **every** answered item (Phase 3 here, or the per-repo session). Three
states: Decided (to apply) · Open · Closed.

```markdown
# Agent follow-up: <REPO>

Context: an unattended `aea-report-finalize` pass ran on <date> (<model> worker).
It edited REPLICATION.md in the working tree only (see `git diff REPLICATION.md`)
and drafted the SUMMARY with **"<decision sentence>"**. <Which decisions it
depends on.> Nothing was committed or written to Jira.

How to use this file:
- **Decided, to apply** (`- [ ]` with a **Decision** line): the editor already
  answered. Apply without asking again, then tick (`- [x]`) immediately.
- **Open** (`- [ ]`, no Decision): ask the editor with AskUserQuestion
  (recommended option first), record the answer here as a **Decision** line
  right away, apply it, tick it.
- **Closed** (`- [x]`): nothing to do.
- Update this file after each item, not at the end. After any tag change:
  rerun `aea-parse-tags` (restore `-----action items go here------` at the end
  of `### Action Items (openICPSR)` first, or ask about `force`), redo the
  singular→plural rewrite, strip `{{ }}`, rerun Step 5b, and revise the
  SUMMARY / decision sentence if the classification changed.

Status (<date>): <n> items — <c> closed, <d> decided (to apply), <o> open.

## Decided, to apply
- [ ] **D1 – <title>.** <Evidence.>
  **Decision (<date>):** <what to do, with verbatim tag text where relevant>.
  <Jira field to update by hand afterwards, if any.>

## Open
- [ ] **D2 – <title>.** <Evidence in one or two sentences.>
  Options: <recommended> (recommended) · <alternative> · <alternative>.
  <"Deferred by the editor on <date>" if it was asked and deferred.>

## Closed
- [x] **D3 – <title>.** Decision: <answer>. <Rule given by the editor, if any.>

## Mechanical edits already made (for review)
- <one line each, from the worker's "fixed automatically" list>

## Worker report (verbatim)
<details><summary><model> worker, <tokens> tokens, <tool uses> tool uses</summary>

<the worker's final message, unchanged>
</details>
```

## 3. Permanent section in the deployed `.claude/CLAUDE.md` (upstream, not per run)

This skill never edits a review repo's `CLAUDE.md`; it is committed with the
review. The section below ships in the template's `.claude/CLAUDE.md`
(source: `build/CLAUDE-deployed.md` in `replication-template-development`), so
every repo carries it after `tools/update_tools.sh`. If it is missing, tell the
user rather than adding it.

```markdown
## Agent follow-up file

At the start of every session, if `AGENTS-FOLLOWUP.md` exists in the repository
root (a local, uncommitted file left by an unattended review agent), read it
first and follow the instructions at its top. Tell the user how many items are
decided, open and closed. Apply decided items without asking again; ask about
open items one at a time with `AskUserQuestion` (clickable options,
recommended option first, evidence in the question). Update
`AGENTS-FOLLOWUP.md` immediately after each item (record the decision, tick it
once applied), never in a batch at the end. Apply changes following the skill
the file names (e.g. `aea-report-finalize`). Never commit, approve, or write to
Jira on the basis of this file; list any Jira fields that need a manual update.
```

## 4. Final summary to the user (chat)

```markdown
**Batch finalize: <n> dispatched, <m> held back.** Nothing committed, approved, or written to Jira.

| Repo | Outcome | Decision sentence | Open decisions | Tokens | Tool uses | Wall clock |
|---|---|---|---|---|---|---|

**Held back:** <repo — status — what the RA/editor must do>.

**Cross-repo issues** (seen in ≥2 repos, likely template/pipeline fixes):
1. <issue> — <repos> — <suggested upstream fix>

**Next:** open a session in each repo (`cd <repo> && claude`); it reads
`AGENTS-FOLLOWUP.md` and walks through what is still open. The file is local
(excluded from git); delete it once everything is ticked.

**Files:** usage log `<abs path>`; `AGENTS-FOLLOWUP.md` in <repos>; edits in each `REPLICATION.md` (`git diff`).
Usage excludes this orchestrating session; account-level: <before/after or "not captured">.
```
