#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

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
  git add $1
  git commit -m "[skipci] $gitmsg" $1 | tee generated/git-commit.log
  case ${PIPESTATUS[0]} in
     0)
     echo "Files added"
     # count the number of previous tags
     if [ "$flag" == "" ]
     then
      tags=$(git tag| wc -l)
      tags=$(expr $tags + 1)
      echo "This is update $tags"
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
