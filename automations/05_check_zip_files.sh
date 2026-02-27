#!/bin/bash
#set -ev

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)]

where (directory) could be the openICPSR ID, Zenodo ID, etc.
EOF
exit 2
fi
directory=$1
tag=$2

if [ ! -d generated ] 
then 
  mkdir generated
fi

# Include tag in filename if it exists
suffix=""
[ -z $tag ] || suffix="$suffix.$tag"

warning_file=$(pwd)/generated/zip-warning$suffix.md

if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory
  
  # Check if there are any zip files in the manifest or if zipfile was extracted
  zip_files_found=false
  zipfile_extracted=false
  
  # Check for zip files in current directory
  if find . -maxdepth 1 -type f \( -name "*.zip" -o -exec sh -c 'file -b --mime-type "$1" | grep -q "application/zip"' _ {} \; \) | grep -q .; then
    zip_files_found=true
  fi
  
  # Check if .zipfile_info exists (indicates zipfile was extracted)
  if [ -f ".zipfile_info" ]; then
    zipfile_extracted=true
  fi
  
  # Check for zip files in any subdirectories (in case they were extracted)
  if find . -type f \( -name "*.zip" -o -exec sh -c 'file -b --mime-type "$1" | grep -q "application/zip"' _ {} \; \) | grep -q .; then
    zip_files_found=true
  fi
  
  # Generate warning if zip files found or were extracted
  if [ "$zip_files_found" = true ] || [ "$zipfile_extracted" = true ]; then
    cat > "$warning_file" << 'EOF'
⚠️ ZIP Files Detected

**Warning:** This deposit contains ZIP files or ZIP files were extracted during processing.


**Files detected:**

EOF
    
    # List ZIP files found
    if [ "$zip_files_found" = true ]; then
      echo "" >> "$warning_file"
      find . -type f \( -name "*.zip" -o -exec sh -c 'file -b --mime-type "$1" | grep -q "application/zip"' _ {} \; \) | sed 's|^\./|* |' >> "$warning_file"
    fi
    
    # Show extracted ZIP info if available
    if [ "$zipfile_extracted" = true ]; then
      echo "" >> "$warning_file"
      echo "**Extracted ZIP files**" >> "$warning_file"
      echo "" >> "$warning_file"
      if [ -f ".zipfile_info" ]; then
        # Extract the ZIPFILE_SUFFIX value
        zipfile_suffix=$(grep "export ZIPFILE_SUFFIX=" .zipfile_info | cut -d'"' -f2)
        echo "* Extracted: $zipfile_suffix" >> "$warning_file"
        
        # List directories that match the extracted names
        IFS=',' read -ra ADDR <<< "$zipfile_suffix"
        for i in "${ADDR[@]}"; do
          if [ -d "$i" ]; then
            echo "* Directory created: $i/" >> "$warning_file"
          fi
        done
      fi
    fi
    
    echo "" >> "$warning_file"
    echo "*Generated on $(date)*" >> "$warning_file"
    
    echo "Warning generated: $warning_file"
  else
    # No ZIP files found, create empty warning file or remove existing one
    echo "**No ZIP Files Detected on $(date)**" >> "$warning_file"
    
    echo "No ZIP files detected. Clean deposit confirmed: $warning_file"
  fi
fi