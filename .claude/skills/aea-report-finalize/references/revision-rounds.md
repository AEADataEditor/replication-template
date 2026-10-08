# Revision rounds — extra steps

Read when Step 1 found post-approval activity. Replicator-facing guidance:
[LDI 12](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/12-jira-revision-guidance.md);
approver-facing: [LDI 13-2](https://github.com/labordynamicsinstitute/ldilab-manual/blob/main/13-2-approving-issues-revision.md).

## Step 1b — Confirm the current ticket via Jira

AEA opens a **new Jira ticket per revision round**, but the work continues in
the same repo, whose history (`config.yml` `jiraticket:`, every commit
message) references the *original* ticket forever. Find the live one:

```bash
[ -n "$JIRA_USERNAME" ] && [ -n "$JIRA_API_KEY" ] && echo "jira env OK"
```

If unset, `source ~/.envvars` and recheck. Still unset → tell the user Jira
confirmation isn't possible, fall back to git-only evidence, note the
limitation; don't block.

Find the current deposit ID (`config.yml` `openicpsr:`, the bare-digit
directory at repo root, or the latest `Adding code from <id>` commit), then:

```bash
python3 tools/jira_find_task_by_icpsr.py <deposit-id>   # try python3.12 if needed
```

Prints the highest-numbered Jira Task tracking that deposit (nothing on
missing credentials or no match). Compare with the repo's own ticket:

- **Same** → proceed normally.
- **Different, higher** → that is the live ticket. Use it everywhere you refer
  to the current case, including Step 6 and any reminder about the eventual
  sign-off commit message.

## Step 1c — Baseline the round-1 requests

```bash
git show ${LAST_APPROVAL_SHA}:REPLICATION.md
```

Extract `### Action Items (manuscript)` and `### Action Items (openICPSR)` as
the round-1 baseline — the authoritative record of what was asked, not what
you infer from the current draft. Needed in Steps 3 and 5.

## Step 2 note

A missing `-----action items go here------` marker is expected (round 1
consumed it). Don't flag it; Step 4 restores it.

## Step 3 addition — assess the baseline

For each round-1 `[REQUIRED]`/`[SUGGESTED]` item, decide complete or
incomplete from the evidence you're already gathering (scan output, deposit
files, logs, current `## Findings`). Round 1's `## SUMMARY` will look
inconsistent with this round's findings — nobody touches it between rounds;
that mismatch is not itself a finding.

For every item judged **incomplete**, make sure a fresh `[REQUIRED]`/
`[SUGGESTED]` tag for it exists in the current draft; add one yourself if the
RA didn't, starting from the round-1 text. This is the mechanical rule from
LDI 12 ("items the authors did not adequately address [are reiterated] as new
`[REQUIRED]` tags"), not a judgment call. Keep a one-line reasoning per item
for Step 5.

## Step 4 note

Run `aea-parse-tags` before writing `### Previously`.

## Step 5 differences

1. **Opening**: "Thank you for your revised replication package." (current
   editor instruction; older LDI docs and examples say "archive" — the live
   instruction wins).
2. **Replace the old `## SUMMARY` entirely** — don't patch it — but keep the
   fixed closing sentence word for word (SKILL.md Step 5, item 5).
3. **Add `### Previously`** after the `### Action Items` subsections, before
   the general body, with two sub-sections:
   - `#### Incomplete` — each incomplete item as `> [We REQUESTED] <original
     text>` or `> [We SUGGESTED] <original text>`, then one sentence on why
     it's not done.
   - `#### Complete` — same conversion, then one sentence starting `Done: `.

   Source the original text from the Step 1c baseline, not memory. (LDI docs
   call these `#### Unresolved`/`#### Resolved`; use `Incomplete`/`Complete`
   per current editor instruction.)
