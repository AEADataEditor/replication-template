#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

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
# Full list of duplicates, shown in the report's appendix. Not named
# duplicate-files-report*, so that 24_amend_report.sh does not mistake it
# for the summary.
duplicates_full=$(pwd)/generated/duplicate-files-full$tag.$date_stamp.md
zero_bytes_report=$(pwd)/generated/zero-byte-files-report$tag.$date_stamp.md
# Full lists of zero-byte and suspiciously small files, for the appendix. Not
# named zero-byte-files-report*, so that 24_amend_report.sh does not mistake it
# for the summary.
zero_bytes_full=$(pwd)/generated/zero-byte-files-full$tag.$date_stamp.md
# Files with one of these (binary-format) extensions and fewer bytes than the
# threshold are suspicious: a real file of that type has a larger header, so
# they are typically placeholders (Dropbox, OneDrive, git-lfs pointers, ...).
small_bytes=${SMALL_FILE_BYTES:-512}
small_exts=${SMALL_FILE_EXTENSIONS:-"dta xlsx xls xlsm zip gz 7z tar pdf png jpg jpeg gif tif tiff docx pptx rds rdata rda mat sav sas7bdat parquet feather fst h5 hdf5 pkl"}
# Number of duplicate files shown as a sample in the main report
sample_lines=${DUPLICATES_SAMPLE_LINES:-12}

# Initialize reports
> $duplicates_report
> $duplicates_full
> $zero_bytes_report
> $zero_bytes_full
tmpfiled=$(mktemp)
tmptable=$(mktemp)

# Check for duplicate files
awk '{print $1}' $manifest_file | sort | uniq -d | while read checksum; do
  grep $checksum $manifest_file >> $tmpfiled
done

# Check for zero byte files and for suspiciously small files of binary types.
# Rows are Markdown table rows; the last comma-separated field is the size.
tmpzero=$(mktemp)
tmpsmall=$(mktemp)
awk -F, '$NF ~ /^[0-9]+$/ && $NF == 0 {sub(/,[0-9]+$/, ""); print "| " $0 " |"}' $metadata_file > $tmpzero
awk -F, -v max=$small_bytes -v exts="$small_exts" '
  BEGIN {n = split(exts, a, " "); for (i = 1; i <= n; i++) e[a[i]] = 1}
  $NF ~ /^[0-9]+$/ && $NF > 0 && $NF < max {
    size = $NF; path = $0; sub(/,[0-9]+$/, "", path)
    m = split(path, p, "."); ext = tolower(p[m])
    if (m > 1 && (ext in e)) print "| " path " | " size " |"
  }' $metadata_file > $tmpsmall

# Count statistics for verbose output
total_files=$(wc -l < $manifest_file)
duplicate_checksums=$(awk '{print $1}' $manifest_file | sort | uniq -d | wc -l)
duplicate_files=$(wc -l < $tmpfiled)
zero_byte_files=$(wc -l < $tmpzero)
small_files=$(wc -l < $tmpsmall)

# Generate Markdown reports
if [ -s $tmpfiled ]; then
  # Table rows, one per duplicate file (grouped by checksum)
  awk '{for (i=1; i<=NF; i++) printf $i " "; print ""}' $tmpfiled | while read -r line; do
    checksum=$(echo $line | awk '{print $1}')
    file=$(echo $line | cut -d' ' -f2-)
    echo "| $checksum | $file |" >> $tmptable
  done

  # Main report: counts and a short sample
  echo "#### Duplicate Files Report" > $duplicates_report
  echo "" >> $duplicates_report
  echo "⚠️ Warning: There are files that are exact duplicates of each other in the report!" >> $duplicates_report
  echo "Files with identical checksums, irregardless of their names, are duplicates." >> $duplicates_report
  echo "If not intentional, you should consider removing duplicates." >> $duplicates_report
  echo "" >> $duplicates_report
  echo "- Files checked: $total_files" >> $duplicates_report
  echo "- Files that have at least one duplicate: $duplicate_files" >> $duplicates_report
  echo "- Groups of identical files: $duplicate_checksums" >> $duplicates_report
  echo "" >> $duplicates_report
  if [ $duplicate_files -gt $sample_lines ]; then
    echo "A sample of $sample_lines of the $duplicate_files duplicate files is shown below. The full list is in the Appendix (\"Duplicate files\")." >> $duplicates_report
    echo "" >> $duplicates_report
  fi
  echo "| Checksum | File |" >> $duplicates_report
  echo "| --- | --- |" >> $duplicates_report
  head -n $sample_lines $tmptable >> $duplicates_report
  echo "" >> $duplicates_report

  # Appendix: full list
  echo "Files with identical checksums, irregardless of their names, are duplicates ($duplicate_files files in $duplicate_checksums groups)." > $duplicates_full
  echo "" >> $duplicates_full
  echo "| Checksum | File |" >> $duplicates_full
  echo "| --- | --- |" >> $duplicates_full
  cat $tmptable >> $duplicates_full
  echo "" >> $duplicates_full
