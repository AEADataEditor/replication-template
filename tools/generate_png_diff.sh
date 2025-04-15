#!/bin/bash

# Directory containing the modified images (live directory)
modified_dir="${1:-209827/local/LocalOutputs}"
# Directory to save the diff images
diff_dir="$modified_dir/diffs"
diff_stats="generated/image_diff_stats.txt"

# Create the diff directory if it doesn't exist
mkdir -p "$diff_dir"

# Get the list of modified PNG files
images=$(git diff --name-only HEAD | grep '\.png$')

# Exit if no images are found
if [ -z "$images" ]; then
    echo "No modified PNG images found."
    exit 0
fi

# Initialize the diff_stats file with the current date
echo "Generated on $(date)" > "$diff_stats"
echo "Generated on $(date)" > "$diff_stats".raw

# Loop through each image and generate the diff
for image in $images; do
    # Extract the original image from the git cache
    original_image_path=$(mktemp)
    git show HEAD:"$image" > "$original_image_path"

    modified_image="$modified_dir/$(basename "$image")"
    diff_image="$diff_dir/diff_$(basename "$image")"

    if [[ -f "$original_image_path" && -f "$modified_image" ]]; then
        magick composite "$original_image_path" "$modified_image" -compose difference "$diff_image"
        compare_output=$(magick compare "$original_image_path" "$modified_image" -verbose -metric MAE null: 2>&1)
        echo "$modified_image --> " >> "${diff_stats}.raw"
        echo "$compare_output"      >> "${diff_stats}.raw"
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