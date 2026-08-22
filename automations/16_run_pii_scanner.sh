#!/bin/bash
#set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessPii" == "no" ]] && exit 0

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


# run scanner for PII
if [ -f PII_stata_scan.do ]
then
  cd $directory
  stata-mp -b do ../PII_stata_scan.do
  cd -
fi

if [ -f $directory/pii_stata_output.csv ]
then 
  mv $directory/pii_stata_output.csv generated/
fi

if [ -f $directory/PII_stata_scan.log ]
then
  mv $directory/PII_stata_scan.log generated/
  tail -10 generated/PII_stata_scan.log | tee generated/PII_stata_scan_summary.txt
  if [ -f generated/pii_stata_output.csv ]
  then 
    tmpfile=$(mktemp)
    head -20 generated/pii_stata_output.csv > $tmpfile
    python3 tools/csv2md.py $tmpfile -o generated/pii_stata_output.md
    if [[ $(cat generated/pii_stata_output.csv | wc -l) -gt 20 ]]
    then
      echo "" >> generated/pii_stata_output.md
      echo "More than 20 rows in the output, only showing the first 20" >> generated/pii_stata_output.md
    fi
  fi
  
fi

