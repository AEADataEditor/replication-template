#!/bin/bash
set -ev

zipfile=$1.zip

if [[ ! -z $zipfile ]]
then
  basename=$(basename $zipfile .zip)

  unzip -n $zipfile -d $basename
fi