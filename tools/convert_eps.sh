#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024-2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

#
# Convert EPS (Encapsulated PostScript) files to PNG format
#
# This script recursively searches for all .eps files in the current directory
# and its subdirectories, then converts them to PNG format using ImageMagick's
# convert utility. This is commonly needed for replication packages where
# statistical software (like Stata, R, or MATLAB) generates EPS graphics that
# need to be converted to more web-friendly PNG format for reports or documentation.
#
# Usage:
#   ./convert_eps.sh
#   bash tools/convert_eps.sh
#
# Requirements:
#   - ImageMagick (convert command) must be installed
#   - Read/write permissions in current directory and subdirectories
#
# Behavior:
#   - Searches recursively from current directory (.)
#   - Finds all files with .eps extension
#   - Converts each .eps file to .png with same base filename
#   - Original .eps files are preserved (not deleted)
#   - Exits with error code 2 if convert utility is not found
#
# Examples:
#   Input:  ./figures/graph1.eps
#   Output: ./figures/graph1.png
#
#   Input:  ./output/results/scatter.eps  
#   Output: ./output/results/scatter.png
#
# Error Handling:
#   - Checks if 'convert' command is available before processing
#   - Exits with code 2 if ImageMagick is not installed
#   - Individual file conversion errors are handled by convert utility
#
# Dependencies:
#   ImageMagick package:
#   - Ubuntu/Debian: sudo apt-get install imagemagick
#   - CentOS/RHEL: sudo yum install ImageMagick
#   - macOS: brew install imagemagick
#
# Note: This script is typically used in replication workflows where
# statistical software generates EPS graphics that need to be converted
# for inclusion in web-based reports or documentation.
#

# check for convert

convert=$(which convert)
case $? in
	0)
		echo "convert found at $convert"
		;;
	*)
		echo "No convert found ... exiting"
		exit 2
		;;
esac

for file in $(find . -name \*.eps); do
    $convert "$file" "${file%.eps}.png"
done

