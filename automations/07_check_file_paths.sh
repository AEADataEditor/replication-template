#!/bin/bash
#set -e

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)]

where (directory) is the directory containing code files to be checked.
EOF
exit 2
fi
directory=$1
tag=$2
[ -z $tag ] || tag=".$tag"

if [ ! -d generated ] 
then 
  mkdir generated
fi

csv_file=$(pwd)/generated/file-paths-report${tag}.csv
report_file=$(pwd)/generated/file-paths-report${tag}.md
summary_file=$(pwd)/generated/file-paths-summary${tag}.md

# Initialize CSV file
echo "Warning,File,Windows Paths,Unix Paths,Mixed Paths,Drive Letters" > $csv_file

# Function to check file paths
check_file_paths() {
  local filedirectory=$1
  local name=$2
  local file="$filedirectory/$name"
  # The regex '[a-zA-Z0-9_.${}()-]+\\' matches Windows file paths (e.g., path\to\file, ${var}\path)
  local windows_paths=$(grep -oP '[a-zA-Z0-9_.${}()-]+\\' "$file" | wc -l)
  # The regex '[a-zA-Z]:\\' matches drive letters (e.g., C:\)
  local drive_letters=$(grep -oP '[a-zA-Z]:\\' "$file" | wc -l)
  # The regex '[^a-zA-Z0-9_/-]/[^a-zA-Z0-9_/-]' matches partial Unix-style file paths (e.g., path/to/file)
  local unix_paths=$(grep -oP '[^a-zA-Z0-9_/-]/[^a-zA-Z0-9_/-]' "$file" | wc -l)
  local mixed_paths=0
  local warning=""

  if [ $windows_paths -gt 0 ] && [ $unix_paths -gt 0 ]; then
    mixed_paths=1
  fi

  if [ $windows_paths -gt 0 ]; then
    warning="⚠️"
  fi

  echo "$warning,$name,$windows_paths,$unix_paths,$mixed_paths,$drive_letters" >> $csv_file
}

# Iterate over code files listed in generated/programs-list.txt and check paths
# Filter out files in "ado" directories or with "ado" extensions
grep -v "Generated on" generated/programs-list.txt | grep -v "/ado/" | grep -v "\.ado$" | while read -r file; do
  check_file_paths "$directory" "$file"
done

# Initialize Markdown report
> $report_file

# Generate Markdown report header
echo "#### File Paths Report" > $report_file
echo "" >> $report_file
echo "Generated on $(date)" >> $report_file
echo "" >> $report_file
echo "|  | File | Windows Paths | Unix Paths | Mixed Paths | Drive Letters |" >> $report_file
echo "| --- | --- | --- | --- | --- | --- |" >> $report_file

# Read CSV file and generate Markdown table
tail -n +2 $csv_file | while IFS=, read -r warning name windows_paths unix_paths mixed_paths drive_letters; do
  echo "| $warning | $name | $windows_paths | $unix_paths | $mixed_paths | $drive_letters |" >> $report_file
done

# Compute overall statistics from CSV file
total_files=$(tail -n +2 $csv_file | wc -l)
total_files_before_filter=$(grep -v "Generated on" generated/programs-list.txt | wc -l)
filtered_ado_files=$((total_files_before_filter - total_files))
total_windows_paths=$(awk -F, '{sum += $3} END {print sum}' $csv_file)
total_drive_letters=$(awk -F, '{sum += $6} END {print sum}' $csv_file)
total_unix_paths=$(awk -F, '{sum += $4} END {print sum}' $csv_file)
total_mixed_paths=$(awk -F, '{sum += $5} END {print sum}' $csv_file)

# Write summary file
> $summary_file
echo "#### File Paths Summary" > $summary_file
echo "" >> $summary_file
echo "Generated on $(date)" >> $summary_file
echo "" >> $summary_file

if [ $total_windows_paths -gt 0 ]; then
  echo "⚠️ Warning: Some files contain Windows file paths!" >> $summary_file
  echo "This will prevent any user on MacOS or Linux from running the code." >> $summary_file
  echo "We strongly urge you to write all file paths using appropriate functions, or, if the software permits, simply using the '/' separator." >> $summary_file
  echo "" >> $summary_file
else
  echo "✅ All file paths identified are cross-platform compatible." >> $summary_file
  echo "" >> $summary_file
fi

echo "| Total Files | Total Windows Paths | Total Unix Paths | Total Mixed Paths | Total Drive Letters |" >> $summary_file
echo "| --- | --- | --- | --- | --- |" >> $summary_file
echo "| $total_files | $total_windows_paths | $total_unix_paths | $total_mixed_paths | $total_drive_letters |" >> $summary_file

# Count files with issues for verbose output
files_with_windows_paths=$(awk -F, '$3 > 0 {count++} END {print count+0}' $csv_file)
files_with_drive_letters=$(awk -F, '$6 > 0 {count++} END {print count+0}' $csv_file)
files_with_mixed_paths=$(awk -F, '$5 > 0 {count++} END {print count+0}' $csv_file)

# Verbose summary output to command line
echo "========================================"
echo "FILE PATHS CHECK SUMMARY"
echo "========================================"
echo "Directory: $directory"
echo "Tag: ${tag:-"(none)"}"
echo ""
echo "📊 STATISTICS:"
echo "  Total code files found: $total_files_before_filter"
if [ $filtered_ado_files -gt 0 ]; then
  echo "  ADO files filtered out: $filtered_ado_files"
fi
echo "  Code files checked: $total_files"
echo "  Files with Windows paths: $files_with_windows_paths"
echo "  Files with drive letters: $files_with_drive_letters"
echo "  Files with mixed paths: $files_with_mixed_paths"
echo ""
echo "  Total Windows path occurrences: $total_windows_paths"
echo "  Total Unix path occurrences: $total_unix_paths"
echo "  Total drive letter occurrences: $total_drive_letters"
echo ""

if [ $total_windows_paths -gt 0 ]; then
  echo "⚠️  PATH COMPATIBILITY ISSUES DETECTED:"
  if [ $files_with_drive_letters -gt 0 ]; then
    echo "  🚨 $files_with_drive_letters files contain drive letters (C:\, D:\, etc.)"
  fi
  if [ $files_with_windows_paths -gt 0 ]; then
    echo "  ⚠️  $files_with_windows_paths files contain Windows-style paths (backslashes)"
  fi
  if [ $files_with_mixed_paths -gt 0 ]; then
    echo "  🔀 $files_with_mixed_paths files contain mixed path styles"
  fi
  echo ""
  echo "  These paths will prevent the code from running on macOS/Linux systems."
  echo "  Consider using cross-platform path functions or forward slashes."
else
  echo "✅ PATH COMPATIBILITY: All paths are cross-platform compatible"
fi
echo ""

echo "📁 REPORTS GENERATED:"
echo "  Detailed report: $report_file"
echo "  Summary report: $summary_file"
echo "  Raw data (CSV): $csv_file"
echo "========================================"
