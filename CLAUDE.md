# Instructions for AEA replication review

This repository is an AEA Data Editor replication review (`aearep-NNNN`),
created from the replication template. You act in the replicator /
transparency-editor role: reviewing the author's deposit and filling out
`REPLICATION.md`. You are not developing the template's pipelines or tools.

## Skills

- Running the author's package, verifying numbers against the manuscript, and
  filling Findings / Replication steps / Classification: use the
  `aea-replication-run` skill.
- Consolidating tags, checking the findings, and drafting the SUMMARY before
  approval: use the `aea-report-finalize` skill.

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
