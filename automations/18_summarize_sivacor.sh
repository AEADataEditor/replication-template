#!/bin/bash
# Generate a template-consistent SIVACOR Part B Markdown file and optionally
# copy it over REPLICATION-PartB.md. This automation does not rerun author code.

set -euo pipefail

jsonld=""
output_dir="generated"
output="REPLICATION-PartB-SIVACOR.md"
report="REPLICATION-PartB.md"
dry_run=""
replace_report=0

usage() {
  echo "Usage: $0 [-j tro.jsonld] [-d output_dir] [-o output.md] [-r report.md] [--replace-report] [--dry-run]"
  echo ""
  echo "If -j is omitted, the first */tro/tro-*.jsonld file is used."
  echo "By default this writes REPLICATION-PartB-SIVACOR.md and does not modify REPLICATION-PartB.md."
}

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
    -r|--report)
      report="$2"
      shift 2
      ;;
    -d|--output-dir)
      output_dir="$2"
      shift 2
      ;;
    -o|--output)
      output="$2"
      shift 2
      ;;
    --replace-report)
      replace_report=1
      shift
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

tools/generate_sivacor_partb.sh --jsonld "$jsonld" --output-dir "$output_dir" --template "$report" --output "$output" $dry_run

if [[ "$replace_report" -eq 1 ]]
then
  if [[ ! -f "$output" ]]
  then
    echo "ERROR: Generated SIVACOR Part B '$output' not found."
    exit 1
  fi
  if [[ "$dry_run" == "--dry-run" ]]
  then
    echo "DRY RUN: Would copy '$output' to '$report'."
  else
    cp "$output" "$report"
    echo "Copied '$output' to '$report'."
  fi
fi
