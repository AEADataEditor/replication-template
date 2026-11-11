#!/bin/bash
# 31_parse_manuscript.sh
# Convert the manuscript PDF(s) attached to the Jira ticket to Markdown, with
# the figures extracted as images, and commit the result as manuscript_parsed/.
#
# The PDFs are downloaded into a scratch directory and are not committed here;
# 30_download_commit_jira_attachments.sh commits them. The conversion itself is
# tools/manuscript_to_markdown.py. The push goes through 32_pull_push.sh, since
# the ingest may be pushing to the same branch.
#
# Usage: 31_parse_manuscript.sh
#
# Environment:
#   jiraticket      - Jira ticket (set by `. ./tools/resolve_jiraticket.sh`)
#   JIRA_USERNAME, JIRA_API_KEY - for the attachment download

if [ -z "${jiraticket:-}" ]; then
    echo "31_parse_manuscript: no Jira ticket; source tools/resolve_jiraticket.sh first" >&2
    exit 1
fi

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

# The download tool exits 1 when it fetched nothing (as 30_download_commit_jira_attachments.sh notes)
python3 tools/jira_download_attachments.py "$jiraticket" --output-dir "$workdir" --filter .pdf \
    || echo "31_parse_manuscript: Warning - no PDF attachments downloaded for $jiraticket"
# A changed manuscript must not inherit files from the earlier one, such as the
# figures of a manuscript since renamed. Nothing is pushed if the conversion fails.
if python3 tools/manuscript_to_markdown.py --source-dir "$workdir" --needs-conversion; then
    rm -rf manuscript_parsed
fi
python3 tools/manuscript_to_markdown.py --source-dir "$workdir" --output-dir manuscript_parsed || exit 1

if [ ! -d manuscript_parsed ]; then
    echo "31_parse_manuscript: no manuscript found for $jiraticket, nothing to commit"
    exit 0
fi

./automations/20_commit_code.sh manuscript_parsed notag
# Only after a successful conversion, so that a failed one is retried by the next ingest
python3 tools/manuscript_to_markdown.py --source-dir "$workdir" --record-checksums
[ -f generated/manuscript.sha256 ] && ./automations/20_commit_code.sh generated/manuscript.sha256 notag
# 20_commit_code.sh leaves generated/git-commit.log behind. The ingest pushes the
# same file, and a dirty tree blocks the rebase, so drop this pipeline's copy.
git checkout -- generated 2>/dev/null
git clean -fdq generated
./automations/32_pull_push.sh rebase
