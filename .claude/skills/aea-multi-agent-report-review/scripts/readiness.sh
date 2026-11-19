#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# Read-only readiness gate for a batch of aearep-NNNN repos.
# Usage: readiness.sh [PARENT_DIR]   (default: current directory)
# Prints one tab-separated line per repo:
#   repo  status  instructions_left  parts  partA_commits  dirty  note
# Status values:
#   READY             report filled; dispatch a worker
#   READY-LEFTOVERS   a few "> INSTRUCTIONS" lines remain; dispatch, worker will flag them
#   NEEDS-RA          report is still (mostly) the unfilled template; do not dispatch
#   NEEDS-MERGE       Part A/Part B exist and Part A was edited; merge first (50_merge-parts.sh, needs go-ahead)
#   FINALIZED         approval commit is HEAD-most activity; do not dispatch
#   PENDING-FOLLOWUP  AGENTS-FOLLOWUP.md from an earlier run still present; resolve it first
#   NO-REPORT         no REPLICATION.md
# Nothing here writes to any repo.

set -u
PARENT="${1:-.}"
LEFTOVER_MAX=9   # more "> INSTRUCTIONS" lines than this => treat as unfilled

printf 'repo\tstatus\tinstructions_left\tparts\tpartA_commits\tdirty\tnote\n'
for d in "$PARENT"/aearep-*/; do
  d="${d%/}"; repo=$(basename "$d")
  [ -e "$d/.git" ] || continue
  note=""; parts="no"; pa_commits="-"; dirty="no"; n="-"

  if [ -f "$d/REPLICATION.md" ]; then
    n=$(grep -c '^> INSTRUCTIONS' "$d/REPLICATION.md")
    [ -n "$(git -C "$d" status --porcelain -- REPLICATION.md)" ] && dirty="yes"
  elif [ ! -f "$d/REPLICATION-PartA.md" ] && [ ! -f "$d/REPLICATION-PartB.md" ]; then
    printf '%s\tNO-REPORT\t-\t-\t-\t-\t\n' "$repo"; continue
  fi

  if [ -f "$d/AGENTS-FOLLOWUP.md" ]; then
    printf '%s\tPENDING-FOLLOWUP\t%s\t-\t-\t%s\tearlier agent follow-up not yet resolved\n' "$repo" "$n" "$dirty"; continue
  fi

  appr=$(git -C "$d" log -E --format=%h --grep='#comment (Approved\. )?Ready to submit' -n1)
  if [ -n "$appr" ] && [ "$(git -C "$d" rev-list --count "$appr"..HEAD)" = "0" ]; then
    printf '%s\tFINALIZED\t%s\t-\t-\t%s\tapproval commit %s is HEAD\n' "$repo" "$n" "$dirty" "$appr"; continue
  fi
  [ -n "$appr" ] && note="approved at $appr, later activity exists (revision round?)"

  if [ -f "$d/REPLICATION-PartA.md" ] || [ -f "$d/REPLICATION-PartB.md" ]; then
    parts="yes"
    pa_commits=$(git -C "$d" log --oneline -- REPLICATION-PartA.md | wc -l)
    pa_dirty=$(git -C "$d" status --porcelain -- REPLICATION-PartA.md)
    if [ "$pa_commits" -le 1 ] && [ -z "$pa_dirty" ]; then
      printf '%s\tNEEDS-RA\t%s\t%s\t%s\t%s\tPart A never edited since split (Part A / Findings missing)\n' "$repo" "$n" "$parts" "$pa_commits" "$dirty"; continue
    fi
    printf '%s\tNEEDS-MERGE\t%s\t%s\t%s\t%s\tPart A edited; merge with automations/50_merge-parts.sh (git rm + commit; ask first)\n' "$repo" "$n" "$parts" "$pa_commits" "$dirty"; continue
  fi

  if [ "$n" -gt "$LEFTOVER_MAX" ]; then status="NEEDS-RA"; note="${note:+$note; }report still largely the template"
  elif [ "$n" -gt 0 ]; then status="READY-LEFTOVERS"
  else status="READY"; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$repo" "$status" "$n" "$parts" "$pa_commits" "$dirty" "$note"
done
