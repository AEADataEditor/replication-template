# Pipeline context

Three tools touch `REPLICATION.md`; this skill runs only #2.

1. **`automations/24_amend_report.sh`** — Bitbucket pipeline, automatic, before
   anyone opens the report. Fills scan placeholders (`{{ pii-summary.md }}`,
   `{{ file-paths-summary.md }}`, candidate-package tables) into
   `REPLICATION.md` / `generated/REPLICATION-filled.md` from `generated/`.
2. **`aea-parse-tags`** — `editor-scripts` (`pip install aea-editor-scripts`).
   Consolidates, routes, priority-orders tags (SKILL.md Step 4).
3. **`aeaready`** (`~/bin/aea-scripts/aeaready`, personal, not in repo,
   **never run by this skill**) — editor's interactive sign-off, given an
   issue number and `approve`/`pre-approve`:
   - strips/regenerates `# Automatically Generated Appendices`
     (`tools/replace_placeholders.py`, `template/REPLICATION_appendix.md`,
     `generated/`);
   - injects DOI, openICPSR URL (replacing `.../openicpsr/xxxxx`), private-data
     notice from Jira; stamps "Report last created on"; renders
     `REPLICATION.pdf`;
   - commits with the message Step 1 greps for (`AEAREP-NNNN #comment
     Approved. Ready to submit.` / `... Preapproved. Ready for approval.`),
     pushes, offers Jira update via `jira-approval-manager`;
   - prompts before committing; a human runs it.

Jira comments: `automations/70_publish_comment.sh`, not this skill.

## `Reason for incomplete reproducibility` ↔ Jira `Reason for Failure to be Fully Reproduced`

Wording is shared except:

| REPLICATION.md | Jira |
| --- | --- |
| `Insufficient computing resources available to replicator` | `Insufficient computing resources available` |
| `None.` | *(field empty)* |
| *(none)* | `Reproduced in a previous round` (administrative) |
| *(none)* | `ZIP file only - returned` (deposit-format fact) |

Match on substance; wording drifts (a frozen `template/original-REPLICATION.md`
may fold compute resources into "Insufficient time..."). Never flag the two
Jira-only options as missing from `REPLICATION.md`.
