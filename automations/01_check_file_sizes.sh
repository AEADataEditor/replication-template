#!/bin/bash
set -ev

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
EOF
exit 2
fi
directory=$1

# default limit
maxsize=100
# Read the configurable limit from config.yml
. ./tools/parse_yaml.sh
eval $(parse_yaml config.yml)

# Set the default limit size to 100MB if not specified in config.yml
limitsize=${limitsize:-$maxsize}

# Find files larger than the limit size
large_files=$(find $directory -type f -size +${limitsize}M)

# Update .gitignore with files larger than the limit
cp .gitignore generated/dot-gitignore
for file in $large_files; do
  echo "$file" >> generated/dot-gitignore
done

# Write the "large file report" to generated/large-file-report.md only if there are large files
if [ -n "$large_files" ]; then
  report="#### Large Files Report\n\n"
  report+="⚠️ Warning: The deposit contains some files larger than $limitsize MB. Replicator should be careful when committing files within the Git repository.\n\n"
  report+="### List of large files:\n\n"
  report+="\`\`\`\n"
  for file in $large_files; do
    report+="$file\n"
  done
  report+="\`\`\`\n"
  echo -e "$report" > generated/large-file-report.md
fi
