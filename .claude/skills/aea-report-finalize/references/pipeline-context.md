# Pipeline context

Three tools touch `REPLICATION.md`; this skill runs only the second.

1. **`automations/24_amend_report.sh`** — Bitbucket pipeline, automatic,
   before anyone opens the report. Fills scan-output placeholders
   (`{{ pii-summary.md }}`, `{{ file-paths-summary.md }}`, candidate-package
   tables) into `REPLICATION.md` / `generated/REPLICATION-filled.md` from
   files under `generated/`.
2. **`aea-parse-tags`** — Python entry point from `editor-scripts`
   (`pip install aea-editor-scripts`), successor to the bash `aeareq`.
   Consolidates, routes, and priority-orders tags (SKILL.md Step 4).
3. **`aeaready`** (`~/bin/aea-scripts/aeaready`, personal, not in repo,
   **never run by this skill**) — the editor's interactive sign-off. Given an
   issue number and `approve`/`pre-approve` it: strips and regenerates the
   `# Automatically Generated Appendices` block (re-running
   `tools/replace_placeholders.py` against `template/REPLICATION_appendix.md`
   and `generated/`); injects the DOI, the openICPSR deposit URL (replacing
   `.../openicpsr/xxxxx`), and any private-data notice from Jira; stamps
   "Report last created on"; renders `REPLICATION.pdf`; commits with the
   message Step 1 greps for (`AEAREP-NNNN #comment Approved. Ready to
   submit.` / `... Preapproved. Ready for approval.`); pushes; offers to
   update Jira via `jira-approval-manager`. It prompts before committing —
   a human runs it.

Jira comments are posted by `automations/70_publish_comment.sh`, not by this
skill.

## `Reason for incomplete reproducibility` ↔ Jira `Reason for Failure to be Fully Reproduced`

Options share wording except:

| REPLICATION.md | Jira |
| --- | --- |
| `Insufficient computing resources available to replicator` | `Insufficient computing resources available` |
| `None.` | *(field empty)* |
| *(none)* | `Reproduced in a previous round` — administrative, revision history |
| *(none)* | `ZIP file only - returned` — deposit-format fact |

Match on substance; wording drifts independently (an older repo's frozen
`template/original-REPLICATION.md` may still bundle compute resources into
the "Insufficient time..." line). Never flag the two Jira-only options as
missing from `REPLICATION.md`.
