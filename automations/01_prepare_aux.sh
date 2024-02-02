#!/bin/bash
set -ev
if [ ! -d generated ] 
then 
  mkdir generated
fi

if [ ! -f generated/README.txt ]
then
    echo "This directory contains information generated automatically" > generated/README.txt
    echo "-- Do not modify --" >> generated/README.txt
fi
ls -lR