#!/bin/bash

if [[ -z $1 ]]
then
cat << EOF

$0 (codeocean-number)

will 
- create, if necessary, a live git clone of codeocean capsule with provided number
- sync that capsule from Codeocean to locally
- create, if necessary, a local static copy (not submodule)
- sync the Codeocean clone with the local static copy
EOF
exit 2
fi

number=$1

live=codeocean-${number}-live
static=codeocean-${number}

if [[ -d $live ]]
then
   (cd $live && git pull)
else
   git clone https://git.codeocean.com/capsule-${number}.git $live
fi

if [[ -d $static ]]
then
   git pull || exit 2
   git rm $static/code/*
   rsync -auv --exclude ".git" $live/ $static/
   git add $static/code
else
   mkdir $static
   rsync -auv --exclude ".git" $live/ $static/
fi

echo "Done."
