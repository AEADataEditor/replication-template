#!/bin/bash
# Generate a template-consistent SIVACOR Part B Markdown file from a TRO JSON-LD file.

set -euo pipefail

jsonld=""
output_dir="generated"
template="REPLICATION-PartB.md"
output="REPLICATION-PartB-SIVACOR.md"
steps_output=""
findings_output=""
environment_output=""
appendix_output=""
report_appendix=""

usage() {
  echo "Usage: $0 [-j tro.jsonld] [-t template.md] [-o output.md] [-d output_dir] [--dry-run]"
  echo ""
  echo "If -j is omitted, the first */tro/tro-*.jsonld file is used."
  echo "Outputs:"
  echo "  generated/partb-SIVACOR-computing-environment.md"
  echo "  generated/partb-SIVACOR-replication-steps.md"
  echo "  generated/partb-SIVACOR-findings.md"
  echo "  generated/partb-SIVACOR-appendix.md"
  echo "  generated/REPLICATION_appendix.md"
  echo "  REPLICATION-PartB-SIVACOR.md"
}

dry_run=""

while [[ $# -gt 0 ]]
do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -j|--jsonld)
      jsonld="$2"
      shift 2
      ;;
    -d|--output-dir)
      output_dir="$2"
      shift 2
      ;;
    -t|--template)
      template="$2"
      shift 2
      ;;
    -o|--output)
      output="$2"
      shift 2
      ;;
    --dry-run)
      dry_run="--dry-run"
      shift
      ;;
    *)
      echo "ERROR: Unknown option $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$jsonld" ]]
then
  jsonld=$(find . -path "*/tro/tro-*.jsonld" -not -path "./.git/*" | sort | head -1)
fi

if [[ -z "$jsonld" || ! -f "$jsonld" ]]
then
  echo "ERROR: Could not find a SIVACOR TRO JSONLD file."
  exit 1
fi

if [[ ! -f "$template" ]]
then
  echo "ERROR: Template file '$template' not found."
  exit 1
fi

steps_output="$output_dir/partb-SIVACOR-replication-steps.md"
findings_output="$output_dir/partb-SIVACOR-findings.md"
environment_output="$output_dir/partb-SIVACOR-computing-environment.md"
appendix_output="$output_dir/partb-SIVACOR-appendix.md"
report_appendix="$output_dir/REPLICATION_appendix.md"

if [[ "$dry_run" != "--dry-run" ]]
then
  mkdir -p "$output_dir"
fi

python3 tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-computing-environment --output "$environment_output" $dry_run
python3 tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-replication-steps --output "$steps_output" $dry_run
python3 tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-findings --output "$findings_output" $dry_run
python3 tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-appendix --output "$appendix_output" $dry_run

if [[ "$dry_run" == "--dry-run" ]]
then
  if [[ -f "$environment_output" && -f "$steps_output" && -f "$findings_output" && -f "$appendix_output" ]]
  then
    python3 tools/insert_sivacor_partb_sections.py --template "$template" --computing-environment "$environment_output" --replication-steps "$steps_output" --findings "$findings_output" --output "$output" --dry-run
    python3 tools/update_sivacor_appendix.py --appendix "$report_appendix" --sivacor-appendix "$appendix_output" --dry-run
  else
    echo "DRY RUN: Would combine generated snippets with '$template' into '$output'."
    echo "DRY RUN: Would add '$appendix_output' to '$report_appendix'."
  fi
else
  python3 tools/insert_sivacor_partb_sections.py --template "$template" --computing-environment "$environment_output" --replication-steps "$steps_output" --findings "$findings_output" --output "$output"
  python3 tools/update_sivacor_appendix.py --appendix "$report_appendix" --sivacor-appendix "$appendix_output"
fi
