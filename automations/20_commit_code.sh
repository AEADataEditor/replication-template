#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022-2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

#set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi

if [ ! -d generated ]
then
  mkdir generated
fi

flag=$2

case $flag in
   run)
   gitmsg="Attempted run $(date +%Y-%m-%d:%H:%M)"
   ;;
   *)
   gitmsg="Adding code from $1"
   ;;
esac

if [ ! -z $1 ] 
then 
  # generated/ may be ignored by .gitignore; its files are committed on purpose
  case $1 in
    generated/*) addflags="-f -v" ;;
    *) addflags="-v" ;;
  esac
  git add $addflags $1
  git commit -m "${premsg}$gitmsg" $1 | tee generated/git-commit.log
  case ${PIPESTATUS[0]} in
     0)
     echo "Files added"
     # count the number of previous tags
     if [ "$flag" == "" ]
     then
      #tags=$(git tag | grep -E "^update" | wc -l)
      # counting them is not reliable, as Bitbucket Pipelines only clones the last 50 commits
      # extract the tag number
      tags=$(git tag | grep -E "^update" | sort | tail -1)
      tags=$(echo $tags | sed 's/update//')
      # now increase counter
      tags=$(expr $tags + 1)
      echo "This is code update $tags"
      git tag -m "Code added from ICPSR" update$tags | tee -a generated/git-commit.log
      echo "Code tagged"
      exit 0
     fi
     ;;
     1)
     echo "No changes detected"
     ;;
     *)
     echo "Not sure how we got here"
     ;;
  esac
fi

exit 0
