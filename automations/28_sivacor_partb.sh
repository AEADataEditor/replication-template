#!/bin/bash
# 28_sivacor_partb.sh
# If the repository contains a SIVACOR artifact (*/tro/tro-*.jsonld), generate
# the SIVACOR-based Part B via 18_summarize_sivacor.sh and, when
# REPLICATION-PartB.md has never been edited since the pipeline created it,
# replace it directly. Otherwise leave the generated file in generated/ and
# notify the Jira ticket that it is waiting there.
#
# Usage:
#   28_sivacor_partb.sh [pipeline-name]
#
#   pipeline-name  Optional. Name of the Bitbucket custom pipeline, passed
#                  through to 70_publish_comment.sh for the Jira comment.
#
# No-op when no SIVACOR artifact is present or SkipProcessing=yes.

[[ "${SkipProcessing:-}" == "yes" ]] && exit 0

_pipeline="${1:-}"

partb=REPLICATION-PartB.md
generated_partb=generated/REPLICATION-PartB-SIVACOR.md
generated_snippets=(
  generated/sivacor-partb-computing-environment.md
  generated/sivacor-partb-replication-steps.md
  generated/sivacor-partb-findings.md
  generated/sivacor-partb-appendix.md
)

if [ -n "${jiraticket:-}" ]
then
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi

jsonld=$(find . -path "*/tro/tro-*.jsonld" -not -path "./.git/*" | sort | head -1)
if [ -z "$jsonld" ]
then
  echo "28_sivacor_partb: no SIVACOR artifact (*/tro/tro-*.jsonld) found, nothing to do"
  exit 0
fi
echo "28_sivacor_partb: found SIVACOR artifact $jsonld"

# Decide whether Part B is still pristine: it must exist, be tracked, have no
# uncommitted changes, and be identical to the version in the commit that
# created it. A missing Part B (unsplit or revision report) counts as modified.
partb_modified=1
if [ -f "$partb" ] && git ls-files --error-unmatch "$partb" >/dev/null 2>&1
then
  first_commit=$(git log --diff-filter=A --format=%H -- "$partb" | tail -1)
  if [ -n "$first_commit" ] && git diff --quiet "$first_commit" -- "$partb"
  then
    partb_modified=0
  fi
fi

if ! ./automations/18_summarize_sivacor.sh -j "$jsonld"
then
  echo "28_sivacor_partb: generating the SIVACOR Part B failed"
  exit 1
fi

if [ "$partb_modified" -eq 0 ]
then
  echo "28_sivacor_partb: $partb has not been edited, replacing it with $generated_partb"
  cp "$generated_partb" "$partb"
  git add -v "$partb" "$generated_partb" "${generated_snippets[@]}"
  git commit -m "${premsg}Replaced Part B with SIVACOR-generated Part B" || true
  ./automations/70_publish_comment.sh "$_pipeline" "applied SIVACOR Part B" \
    "The SIVACOR-generated Part B was written to {{$partb}} (source: {{$jsonld}}). Please review and complete it." || true
else
  echo "28_sivacor_partb: $partb has been edited, leaving the SIVACOR Part B in $generated_partb"
  git add -v "$generated_partb" "${generated_snippets[@]}"
  git commit -m "${premsg}Added SIVACOR-generated Part B to generated/" || true
  ./automations/70_publish_comment.sh "$_pipeline" "generated SIVACOR Part B" \
    "{{$partb}} has already been edited, so it was not replaced. The SIVACOR-generated Part B is waiting in {{$generated_partb}} (source: {{$jsonld}}). To apply it, run {{./automations/18_summarize_sivacor.sh --replace-report}} and commit, or merge the relevant sections by hand." || true
fi

exit 0
