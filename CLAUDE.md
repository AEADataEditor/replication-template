# Repository Memory for AI Code Reviews

## Quick Review Commands

When asked to "run code review" or "review code", use these prompts:

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

### Report Generation
Always end reviews with:
```
write the error report to a file AI-Review.md
```

Then add statistics:
```
Add to the report the total numbers of tokens used for the review, and the approximate cost of this session.
```

## Transparency Editor Tasks
When filling out REPLICATION-PartA.md, cross-referencing README against manuscripts,
or validating replication package compliance, read and follow the full specification
in `.github/agents/transparency-editor.agent.md` before proceeding.

## Repository Context
- This is a research/academic repository
- Contains Python data analysis code
- Uses MATLAB for modeling
- Focus on data science and financial analysis code patterns

## Coding Conventions

- Keep `bitbucket-pipelines.yml` steps short: call into `automations/*.sh` rather than writing multi-line inline logic in the YAML.
- When an automation needs real logic beyond argument/ticket resolution and shell plumbing (API calls, parsing, data transforms), pair a thin `automations/NN_name.sh` (resolves arguments/the Jira ticket, calls the tool) with a `tools/name.py` that does the actual work. Examples: `70_publish_comment.sh`->`jira_add_comment.py`, `30_download_commit_jira_attachments.sh`->`jira_download_attachments.py`, `26_update_jira_software.sh`->`jira_update_software.py`. Don't add a wrapper script whose only job is to call another script that already does the work - extend that script instead.
- Never write or run inline Python (`python3 -c "..."`) in the pipeline YAML or in shell scripts, under any circumstances. Always put it in a proper file under `tools/`. (Note: `bitbucket-pipelines.yml` currently has several pre-existing `python3 -c "..."` snippets for Zenodo-ID URL parsing that violate this rule - out of scope for prior changes, flagged for a future cleanup pass.)
