#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024-2025 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

#set -ev
if [ ! -d generated ] 
then 
  mkdir generated
fi

if [ ! -f generated/README.txt ]
then
    echo "This directory contains information generated automatically" > generated/README.txt
    echo "-- Do not modify --" >> generated/README.txt
fi
ls -lR
