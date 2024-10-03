#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

[[ -z $1 ]] && indir=generated || indir=$@

if [ ! -d "$indir" ]
then
   echo "$indir is not a directory"
   echo "Please check, and if necessary, call this script"
   echo "as $0 [name of dir]"
   exit 2
fi

# if necessary, install the requirements
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Test for two optional files

if [ ! -f "$indir/candidatepackages.md" ]
then
   echo "$indir/candidatepackages.md not found, creating empty version"
   echo "Check not run or no packages found." > "$indir/candidatepackages.md"
fi


if [ ! -f "$indir/r-deps-summary.md" ]
then
   echo "$indir/r-deps-summary.md not found, creating empty version"
   echo "Check not run or no packages found." > "$indir/r-deps-summary.md"
fi

if [ ! -f "$indir/python-deps.md" ]
then
   echo "$indir/python-deps.md not found, creating empty version"
   echo "Check not run or no packages found." > "$indir/python-deps.md"
fi


# Now use the template to fill it in
python3 tools/replace_placeholders.py --indir "$indir" --outfile "$indir/REPLICATION-filled.md"
