#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024-2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

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

# Files larger than the limit go into generated/dot-ignore-local: only the local
# additions, never a copy of .gitignore. The file is committed, so entries from
# earlier runs (another directory, an earlier ingest) are kept and merged.
# tools/apply_ignore_local.sh appends it to .gitignore.
local_ignore=generated/dot-ignore-local

if [ -n "$large_files" ]; then
  mkdir -p generated
  {
    [ -f $local_ignore ] && grep -v -e '^#' -e '^[[:space:]]*$' $local_ignore
    echo "$large_files"
  } | sort -u > $local_ignore.entries
  {
    echo "# Files larger than ${limitsize}MB, which should not be committed to Git"
    cat $local_ignore.entries
  } > $local_ignore
  rm -f $local_ignore.entries
fi

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
