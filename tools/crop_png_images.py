#!/usr/bin/env python3
"""
Crop all PNG files in the current directory to their closest bounding box.
"""

from PIL import Image
import os
import glob

def get_bbox(image):
    """
    Get the bounding box of non-white/non-transparent content.
    """
    # Convert to RGBA if not already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Get the bounding box
    bbox = image.getbbox()
    return bbox

def crop_image(input_path):
    """
    Crop a single image to its bounding box and save it.
    """
    try:
        img = Image.open(input_path)

        # Get bounding box
        bbox = get_bbox(img)

        if bbox:
            # Crop to bounding box
            cropped = img.crop(bbox)

            # Save back to the same file
            cropped.save(input_path)

            original_size = img.size
            new_size = cropped.size

            print(f"✓ {os.path.basename(input_path)}: {original_size} → {new_size}")
            return True
        else:
            print(f"✗ {os.path.basename(input_path)}: Empty image, skipped")
            return False

    except Exception as e:
        print(f"✗ {os.path.basename(input_path)}: Error - {e}")
        return False

def main():
    # Get all PNG files in current directory
    png_files = sorted(glob.glob("*.png"))

    if not png_files:
        print("No PNG files found in current directory")
        return

    print(f"Found {len(png_files)} PNG files")
    print("-" * 60)

    success_count = 0
    for png_file in png_files:
        if crop_image(png_file):
            success_count += 1

    print("-" * 60)
    print(f"Successfully cropped {success_count}/{len(png_files)} images")

if __name__ == "__main__":
    main()
