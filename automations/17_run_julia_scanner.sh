#!/bin/bash
set -ev


[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessJulia" == "no" ]] && exit 0
[[ -z $(which julia) ]] && exit 0

if [ ! -d generated ] 
then 
  mkdir generated
fi

projectID=$1


# Run the Julia scanner using `pkgdeps`
julia tools/scan_pkg.jl $projectID generated/julia_pkgs.csv

