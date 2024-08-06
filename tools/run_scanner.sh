#!/bin/bash

# will run the Stata code scanner on the ICPSR directory
# invoke from root of repository

rootdir=$(pwd)
icpsrdir=$1

# find the config file
if [ -f ./tools/parse_yaml.sh ]
then
. ./tools/parse_yaml.sh
level=0
fi

if [ -f ./parse_yaml.sh ]
then
. ./parse_yaml.sh
level=1
fi


# read parameters, depending on where we are
case $level in 
  0)
  [[ -f config.yml ]] && eval $(parse_yaml config.yml)
  ;;
  1)
  [[ -f ../config.yml ]] && eval $(parse_yaml ../config.yml)
  ;;
esac

# fix for running in Codespaces

CI=${CI-$CODESPACES}

[[ -z $icpsrdir ]] && icpsrdir=$(ls -1d *| grep -E "^[1-9][0-9][0-9][0-9][0-9][0-9]$")
if [[ -d $icpsrdir ]]
then 
   echo "Found $icpsrdir - processing."
else
   echo "$icpsrdir is not a directory - don't know what to do"
   exit 2
fi

SOFTWARE=stata
VERSION=17
TAG=$stata17version
MYHUBID=dataeditors
MYNAME=${SOFTWARE}${VERSION}
MYIMG=$MYHUBID/${MYNAME}:${TAG}
# this probably only works for Lars
[[ -z $STATALIC && -z $CI ]] && STATALIC=$(find $HOME/Dropbox/ -name stata.lic.$VERSION| tail -1)


if [[ -z $STATALIC && -z $CI ]]
then
	echo "Could not find Stata license"
	grep STATALIC $0
	exit 2
fi

# modify the scan code

cd tools/Stata_scan_code
#sed -i "s+XXXCODEDIRXXX+../../$icpsrdir+" scan_packages.do

if [ "$CI" == "true" ]
then
# we run without Docker call, because we are inside Docker
  stata-mp -q -b scan_packages.do ../../$icpsrdir
else
  # now run it with the Docker Stata
  docker run -it --rm \
    -v "${STATALIC}":/usr/local/stata/stata.lic \
    -v "$rootdir":/project \
    -w /project/tools/Stata_scan_code \
    $MYIMG -q -b scan_packages.do ../../$icpsrdir

  cd $rootdir
  git add tools/Stata_scan_code/scan_packages.*
  [[ -f $icpsrdir/candidatepackages.xlsx ]] && git add $icpsrdir/candidatepackages.xlsx
fi
# clean up




