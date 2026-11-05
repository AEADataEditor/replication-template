# Revision rounds — extra steps

Read when Step 1 found post-approval activity. Replicator-facing:
[LDI 12](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/12-jira-revision-guidance.md);
approver-facing: [LDI 13-2](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-2-approving-issues-revision.md).

## Step 1b — Confirm the current ticket via Jira

Each revision round gets a **new Jira ticket** but the same repo, whose
history (`config.yml` `jiraticket:`, commit messages) keeps the *original*
ticket. Find the live one:

```bash
[ -n "$JIRA_USERNAME" ] && [ -n "$JIRA_API_KEY" ] && echo "jira env OK"
```

Unset → `source ~/.envvars`, recheck. Still unset → tell the user, fall back
to git-only evidence, note the limitation; don't block.

Deposit ID: `config.yml` `openicpsr:`, the bare-digit root directory, or the
latest `Adding code from <id>` commit.

```bash
python3 tools/jira_find_task_by_icpsr.py <deposit-id>   # python3.12 if needed
```

Prints the highest-numbered Task for that deposit (nothing on missing
credentials/no match). Compare with the repo's ticket:

- Same → proceed.
- Different, higher → live ticket; use it everywhere (Step 6, sign-off
  reminders).

## Step 1c — Baseline the prior-round requests

```bash
git show ${LAST_APPROVAL_SHA}:REPLICATION.md
```

Extract `### Action Items (manuscript)` and `### Action Items (openICPSR)` as
the baseline — the authoritative record of what was asked. Needed in Steps 3
and 5.

## Step 3 addition — assess the baseline

- For each baseline `[REQUIRED]`/`[SUGGESTED]` item, judge complete or
  incomplete from evidence already gathered (scan output, deposit files, logs,
  `## Findings`).
- The prior `## SUMMARY` will look inconsistent with this round's findings
  (untouched between rounds); not itself a finding.
- Each **incomplete** item must have a fresh `[REQUIRED]`/`[SUGGESTED]` tag in
  the current draft; add one from the baseline text if the RA didn't (LDI 12
  rule, not judgment). Keep a one-line reason per item for Step 5.

## Step 5 differences

1. **Opening**: "Thank you for your revised replication package."
2. **Replace the old `## SUMMARY` entirely**; keep the fixed closing sentence
   verbatim (SKILL.md Step 5.5).
3. **Add `### Previously`** after the `### Action Items` subsections, before
   the general body:
   - `#### Incomplete` — each item as `> [We REQUESTED] <original text>` or
     `> [We SUGGESTED] <original text>`, then one sentence on why it's not
     done.
   - `#### Complete` — same conversion, then one sentence starting `Done: `.

   Source original text from the Step 1c baseline, not memory.

Notes: missing `-----action items go here------` marker is expected (prior
round consumed it); Step 4 restores it. Run `aea-parse-tags` before writing
`### Previously`.
