#!/bin/bash
#set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

[[ ! -d generated ]] && exit 0

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi

# if gitignore was amended, copy it from the generated folder

if [ -f generated/dot-gitignore ]
then
  cp generated/dot-gitignore .gitignore
  git add -f .gitignore
  git commit -m "${premsg}Updating .gitignore" .gitignore | tee -a generated/git-commit.log
  case ${PIPESTATUS[0]} in
     0)
     echo ".gitignore updated"
     ;;
     1)
     echo "No changes detected"
     ;;
     *)
     echo "Not sure how we got here"
     ;;
  esac
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
fi
