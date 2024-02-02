#!/bin/bash

# This script is part of replication-template/tools.
# It can also be manually invoked by running
#   wget -O - https://raw.githubusercontent.com/AEADataEditor/replication-template/master/tools/update_tools.sh | bash -x
# NOTE: in order to do that, you have to trust what I've put together here!

GITREPO=replication-template
GITBRANCH=master
type="full"

echo "Using default gitrepo ${GITREPO} and gitbranch ${GITBRANCH}"

wget -O newversion.zip https://github.com/AEADataEditor/${GITREPO}/archive/refs/heads/${GITBRANCH}.zip
unzip newversion.zip 
cd ${GITREPO}-${GITBRANCH}

if [[ "$type" == "full" ]]
then
  echo "Adding everything"
  tar cvf ../tmp.tar [A-Z]* [a-z]* .[a-z]*
  cd ..
  tar xvf tmp.tar
  \rm -rf ${GITREPO}-${GITBRANCH} tmp.tar newversion.zip
  git add [A-Z]* [a-z]* .[a-z]* 
  git add -f *.txt */*.txt
fi

git commit -m "[skip ci] Init of repo from ${GITREPO}"
case $? in
     0)
     echo "Code added"
     ;;
     1)
     echo "No changes detected"
     ;;
     *)
     echo "Not sure how we got here"
     ;;
  esac
exit 0

