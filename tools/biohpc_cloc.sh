#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024-2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

if [[ -z $1 ]]
then
    echo "Usage: $0 <project_dir> <suffix>"
    exit 1
fi

docker=$(which docker1)
[ -z $docker ] && docker=$(which docker)
if [[ -z $docker ]]
then
    echo "Docker not found"
    exit 1
fi



clocimg=aldanial/cloc
docker=docker1
$docker run --rm -v $(pwd):/tmp \
   --entrypoint=/bin/bash $clocimg  \
   ./automations/05_count_lines.sh $@

