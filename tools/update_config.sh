#!/bin/bash
#set -ev

# Get some functions

. ./tools/parse_yaml.sh

# Check for config.yml

if [ ! -f config.yml ]; then
    # see if the template is there
    if [ -f template/new-config.yml ]; then
        cp template/new-config.yml config.yml
    else
      echo "config.yml not found!"
      exit 1
    fi
fi

# read parameters
eval $(parse_yaml config.yml)

# from environment
#          - name: openICPSRID   
#          - name: jiraticket
#          - name: ZenodoID
#          - name: DataverseID
#          - name: OSFID
#          - name: main

# environment overwrite config

openICPSRID="${openICPSRID:-$openicpsr}"
ZenodoID="${ZenodoID:-$zenodo}"
DataverseID="${DataverseID:-$dataverse}"
OSFID="${OSFID:-$osf}"
MainFile="${MainFile:-$main}"
jiraticket="${jiraticket:-$jiraticket}"

# write it back
config=config.yml

sed -i "s/openicpsr: \(.*\)/openicpsr: $openICPSRID/" $config
sed -i "s/osf: \(.*\)/osf: $OSFID/" $config
sed -i "s/dataverse: \(.*\)/dataverse: $DataverseID/" $config
sed -i "s/zenodo: \(.*\)/zenodo: $ZenodoID/" $config
sed -i "s/main: \(.*\)/main: $MainFile/" $config  
sed -i "s/jiraticket: \(.*\)/jiraticket: $jiraticket/" $config  

cat $config
