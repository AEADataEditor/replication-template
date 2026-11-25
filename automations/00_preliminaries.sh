#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

if [ "$1" == "no" ]; then exit 0; fi

# Define the $pythonbin variable based on the operating system using a case statement
case "$(uname -o)" in
  Msys)
    pythonbin="python"
    ;;
  *)
    pythonbin="python3"
    ;;
esac

projectID=$2

if [ -d cache ]; then ls -lR cache/*; fi
if [ -f cache/$projectID.zip ]; then mv cache/$projectID.zip .; fi
