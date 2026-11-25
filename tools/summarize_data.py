# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

import csv
from collections import defaultdict

# Define the path to the CSV file
csv_file_path = './generated/data-metadata.csv'

# Initialize a dictionary to store the total bytes for each highest directory level
directory_bytes = defaultdict(int)

# Read the CSV file
with open(csv_file_path, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        # Extract the lowest directory level from the filename
        lowest_directory = row['filename'].split('/')[-2]
        # Add the bytes to the corresponding directory
        directory_bytes[lowest_directory] += int(row['bytes']) / (1024 * 1024)

# Print the summary
print("Summary of data by highest directory level:")
for directory, total_megabytes in directory_bytes.items():
    print(f"{directory}: {total_megabytes:.2f} MB")