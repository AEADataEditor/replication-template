#!/bin/bash
#set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessStata" == "no" ]] && exit 0

# Define the $pythonbin variable based on the operating system using a case statement
case "$(uname -o)" in
  Msys)
    pythonbin="python"
    ;;
  *)
    pythonbin="python3"
    ;;
esac

if [ -z $1 ]
then
cat << EOF
$0 (directory)

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
EOF
exit 2
fi
directory=$1


[ -f ./tools/parse_yaml.sh ] && source ./tools/parse_yaml.sh
if [[ -f config.yml ]]
then
  # lets read it
  echo "--------------------------------"
  cat config.yml
  echo "--------------------------------"
  tmpfile=$(mktemp)
  parse_yaml config.yml > $tmpfile
  source $tmpfile
fi


if [ ! -d generated ] 
then 
  mkdir generated
fi



if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
fi

# run the scanner for packages
chmod a+rx tools/run_scanner.sh
./tools/run_scanner.sh $directory

if [ -f $directory/candidatepackages.xlsx ] 
then 
  mv $directory/candidatepackages.xlsx generated/
fi
if [ -f $directory/candidatepackages.csv ]; then mv $directory/candidatepackages.csv generated/; fi
if [ -f generated/candidatepackages.csv ]; then $pythonbin tools/csv2md.py generated/candidatepackages.csv; fi
