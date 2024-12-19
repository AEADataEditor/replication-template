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

# define outputs

appendix="$indir/REPLICATION_appendix.md"
basefile="REPLICATION.md"
filled="$indir/REPLICATION-filled.md"
template="template/REPLICATION_appendix.md"

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

if [ -f "$indir/PII_stata_scan_summary.txt" ]
then
   # create a Markdown version of the Stata scan summary
   echo '```' > "$indir/pii-summary.md"
   cat "$indir/PII_stata_scan_summary.txt" >> "$indir/pii-summary.md"
   echo '```' >> "$indir/pii-summary.md"
   echo "" >> "$indir/pii-summary.md"
   # Check if there is a non-zero count of variables with POTENTIAL PII in the summary file:
   if grep -q "POTENTIAL PII = 0" "$indir/PII_stata_scan_summary.txt"; then
      echo "Our courtesy checks did not identify any variables potentially including PII." >> "$indir/pii-summary.md"
   else
      echo "> [REQUIRED] We have identified possible PII. Please verify, and if necessary, remove from deposit. If not removing, please explicitly confirm in your response letter that the identified variables are OK to publish without restrictions." >> "$indir/pii-summary.md"
   fi
   echo "" >> "$indir/pii-summary.md"

else
   echo "$indir/PII_stata_scan_summary.txt not found, creating empty version"
   echo "Check not run or no PII found." > "$indir/pii-summary.md"
fi

# Identify the line with the 
# Now use the template to fill it in
python3 tools/replace_placeholders.py --infile $template --indir "$indir" --outfile $appendix

# If there is a line with "Automatically Generated Appendices", we remove it and everything after it.
tmpfile=$(mktemp)

if grep -q "Automatically Generated Appendices" $basefile
then
   sed  '/Automatically Generated Appendices/,$d' $basefile > $tmpfile
else
   cp $basefile $tmpfile
fi

# Append the generated appendix to the base file
echo "" >> $tmpfile
cat $tmpfile $appendix > $filled



