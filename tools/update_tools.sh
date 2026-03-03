#!/bin/bash

# This script is part of replication-template/tools.
# It can also be manually invoked by running
#   wget -O - https://raw.githubusercontent.com/AEADataEditor/replication-template/master/tools/update_tools.sh | bash -x
# NOTE: in order to do that, you have to trust what I've put together here!

GITREPO=replication-template
GITBRANCH=master

wget -O newversion.zip https://github.com/AEADataEditor/${GITREPO}/archive/refs/heads/${GITBRANCH}.zip
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to download repository archive"
    exit 1
fi

unzip newversion.zip
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to unzip repository archive"
    rm -f newversion.zip
    exit 1
fi

cd ${GITREPO}-${GITBRANCH}
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to change to repository directory"
    rm -rf newversion.zip ${GITREPO}-${GITBRANCH}
    exit 1
fi
# Copy any updated MD files to "template" directory
# Check that it exists first!
[[ -d template ]] || mkdir template
for file in REPLICATION.md EXTERNAL-REPORT.md config.yml
do
 cp $file template/new-$file
done
tar cvf ../tmp.tar tools/ automations/ bitbucket*  template-* template/ requirements.txt sample-language-report.md .gitignore run.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create tar archive"
    cd ..
    rm -rf ${GITREPO}-${GITBRANCH} tmp.tar newversion.zip
    exit 1
fi

cd ..
tar xvf tmp.tar
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to extract tar archive"
    rm -rf ${GITREPO}-${GITBRANCH} tmp.tar newversion.zip
    exit 1
fi

git add tools/ automations/ *.yml template-* template/* sample-language-report.md .gitignore run.sh
git add -f tools/requ*txt
git add -f requirements.txt
git commit -m '[skip ci] Update of tools'
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
\rm -rf ${GITREPO}-${GITBRANCH} tmp.tar newversion.zip
exit 0

