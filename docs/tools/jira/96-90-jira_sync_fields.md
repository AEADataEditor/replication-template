(help-jira_sync_fields)=

# jira_sync_fields.py - Sync fields from a source Jira issue to a target issue

## Description

Copies fields from a source Jira issue to a target issue, but only for fields that are empty or null on the target. This is useful when a revision case is created and many metadata fields (e.g., DOI, openICPSR URL, manuscript ID) need to be carried over from the original issue without overwriting any values already entered on the revision.

## Usage

```bash
python3 tools/jira_sync_fields.py <issue-key> [<target-key>] [--yes] [--comment]
```

### Arguments

- **issue-key** (required) - Jira issue key or bare number (e.g., `AEAREP-9603` or `9603`).
  - If `<target-key>` is also provided, this is the **source** issue to copy fields from.
  - If `<target-key>` is omitted, this is treated as the **revision (target)** issue and the original is auto-detected via an `"is a revision of"` link.
- **target-key** (optional) - Explicit target issue key to copy fields into. If omitted, the target is auto-detected.

### Options

- `-y`, `--yes` - Apply changes without prompting for confirmation
- `-c`, `--comment` - Post a comment to the target issue listing all synced fields

### Issue Key Formats

Bare numbers (e.g., `9603`) are automatically expanded to `AEAREP-9603`. Keys with any non-numeric prefix (e.g., `TRAIN-2000`) are used as-is (uppercased).

## Examples

```bash
# Explicit source and target
python3 tools/jira_sync_fields.py AEAREP-9000 AEAREP-9603

# Using bare numbers
python3 tools/jira_sync_fields.py 9000 9603

# Auto-detect source from revision link on the target issue
python3 tools/jira_sync_fields.py AEAREP-9603

# Auto-apply without confirmation prompt
python3 tools/jira_sync_fields.py 9603 --yes

# Post a comment listing all synced fields
python3 tools/jira_sync_fields.py 9000 9603 --comment
```

## Requirements

- Python >= 3.6
- `jira`: Python Jira library

### Environment Variables Required

- `JIRA_USERNAME` - Your Jira email address
- `JIRA_API_KEY` - API token from https://id.atlassian.com/manage-profile/security/api-tokens

To obtain a Jira API token:
1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token and set it as `JIRA_API_KEY` environment variable

## Behavior

- Only fields that are **empty on the target** and **populated on the source** are transferred.
- System-managed fields (status, reporter, created, attachments, etc.) are always skipped.
- Certain fields that are legitimately blank on a new/revision issue (e.g., `MCRecommendationV2`) are also skipped.
- In interactive mode (without `--yes`), a preview of changes is shown and confirmation is required before any update is applied.
- With `--comment`, a comment is posted to the target issue listing every field that was synced.

## Output

- **Preview**: Lists all fields to be transferred with their values before applying.
- **Summary**: After applying, lists the field names that were successfully synced.
- **Nothing to transfer**: Reports when all target fields are already populated.
- **Exit code 0** on success; **exit code 1** on usage or authentication error.

## Use in Bitbucket Pipelines

This tool is invoked by the `s-sync-issue-fields` custom pipeline, which runs automatically when a revision ticket is associated with an original issue via the `"is a revision of"` Jira link. The pipeline passes the `--yes` and `--comment` flags so that changes are applied non-interactively and a comment is posted to the target issue.

See [Bitbucket Pipelines Configuration](bitbucket-pipelines-configuration) for details on the `s-sync-issue-fields` pipeline.

## See Also

- [jira_get_info.py](help-jira_get_info) - Retrieve individual fields from a Jira issue
- [jira_add_comment.py](help-jira_add_comment) - Post comments to Jira issues
- [jira_find_task_by_icpsr.py](help-jira_find_task_by_icpsr) - Find Jira tasks by openICPSR ID
