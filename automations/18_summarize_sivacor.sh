#!/bin/bash
# Generate a template-consistent SIVACOR Part B Markdown file and optionally
# copy it over REPLICATION-PartB.md. This automation does not rerun author code.

set -euo pipefail

PYTHON=${PYTHON:-}
if [[ -z "$PYTHON" ]]
then
  if command -v python3 >/dev/null 2>&1
  then
    PYTHON=python3
  elif command -v python >/dev/null 2>&1
  then
    PYTHON=python
  else
    echo "ERROR: Could not find python3 or python in PATH."
    exit 1
  fi
elif ! command -v "$PYTHON" >/dev/null 2>&1
then
  echo "ERROR: PYTHON is set to '$PYTHON', but that command was not found."
  exit 1
fi

jsonld=""
output_dir="generated"
output=""
report="REPLICATION-PartB.md"
template="REPLICATION.md"
dry_run=""
replace_report=0

usage() {
  echo "Usage: $0 [-j tro.jsonld] [-d output_dir] [-o output.md] [-r report.md] [-t template.md] [--replace-report] [--dry-run]"
  echo ""
  echo "If -j is omitted, the first */tro/tro-*.jsonld file is used."
  echo "By default this writes generated/REPLICATION-PartB-SIVACOR.md and does not modify REPLICATION-PartB.md."
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
    -t|--template)
      template="$2"
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

if [[ -z "$output" ]]
then
  output="$output_dir/REPLICATION-PartB-SIVACOR.md"
fi

if [[ ! -f "$template" ]]
then
  echo "ERROR: Template file '$template' not found."
  exit 1
fi

PYTHON="$PYTHON" tools/generate_sivacor_partb.sh --jsonld "$jsonld" --output-dir "$output_dir" --template "$template" --output "$output" $dry_run

if [[ "$replace_report" -eq 1 ]]
then
  if [[ "$dry_run" == "--dry-run" ]]
  then
    if [[ -f "$report" ]]
    then
      echo "DRY RUN: Would copy '$output' to '$report'."
    elif [[ -f "REPLICATION.md" ]]
    then
      echo "DRY RUN: Would replace the Part B section of REPLICATION.md with '$output'."
    else
      echo "DRY RUN: Would copy '$output' to '$report'."
    fi
  else
    if [[ ! -f "$output" ]]
    then
      echo "ERROR: Generated SIVACOR Part B '$output' not found."
      exit 1
    fi
    if [[ -f "$report" ]]
    then
      cp "$output" "$report"
      echo "Copied '$output' to '$report'."
    elif [[ -f "REPLICATION.md" ]]
    then
      splitline=$(grep -n "You are starting \*PartB\*." REPLICATION.md | cut -f1 -d: | head -1 || true)
      if [[ -z "$splitline" ]]
      then
        splitline=$(grep -n "^## All data files provided$" REPLICATION.md | cut -f1 -d: | head -1 || true)
      fi
      if [[ -z "$splitline" ]]
      then
        echo "ERROR: Could not find the Part B split marker in REPLICATION.md."
        exit 1
      fi
      tmp_report=$(mktemp)
      head -n $(( splitline - 1 )) REPLICATION.md > "$tmp_report"
      cat "$output" >> "$tmp_report"
      mv "$tmp_report" REPLICATION.md
      echo "Replaced the Part B section of REPLICATION.md with '$output'."
    else
      cp "$output" "$report"
      echo "Copied '$output' to '$report'."
    fi
  fi
fi
