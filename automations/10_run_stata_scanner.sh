#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessStata" == "no" ]] && exit 0

if [ -z $1 ]
then
cat << EOF
$0 (projectID)

where (projectID) could be openICPSR, Zenodo, etc. ID.
EOF
exit 2
fi
projectID=$1


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



if [ ! -d $projectID ]
then
  echo "$projectID not a directory"
  exit 2
fi

# run the scanner for packages
chmod a+rx tools/run_scanner.sh
./tools/run_scanner.sh $projectID

if [ -f $projectID/candidatepackages.xlsx ] 
then 
  mv $projectID/candidatepackages.xlsx generated/
fi
if [ -f $projectID/candidatepackages.csv ]; then mv $projectID/candidatepackages.csv generated/; fi
if [ -f generated/candidatepackages.csv ]; then python3 tools/csv2md.py generated/candidatepackages.csv; fi


# run scanner for PII
if [ -f PII_stata_scan.do ]
then
  cd $projectID
  stata-mp -b do ../PII_stata_scan.do
  cd -
fi

if [ -f $projectID/pii_stata_output.csv ]
then 
  mv $projectID/pii_stata_output.csv generated/
fi

if [ -f $projectID/PII_stata_scan.log ]
then
  mv $projectID/PII_stata_scan.log generated/
  tail -10 generated/PII_stata_scan.log | tee generated/PII_stata_scan_summary.txt
  if [ -f generated/pii_stata_output.csv ]; then python3 tools/csv2md.py generated/pii_stata_output.csv; fi
  
fi

