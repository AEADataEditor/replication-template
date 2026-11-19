#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# 32_pull_push.sh
# Push the current branch after pulling in what others pushed in the meantime.
# Needed because the m-parse-manuscript pipeline runs alongside the ingest and
# pushes manuscript_parsed/ to the same branch; the two touch disjoint files.
#
# Usage: 32_pull_push.sh [merge|rebase]
#   merge   (default) merge the remote branch. Keeps the commits, and with them
#           the update<N> tags, as they are: use this in the ingest.
#   rebase  rebase onto the remote branch: use this for work without tags.
#
# Environment:
#   BITBUCKET_BRANCH - branch to push to (default: the current branch)
# Does not push tags; the caller does (git push --tags).

mode="${1:-merge}"
case $mode in
    merge)  pull=(git pull --no-rebase --no-edit) ;;
    rebase) pull=(git pull --rebase) ;;
    *) echo "Usage: $0 [merge|rebase]" >&2; exit 2 ;;
esac

branch="${BITBUCKET_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
for attempt in 1 2 3 4 5; do
    if "${pull[@]}" origin "$branch" && git push origin "HEAD:$branch"; then
        exit 0
    fi
    # Both sides changed the same file: retrying cannot resolve that. Undo the
    # half-done pull, so the checkout is as it was, and say which files clash.
    conflicts=$(git diff --name-only --diff-filter=U)
    if [ -n "$conflicts" ]; then
        git "$mode" --abort
        echo "32_pull_push: cannot $mode origin/$branch, conflicting changes in:" >&2
        echo "$conflicts" >&2
        exit 1
    fi
    echo "Pull/push attempt $attempt failed; retrying"
    sleep $((attempt * 5))
done
echo "32_pull_push: could not push to $branch" >&2
exit 1
