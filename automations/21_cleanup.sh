#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi


if [ ! -z $1 ] 
then 
  [[ -f README.md ]] && git rm    README.md 
  [[ -d build ]]     && git rm -r build
  git commit -m "${premsg}Cleaning up" | tee generated/git-commit.log
  case ${PIPESTATUS[0]} in
     0)
     echo "Cleanup done"
     # count the number of previous tags
     exit 0
     ;;
     1)
     echo "No cleanup needed"
     ;;
     *)
     echo "Not sure how we got here"
     ;;
  esac
  exit 0
fi
