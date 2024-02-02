#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

[[ ! -d generated ]] && exit 0

git add -f generated/*
git commit -m "[skipci] Adding generated files and logs" generated | tee -a generated/git-commit.log 
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
fi