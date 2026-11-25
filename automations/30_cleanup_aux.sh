#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

#set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

[[ ! -d generated ]] && exit 0

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi

# Add all files in generated

git add -f generated/*
git commit -m "${premsg}Adding generated files and logs" generated | tee -a generated/git-commit.log 
  case ${PIPESTATUS[0]} in
     0)
     echo "Files added"
     # count the number of previous tags
     exit 0
     ;;
     1)
     echo "No changes detected"
     ;;
     *)
     echo "Not sure how we got here"
     ;;
  esac
