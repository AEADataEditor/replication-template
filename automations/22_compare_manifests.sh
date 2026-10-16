#!/bin/bash

# Script to compare current manifest with the most recent previous manifest
# Usage: 08_compare_manifests.sh [project_id]

#set -e

[[ "$SkipProcessing" == "yes" ]] && exit 0

PROJECT_ID="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GENERATED_DIR="$REPO_ROOT/generated"

# Ensure generated directory exists
mkdir -p "$GENERATED_DIR"

# Function to find manifest files
find_manifest_files() {
    # Look for manifest files with SHA256 in the name, sorted by modification time (newest first)
    find "$REPO_ROOT" -name "*manifest*sha256*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | cut -d' ' -f2-
}

echo "🔍 Searching for manifest files to compare..."

# Find all manifest files
manifest_files=($(find_manifest_files))

if [ ${#manifest_files[@]} -lt 2 ]; then
    echo "ℹ️  Found ${#manifest_files[@]} manifest file(s). Need at least 2 files to compare."
    if [ ${#manifest_files[@]} -eq 1 ]; then
        echo "   Current manifest: ${manifest_files[0]}"
    fi
    echo "   Creating placeholder report indicating no comparison available."
    
    # Create placeholder report
    cat > "$GENERATED_DIR/manifest-comparison.md" << EOF
No previous manifest found for comparison.

This is likely the first run of the manifest creation process for this repository.
EOF
    exit 0
fi

# Get the two most recent manifest files
current_manifest="${manifest_files[0]}"
previous_manifest="${manifest_files[1]}"

echo "📋 Found manifest files for comparison:"
echo "   Current:  $(basename "$current_manifest")"
echo "   Previous: $(basename "$previous_manifest")"

# Extract dates from filenames or use file modification time
current_date=$(basename "$current_manifest" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || date -r "$current_manifest" +%Y-%m-%d)
previous_date=$(basename "$previous_manifest" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || date -r "$previous_manifest" +%Y-%m-%d)

echo "   Current date:  $current_date"
echo "   Previous date: $previous_date"

# Generate comparison report
report_file="$GENERATED_DIR/manifest-comparison.md"
summary_file="$GENERATED_DIR/manifest-cmp-summary.md"

echo "📊 Generating comparison report..."

# Create markdown report header
cat > "$report_file" << EOF

- **Generated:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')  
- **Previous Manifest:** \`$(basename "$previous_manifest")\`  
- **Current Manifest:** \`$(basename "$current_manifest")\`  

This report compares the current manifest with the most recent previous manifest to identify changes in the repository contents.

EOF

# Run the comparison and append to the report
echo "🔄 Running manifest comparison..."
cd "$REPO_ROOT"

# Capture the comparison output and format for markdown
if python3 "$REPO_ROOT/tools/compare_manifests.py" "$previous_manifest" "$current_manifest" --summary-file "$summary_file" >> "$report_file" 2>&1; then
    echo "✅ Comparison completed successfully!"
else
    echo "⚠️  Comparison encountered issues, but report was generated."
fi

echo "   Report location: $report_file"
echo "   Summary location: $summary_file"
echo "🎉 Manifest comparison automation completed!"