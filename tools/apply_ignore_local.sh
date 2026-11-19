#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# Append generated/dot-ignore-local (the local additions to .gitignore) to .gitignore.
#
# Used by automations/30_cleanup_aux.sh and tools/update_tools.sh, so .gitignore is
# always the current template plus the local block. Safe to run repeatedly: a block
# from an earlier run is replaced, not duplicated.
#
# Backward compatibility: an old-style generated/dot-gitignore (a full copy of
# .gitignore with the large files appended after an "# Auto-generated on" line) is
# converted into generated/dot-ignore-local and removed.
#
# Run from the root of the repository. Takes no arguments.

local_ignore=generated/dot-ignore-local
legacy=generated/dot-gitignore
legacy_diff=generated/diff-dot-gitignore.txt
marker='# local additions - auto-generated on'

is_tracked() { git ls-files --error-unmatch "$1" > /dev/null 2>&1; }

# Entries of the local file, without comments and blank lines
entries() { [ -f "$1" ] && grep -v -e '^#' -e '^[[:space:]]*$' "$1"; }

converted=0
if [ -f $legacy ]; then
  # Everything after the last "# Auto-generated on" line, minus comments
  # (no marker: no large files were found, so nothing to carry over)
  legacy_entries=$(awk '/^# Auto-generated on/ {n = 0; seen = 1; next} seen {l[++n] = $0} END {for (i = 1; i <= n; i++) print l[i]}' $legacy \
    | grep -v -e '^#' -e '^[[:space:]]*$')
  if [ -n "$legacy_entries" ]; then
    mkdir -p generated
    { entries $local_ignore; echo "$legacy_entries"; } | sort -u > $local_ignore.entries
    {
      echo "# Files larger than the size limit, which should not be committed to Git"
      cat $local_ignore.entries
    } > $local_ignore
    rm -f $local_ignore.entries
    converted=$(echo "$legacy_entries" | wc -l)
  fi
  for f in $legacy $legacy_diff; do
    [ -f $f ] || continue
    if is_tracked $f; then git rm -q --cached -f $f; fi
    rm -f $f
  done
  echo "Converted old-style $legacy: $converted entries moved to $local_ignore"
fi

if [ -f $local_ignore ]; then
  # Stage it, as generated/ may be ignored
  git add -f $local_ignore 2> /dev/null
fi

[ -f .gitignore ] || touch .gitignore

# Drop the block of an earlier run (it is always the last thing in the file)
if grep -q -F "$marker" .gitignore; then
  sed -i "/^$marker/,\$d" .gitignore
  # and the blank line that preceded it
  sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' .gitignore
fi

if [ -n "$(entries $local_ignore)" ]; then
  {
    echo ""
    echo "$marker $(date +%Y-%m-%d)"
    cat $local_ignore
  } >> .gitignore
  echo "Appended $local_ignore to .gitignore"
fi
exit 0
