#!/bin/bash
set -e

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
EOF
exit 2
fi
directory=$1
tag=$2

if [ ! -d generated ] 
then 
  mkdir generated
fi

[ -z $tag ] || tag=".$tag" 
manifest_file=$(pwd)/generated/manifest$tag.$(date +%Y-%m-%d).sha256
metadata_file=$(pwd)/generated/metadata$tag.txt
duplicates_report=$(pwd)/generated/duplicate-files-report$tag.md
zero_bytes_report=$(pwd)/generated/zero-byte-files-report$tag.md

# Initialize reports
> $duplicates_report
> $zero_bytes_report
tmpfiled=$(mktemp)

# Check for duplicate files
awk '{print $1}' $manifest_file | sort | uniq -d | while read checksum; do
  grep $checksum $manifest_file >> $tmpfiled
done

# Check for zero byte files
awk -F, '$2 == 0 {print $1}' $metadata_file | while read file; do
  echo $file >> $zero_bytes_report
done

# Generate Markdown reports
if [ -s $tmpfiled ]; then
  echo "#### Duplicate Files Report" > $duplicates_report
  echo "" >> $duplicates_report
  echo "⚠️ Warning: There are files that are exact duplicates of each other in the report!" >> $duplicates_report
  echo "" >> $duplicates_report
  echo "| Checksum | File |" >> $duplicates_report
  echo "| --- | --- |" >> $duplicates_report
  awk '{for (i=1; i<=NF; i++) printf $i " "; print ""}' $tmpfiled | while read -r line; do
    checksum=$(echo $line | awk '{print $1}')
    file=$(echo $line | cut -d' ' -f2-)
    echo "| $checksum | $file |" >> $duplicates_report
  done
  echo "" >> $duplicates_report
else
  echo "✅ No duplicates found" > $duplicates_report
  echo "" >> $duplicates_report
fi

if [ -s $zero_bytes_report ]; then
  tmpfile=$(mktemp)
  cp $zero_bytes_report $tmpfile
  echo "#### Zero Byte Files Report" > $zero_bytes_report
  echo "" >> $zero_bytes_report
  echo "| File |" >> $zero_bytes_report
  echo "| --- |" >> $zero_bytes_report
  cat $tmpfile >> $zero_bytes_report
  echo "" >> $zero_bytes_report
else
  echo "✅ No zero byte files found" > $zero_bytes_report
  echo "" >> $zero_bytes_report
fi

