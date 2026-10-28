#!/bin/bash
# Generate a template-consistent SIVACOR Part B Markdown file from a TRO JSON-LD file.

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
template="REPLICATION.md"
output=""
steps_output=""
findings_output=""
environment_output=""
appendix_output=""

usage() {
  echo "Usage: $0 [-j tro.jsonld] [-t template.md] [-o output.md] [-d output_dir] [--dry-run]"
  echo ""
  echo "If -j is omitted, the first */tro/tro-*.jsonld file is used."
  echo "Outputs:"
  echo "  generated/sivacor-partb-computing-environment.md"
  echo "  generated/sivacor-partb-replication-steps.md"
  echo "  generated/sivacor-partb-findings.md"
  echo "  generated/sivacor-partb-appendix.md"
  echo "  generated/REPLICATION-PartB-SIVACOR.md"
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

if [[ -z "$output" ]]
then
  output="$output_dir/REPLICATION-PartB-SIVACOR.md"
fi

if [[ ! -f "$template" ]]
then
  echo "ERROR: Template file '$template' not found."
  exit 1
fi

steps_output="$output_dir/sivacor-partb-replication-steps.md"
findings_output="$output_dir/sivacor-partb-findings.md"
environment_output="$output_dir/sivacor-partb-computing-environment.md"
appendix_output="$output_dir/sivacor-partb-appendix.md"
if [[ "$dry_run" != "--dry-run" ]]
then
  mkdir -p "$output_dir"
fi

"$PYTHON" tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-computing-environment --output "$environment_output" $dry_run
"$PYTHON" tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-replication-steps --output "$steps_output" $dry_run
"$PYTHON" tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-findings --output "$findings_output" $dry_run
"$PYTHON" tools/get_sivacor_info.py --jsonld "$jsonld" --key sivacor-appendix --output "$appendix_output" $dry_run

template_input="$template"
tmp_template=""
if grep -Fq "You are starting *PartB*." "$template"
then
  splitline=$(grep -Fn "You are starting *PartB*." "$template" | cut -f1 -d: | head -1)
  tmp_template=$(mktemp)
  tail -n +"$splitline" "$template" > "$tmp_template"
  template_input="$tmp_template"
fi

if [[ "$dry_run" == "--dry-run" ]]
then
  if [[ -f "$environment_output" && -f "$steps_output" && -f "$findings_output" && -f "$appendix_output" ]]
  then
    preview_output=$(mktemp)
    "$PYTHON" tools/replace_placeholders.py --infile "$template_input" --indir "$output_dir" --outfile "$preview_output"
    cat "$preview_output"
    rm "$preview_output"
  else
    echo "DRY RUN: Would combine generated snippets with '$template' into '$output'."
    echo "DRY RUN: Would write the SIVACOR appendix snippet to '$appendix_output'."
  fi
else
  "$PYTHON" tools/replace_placeholders.py --infile "$template_input" --indir "$output_dir" --outfile "$output"
fi

if [[ -n "$tmp_template" ]]
then
  rm "$tmp_template"
fi
