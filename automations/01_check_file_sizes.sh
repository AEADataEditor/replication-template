#!/bin/bash
set -e
# default limit
maxsize=100
# Read the configurable limit from config.yml
. ./tools/parse_yaml.sh
eval $(parse_yaml config.yml)

# Set the default limit size to 100MB if not specified in config.yml
limitsize=${limitsize:-$maxsize}

# Find files larger than the limit size
large_files=$(find . -type f -size +${limitsize}M)

# Update .gitignore with files larger than the limit
cp .gitignore generated/dot-gitignore
for file in $large_files; do
  echo "$file" >> generated/dot-gitignore
done

# Write the "large file report" to generated/large-file-report.md only if there are large files
if [ -n "$large_files" ]; then
  report="## Large Files Report\n"
  report+="⚠️ Warning: The repository contains some files larger than $(($limitsize / 1000000))MB. Please be careful when committing these files.\n\n"
  report+="### List of large files:\n"
  for file in $large_files; do
    report+="- $file\n"
  done
  echo -e "$report" > generated/large-file-report.md
fi
