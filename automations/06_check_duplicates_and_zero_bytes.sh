#!/bin/bash
#set -e

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)] [(date)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
(tag) is an optional tag to identify the manifest files
(date) is an optional date stamp in YYYY-MM-DD format (defaults to today's date)

Usage examples:
  $0 mydir                    - Uses today's date
  $0 mydir tag                - Uses today's date with tag
  $0 mydir tag 2025-07-09     - Uses specified date with tag
  $0 mydir "" 2025-07-09      - Uses specified date without tag
EOF
exit 2
fi
directory=$1
tag=$2
date_stamp=$3

if [ ! -d generated ] 
then 
  mkdir generated
fi

[ -z $tag ] || tag=".$tag" 
[ -z $date_stamp ] && date_stamp=$(date +%Y-%m-%d)
manifest_file=$(pwd)/generated/manifest$tag.$date_stamp.sha256
metadata_file=$(pwd)/generated/metadata$tag.txt
duplicates_report=$(pwd)/generated/duplicate-files-report$tag.$date_stamp.md
zero_bytes_report=$(pwd)/generated/zero-byte-files-report$tag.$date_stamp.md

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

# Count statistics for verbose output
total_files=$(wc -l < $manifest_file)
duplicate_checksums=$(awk '{print $1}' $manifest_file | sort | uniq -d | wc -l)
duplicate_files=$(wc -l < $tmpfiled)
zero_byte_files=$(awk -F, '$2 == 0 {print $1}' $metadata_file | wc -l)

# Generate Markdown reports
if [ -s $tmpfiled ]; then
  echo "#### Duplicate Files Report" > $duplicates_report
  echo "" >> $duplicates_report
  echo "⚠️ Warning: There are files that are exact duplicates of each other in the report!" >> $duplicates_report
  echo "Files with identical checksums, irregardless of their names, are duplicates." >> $duplicates_report
  echo "If not intentional, you should consider removing duplicates." >> $duplicates_report
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

# Verbose summary output to command line
echo "========================================"
echo "DUPLICATE FILES & ZERO BYTES CHECK SUMMARY"
echo "========================================"
echo "Directory: $directory"
echo "Tag: ${tag:-"(none)"}"
echo "Date: $date_stamp"
echo ""
echo "📊 STATISTICS:"
echo "  Total files checked: $total_files"
echo "  Duplicate checksums found: $duplicate_checksums"
echo "  Total duplicate files: $duplicate_files"
echo "  Zero-byte files found: $zero_byte_files"
echo ""

if [ $duplicate_files -gt 0 ]; then
  echo "⚠️  DUPLICATES DETECTED:"
  echo "  Found $duplicate_files duplicate files across $duplicate_checksums unique checksums"
  echo "  See detailed report: $duplicates_report"
else
  echo "✅ DUPLICATES: No duplicate files found"
fi
echo ""

if [ $zero_byte_files -gt 0 ]; then
  echo "⚠️  ZERO-BYTE FILES DETECTED:"
  echo "  Found $zero_byte_files empty files"
  echo "  See detailed report: $zero_bytes_report"
else
  echo "✅ ZERO-BYTE FILES: No empty files found"
fi
echo ""

echo "📁 REPORTS GENERATED:"
echo "  Duplicates report: $duplicates_report"
echo "  Zero-byte files report: $zero_bytes_report"
echo "========================================"