else
  echo "✅ No duplicates found" > $duplicates_report
  echo "" >> $duplicates_report
  echo "✅ No duplicates found" > $duplicates_full
  echo "" >> $duplicates_full
fi
rm -f $tmpfiled $tmptable

# Write one section of the zero-byte report: counts and a sample in the main
# report, the complete list in the appendix file.
# usage: write_pruned_section (heading) (intro) (table header) (table rule) (rows file) (none message)
write_pruned_section() {
  local count
  count=$(wc -l < $5)
  echo "#### $1" >> $zero_bytes_report
  echo "" >> $zero_bytes_report
  echo "#### $1" >> $zero_bytes_full
  echo "" >> $zero_bytes_full
  if [ $count -eq 0 ]; then
    echo "$6" >> $zero_bytes_report
    echo "" >> $zero_bytes_report
    echo "$6" >> $zero_bytes_full
    echo "" >> $zero_bytes_full
    return
  fi
  echo "$2" >> $zero_bytes_report
  echo "" >> $zero_bytes_report
  echo "- Files found: $count" >> $zero_bytes_report
  echo "" >> $zero_bytes_report
  if [ $count -gt $sample_lines ]; then
    echo "A sample of $sample_lines of the $count files is shown below. The full list is in the Appendix (\"Zero-byte and suspiciously small files\")." >> $zero_bytes_report
    echo "" >> $zero_bytes_report
  fi
  echo "$3" >> $zero_bytes_report
  echo "$4" >> $zero_bytes_report
  head -n $sample_lines $5 >> $zero_bytes_report
  echo "" >> $zero_bytes_report
  echo "$2 ($count files)" >> $zero_bytes_full
  echo "" >> $zero_bytes_full
  echo "$3" >> $zero_bytes_full
  echo "$4" >> $zero_bytes_full
  cat $5 >> $zero_bytes_full
  echo "" >> $zero_bytes_full
}

write_pruned_section "Zero Byte Files Report" \
  "⚠️ Warning: There are empty (zero-byte) files in the deposit." \
  "| File |" "| --- |" $tmpzero \
  "✅ No zero byte files found"
write_pruned_section "Suspiciously Small Files" \
  "⚠️ Warning: There are files of a binary type (e.g., Stata, Excel, PDF, ZIP) that are smaller than $small_bytes bytes. They may be placeholders (Dropbox, OneDrive, git-lfs) rather than the real files." \
  "| File | Bytes |" "| --- | --- |" $tmpsmall \
  "✅ No suspiciously small files found"
if [ -s $tmpzero ] || [ -s $tmpsmall ]; then
  echo "You may want to consult [this note by the Data Editor](https://aeadataeditor.github.io/posts/2025-08-18-dropbox-etc) for a potential solution." >> $zero_bytes_report
  echo "" >> $zero_bytes_report
fi
rm -f $tmpzero $tmpsmall

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
echo "  Suspiciously small files found: $small_files"
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

if [ $small_files -gt 0 ]; then
  echo "⚠️  SUSPICIOUSLY SMALL FILES DETECTED:"
  echo "  Found $small_files binary-type files under $small_bytes bytes"
  echo "  See detailed report: $zero_bytes_report"
else
  echo "✅ SMALL FILES: No suspiciously small files found"
fi
echo ""

echo "📁 REPORTS GENERATED:"
echo "  Duplicates report: $duplicates_report"
echo "  Duplicates full list (appendix): $duplicates_full"
echo "  Zero-byte files report: $zero_bytes_report"
echo "  Zero-byte and small files full list (appendix): $zero_bytes_full"
echo "========================================"

