#!/bin/bash
#set -ev

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

# Count files that will be added
file_count=$(find $directory -type f -size +${limitsize}M | wc -l)

# Only add comment and files if there are large files found
if [ $file_count -gt 0 ]; then
  # Add comment header with date and reason
  echo "" >> generated/dot-gitignore
  echo "# Auto-generated on $(date '+%Y-%m-%d %H:%M:%S')" >> generated/dot-gitignore
  echo "# The following files exceed ${limitsize}MB and should not be committed to Git" >> generated/dot-gitignore

  # Add the large files
  while IFS= read -r -d '' file; do
    echo "$file" >> generated/dot-gitignore
  done < <(find $directory -type f -size +${limitsize}M -print0)
fi

# Create diff file showing changes
diff -u .gitignore generated/dot-gitignore > generated/diff-dot-gitignore.txt || true

# Write the "large file report" to generated/large-file-report.md only if there are large files
if [ -n "$large_files" ]; then
  report="#### Large Files Report\n\n"
  report+="⚠️ Warning: The deposit contains some files larger than $limitsize MB. Replicator should be careful when committing files within the Git repository.\n\n"
  report+="**List of large files**\n\n"
  report+="\`\`\`\n"
  while IFS= read -r -d '' file; do
    report+="$file\n"
  done < <(find $directory -type f -size +${limitsize}M -print0)
  report+="\`\`\`\n"
  echo -e "$report" > generated/large-file-report.md
fi

# Write out to console if CI
if [ ! -z $CI ]; then
  echo "$large_files"
fi
