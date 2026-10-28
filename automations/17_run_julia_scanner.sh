#!/bin/bash
#set -ev


[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessJulia" == "no" ]] && exit 0
[[ -z $(which julia) ]] && exit 0

if [ ! -d generated ] 
then 
  mkdir generated
fi

projectID=$1

# Check for Manifest.toml and Project.toml files
manifest_files=$(find $projectID -name 'Manifest.toml')
project_files=$(find $projectID -name 'Project.toml')

# Generate Markdown formatted checklist
checklist="## Julia Project Checklist\n\n"
checklist+="| File          | Present |\n"
checklist+="|---------------|---------|\n"

if [ -n "$manifest_files" ]; then
  for file in $manifest_files; do
    checklist+="| $file | Yes |\n"
  done
else
  checklist+="| Manifest.toml | No |\n"
fi

if [ -n "$project_files" ]; then
  for file in $project_files; do
    checklist+="| $file | Yes |\n"
  done
else
  checklist+="| Project.toml | No |\n"
fi

echo -e "$checklist" > generated/julia_toml_chks.md

# Run the Julia scanner using `pkgdeps`
julia tools/scan_pkg.jl $projectID generated/julia_pkgs.csv

# Convert CSV to Markdown
if [ -f generated/julia_pkgs.csv ]; then
  python3 tools/csv2md.py generated/julia_pkgs.csv
fi
