#!/bin/bash
#set -ev

configfile=config.yml
# Get some functions

. ./tools/parse_yaml.sh

# Check for config.yml

if [ ! -f $configfile ]; then
    # see if the template is there
    if [ -f template/new-$configfile ]; then
        cp template/new-$configfile $configfile
    else
      echo "$configfile not found!"
      exit 1
    fi
fi

# Save pipeline-provided values before eval overwrites them.
# config.yml and pipeline vars share the same key name for jiraticket, so
# eval $(parse_yaml ...) silently clobbers the pipeline/environment variable.
_env_jiraticket="${jiraticket:-}"

# read parameters
eval $(parse_yaml $configfile)

# from environment
#          - name: openICPSRID
#          - name: jiraticket
#          - name: ZenodoID
#          - name: DataverseID
#          - name: OSFID
#          - name: main
#          - name: mcid

# environment overwrite config

openICPSRID="${openICPSRID:-$openicpsr}"
ZenodoID="${ZenodoID:-$zenodo}"
DataverseID="${DataverseID:-$dataverse}"
OSFID="${OSFID:-$osf}"
MainFile="${MainFile:-$main}"
# Restore pipeline/environment value if it was set; otherwise keep config.yml value
jiraticket="${_env_jiraticket:-$jiraticket}"
mcid="${mcid:-$mcid}"


# write it back

sed -i "s/openicpsr:\(.*\)/openicpsr: $openICPSRID/" $configfile
sed -i "s/osf:\(.*\)/osf: $OSFID/" $configfile
sed -i "s/dataverse:\(.*\)/dataverse: $DataverseID/" $configfile
sed -i "s/zenodo:\(.*\)/zenodo: $ZenodoID/" $configfile
sed -i "s/main:\(.*\)/main: $MainFile/" $configfile
sed -i "s/jiraticket:\(.*\)/jiraticket: $jiraticket/" $configfile
sed -i "s/mcid:\(.*\)/mcid: $mcid/" $configfile  

cat $configfile
