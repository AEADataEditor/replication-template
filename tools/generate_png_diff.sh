#!/bin/bash

# generate_png_diff.sh - Generate visual diffs for modified PNG images
#
# DESCRIPTION:
#   This script compares PNG images in the git repository that have been modified
#   against their original versions (from HEAD). It generates visual difference
#   images and calculates Mean Absolute Error (MAE) statistics for each comparison.
#
# USAGE:
#   ./generate_png_diff.sh [modified_dir]
#
# PARAMETERS:
#   modified_dir  - Directory containing the modified images (optional)
#                   Default: "209827/local/LocalOutputs"
#
# OUTPUT FILES:
#   - {modified_dir}/diffs/diff_{image_name}.png - Visual diff images
#   - generated/image_diff_stats.txt - Summary statistics file
#   - generated/image_diff_stats.txt.raw - Detailed comparison output
#
# DEPENDENCIES:
#   - ImageMagick (magick command with composite and compare tools)
#   - Git (for retrieving original images and detecting changes)
#
# EXAMPLE:
#   ./generate_png_diff.sh
#   ./generate_png_diff.sh "custom/output/directory"

# Directory containing the modified images (live directory)
modified_dir="${1:-209827/local/LocalOutputs}"
# Directory to save the diff images
diff_dir="$modified_dir/diffs"
diff_stats="generated/image_diff_stats.txt"

# Create the diff directory if it doesn't exist
mkdir -p "$diff_dir"

# Get the list of modified PNG files from git
images=$(git diff --name-only HEAD | grep '\.png$')

# Exit if no images are found
if [ -z "$images" ]; then
    echo "No modified PNG images found."
    exit 0
fi

# Initialize the statistics files with timestamps
echo "Generated on $(date)" > "$diff_stats"
echo "Generated on $(date)" > "$diff_stats".raw

# Process each modified PNG image
for image in $images; do
    # Extract the original image from git HEAD into a temporary file
    original_image_path=$(mktemp)
    git show HEAD:"$image" > "$original_image_path"

    # Define paths for the modified image and output diff image
    modified_image="$modified_dir/$(basename "$image")"
    diff_image="$diff_dir/diff_$(basename "$image")"

    # Verify both images exist before processing
    if [[ -f "$original_image_path" && -f "$modified_image" ]]; then
        # Generate visual difference image using ImageMagick composite
        magick composite "$original_image_path" "$modified_image" -compose difference "$diff_image"
        
        # Calculate Mean Absolute Error (MAE) statistics
        compare_output=$(magick compare "$original_image_path" "$modified_image" -verbose -metric MAE null: 2>&1)
        
        # Log detailed comparison output
        echo "$modified_image --> " >> "${diff_stats}.raw"
        echo "$compare_output"      >> "${diff_stats}.raw"
        
        # Extract the overall MAE statistic and write to summary file
        all_stat=$(echo "$compare_output" | grep "all:" | awk '{print $3}' | tr -d '()')
        if [ -n "$all_stat" ]; then
            echo "$(basename "$image"): $all_stat" >> "$diff_stats"
        else
            echo "$(basename "$image")): No difference detected" >> "$diff_stats"
        fi
        
        echo "Diff generated for $(basename "$image")"
    else
        echo "One of the images ($(basename "$image")) is missing."
    fi

    # Clean up the temporary original image file
    rm "$original_image_path"
done