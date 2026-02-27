#!/bin/bash
#set -ev

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

basefile="REPLICATION.md"
filled="$indir/REPLICATION-filled.md"
template_app="template/REPLICATION_appendix.md"
appendix="$indir/REPLICATION_appendix.md"

# Test for optional files

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
      echo "> [REQUIRED] Our scanner identified possible PII. Please verify, and if necessary, remove from deposit. If not removing, please explicitly confirm in your response letter that the identified variables are OK to publish without restrictions." >> "$indir/pii-summary.md"
   fi
   echo "" >> "$indir/pii-summary.md"

else
   echo "$indir/PII_stata_scan_summary.txt not found, creating empty version"
   echo "Check not run or no PII found." > "$indir/pii-summary.md"
fi

# Check for duplicate files report
latest_duplicates=$(ls "$indir"/duplicate-files-report*.md 2>/dev/null | sort -t. -k3 -r | head -1)
if [ -n "$latest_duplicates" ]; then
  cp "$latest_duplicates" "$indir/duplicate-files-report.md"
else
  echo "⚠️ Duplicate file report not run" > "$indir/duplicate-files-report.md"
fi

# Check for zero byte files report
latest_zerobyte=$(ls "$indir"/zero-byte-files-report*.md 2>/dev/null | sort -t. -k3 -r | head -1)
if [ -n "$latest_zerobyte" ]; then
  cp "$latest_zerobyte" "$indir/zero-byte-files-report.md"
else
  echo "⚠️ Zero byte files report not run" > "$indir/zero-byte-files-report.md"
fi

# Check for linecount report
latest_linecount=$(ls "$indir"/linecount*.md 2>/dev/null | sort -t. -k2 -r | head -1)
if [ -n "$latest_linecount" ]; then
  cp "$latest_linecount" "$indir/linecount.md"
else
  echo "⚠️ Line count report not run" > "$indir/linecount.md"
fi

# Check for restricted data manifest
if [ ! -f "$indir/manifest.restricted.txt" ]; then
  echo "not present" > "$indir/manifest.restricted.txt"
fi



# Now use the template to fill in the main part
tmpmain=$(mktemp)
tmpapp=$(mktemp)

python3 tools/replace_placeholders.py --infile ${basefile} --indir "$indir" --outfile $tmpmain

# If the {{ large-file-report.md }} was not generated, remove the placeholder

if [ ! -f "generated/large-file-report.md" ]; then
  sed -i 's/{{ large-file-report.md }}/\n/' $tmpmain
fi

# If there is a line with "Automatically Generated Appendices", we remove it and everything after it.

if grep -q "Automatically Generated Appendices" $tmpmain
then
   sed  '/Automatically Generated Appendices/,$d' $tmpmain > $tmpapp
else
   cp $tmpmain $tmpapp
fi

# Fill in the appendix

python3 tools/replace_placeholders.py --infile ${template_app} --indir "$indir" --outfile $appendix

# DISABLED: Append the generated appendix to the base file
echo "" >> $tmpapp
#cat $tmpapp $appendix > $filled

cat $tmpapp > $filled

# Cleanup
