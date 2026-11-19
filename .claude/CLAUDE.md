# Instructions for AEA replication review

This repository is an AEA Data Editor replication review (`aearep-NNNN`),
created from the replication template. You act in the replicator /
transparency-editor role: reviewing the author's deposit and filling out
`REPLICATION.md`. You are not developing the template's pipelines or tools.

## Template tooling: where it comes from and where to report problems

Everything outside the author's deposit -- `automations/`, `tools/`,
`bitbucket-pipelines.yml`, `template*`, `docs/`, `.claude/` (including this
file) -- is template tooling, not part of the review.

- Source of truth: <https://github.com/AEADataEditor/replication-template-development>
  (default branch `development`). Bugs, fixes, and feature requests for the
  tooling go there, as issues or pull requests.
- `AEADataEditor/replication-template` (`master`) is only the published copy
  that `tools/update_tools.sh` downloads. Issues are disabled there and PRs
  are not accepted, because it is overwritten on every deploy.
- Don't fix tooling bugs only in this `aearep-NNNN` repository: the next
  `tools/update_tools.sh` run overwrites them. If you need a local
  workaround, report the bug upstream too.

## Skills

- Running the author's package, verifying numbers against the manuscript, and
  filling Findings / Replication steps / Classification: use the
  `aea-replication-run` skill.
- Consolidating tags, checking the findings, and drafting the SUMMARY before
  approval: use the `aea-report-finalize` skill.
- Running the `aea-report-finalize` pass on several `aearep-NNNN` repos at
  once, from their parent directory: the `aea-multi-agent-report-review` skill.
  It is installed at user level by editor-scripts' `install.sh`, because skills
  inside a review repo are not loaded from the parent directory.

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

## Transparency Editor Tasks

When filling out REPLICATION-PartA.md, cross-referencing README against manuscripts,
or validating replication package compliance, read and follow the full specification
in `.github/agents/transparency-editor.agent.md` before proceeding.

## Code Review of the Deposit

When asked to "run code review" or "review code" on the author's code, use these prompts:

### Standard Code Review
```
You are a code reviewer. Find any bugs in the code in this repository in the [TARGET_DIRECTORY] directory.
```

### Comprehensive Python Review
```
Search through all Python files and look for:
1. Import errors or missing modules
2. Variable naming inconsistencies
3. File path issues (hardcoded paths, missing directories)
4. Data type mismatches or conversion errors
5. Index/column name mismatches in pandas operations
6. Division by zero or NaN handling issues
7. Logic errors in conditionals
8. Missing error handling
9. Inefficient or problematic code patterns
```
