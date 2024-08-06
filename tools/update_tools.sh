#!/bin/bash

# This script is part of replication-template/tools.
# It can also be manually invoked by running
#   wget -O - https://raw.githubusercontent.com/AEADataEditor/replication-template/master/tools/update_tools.sh | bash -x
# NOTE: in order to do that, you have to trust what I've put together here!

GITREPO=replication-template
GITBRANCH=master

wget -O newversion.zip https://github.com/AEADataEditor/${GITREPO}/archive/refs/heads/${GITBRANCH}.zip
unzip newversion.zip 
cd ${GITREPO}-${GITBRANCH}
[[ -f config.yml ]] && mv config.yml config-template.yml
tar cvf ../tmp.tar tools/ automations/ *.yml template-* requirements.txt sample-language-report.md .gitignore
cd ..
tar xvf tmp.tar
# Copy any updated MD files to "template" directory
# Check that it exists first!
[[ -d template ]] || mkdir template
for file in REPLICATION EXTERNAL-REPORT
do
 cp ${GITREPO}-${GITBRANCH}/$file.md template/new-$file.md
done
git add tools/ automations/ *.yml template-* template/* sample-language-report.md .gitignore
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

