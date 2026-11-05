#!/bin/bash
# 33_trigger_parse_manuscript.sh
# Start the m-parse-manuscript pipeline for the current Jira ticket, so that the
# manuscript is converted to Markdown while the ingest runs. The pipeline is only
# started if the manuscript differs from the checksum recorded by the last
# conversion (generated/manuscript.sha256). If the check itself breaks, the
# pipeline is started. It never fails: the ingest does not depend on the result,
# and a failed trigger is only reported.
#
# Usage: 33_trigger_parse_manuscript.sh
#
# Environment:
#   jiraticket - Jira ticket (set by `. ./tools/resolve_jiraticket.sh`)
#   JIRA_USERNAME, JIRA_API_KEY - for the attachment download
#   BITBUCKET_*, JIRA_USERNAME, P_BITBUCKET_PAT - see tools/bitbucket_trigger_pipeline.py

if [ -n "${jiraticket:-}" ]; then
    workdir=$(mktemp -d)
    trap 'rm -rf "$workdir"' EXIT
    # The download tool exits 1 when it fetched nothing (as 31_parse_manuscript.sh notes)
    python3 tools/jira_download_attachments.py "$jiraticket" --output-dir "$workdir" --filter .pdf \
        || echo "33_trigger_parse_manuscript: Warning - no PDF attachments downloaded for $jiraticket"
    python3 tools/manuscript_to_markdown.py --source-dir "$workdir" --needs-conversion
    if [ $? -eq 3 ]; then
        echo "33_trigger_parse_manuscript: m-parse-manuscript not needed, not started"
        exit 0
    fi
fi

python3 tools/bitbucket_trigger_pipeline.py m-parse-manuscript --var "jiraticket=${jiraticket:-}" \
    || echo "33_trigger_parse_manuscript: Warning - m-parse-manuscript was not started"
exit 0
