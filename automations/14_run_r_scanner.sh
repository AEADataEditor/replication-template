#!/bin/bash
#set -ev


[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessR" == "no" ]] && exit 0

if [ ! -d generated ] 
then 
  mkdir generated
fi

projectID=$1

#./automations/00_unpack_zip.sh
R CMD BATCH "--args $projectID" tools/check_rds_files.R 
if [ -f check_rds_files.Rout ]; then mv check_rds_files.Rout generated/; fi
if [ -f r-data-checks.csv ]; then mv r-data-checks.csv generated/; fi
if [ -f generated/r-data-checks.csv ]; then python3 tools/csv2md.py generated/r-data-checks.csv; fi

# verify the libraries and dependencies

R CMD BATCH "--args $projectID" tools/check_r_deps.R
if [ -f check_r_deps.Rout ]; then mv check_r_deps.Rout generated/; fi
if [ -f r-deps.csv ]; then mv r-deps.csv generated/; fi
if [ -f generated/r-deps.csv ]; then python3 tools/csv2md.py generated/r-deps.csv; fi
if [ -f r-deps-summary.csv ]; then mv r-deps-summary.csv generated/; fi
if [ -f generated/r-deps-summary.csv ]; then python3 tools/csv2md.py generated/r-deps-summary.csv; fi

# If the R dependency scan produced results, write a software-warnings fragment
# for the top of the report (assembled into software-warnings.md by 24_amend_report.sh)
if [ -f generated/r-deps-summary.csv ]
then
  echo "> [NOTE] R code was detected and scanned. Please compare the identified packages against the requirements stated in the README. See [Appendix: Candidate R packages](#appendix-candidate-r-packages-if-any-based-on-scan) and [Appendix: R environment notes](#appendix-r-environment-notes-if-any)." > generated/software-warnings-r.md
fi

# Run find_cran_date.py if a standardized R package file is found
renv_file=$(find "$projectID" -maxdepth 4 -name "renv.lock" 2>/dev/null | head -1)
if [ -n "$renv_file" ]; then
    echo "Found $renv_file, running find_cran_date.py"
    python3 tools/find_cran_date.py "$renv_file" --output generated/notes-for-r.md
fi

ls