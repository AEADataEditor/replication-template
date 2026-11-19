#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# Export the identifier variable that matches a deposit directory name.
#
# Source this file from the repository root with the directory name as argument:
#   . ./tools/set_id_from_dirname.sh "$newName"
#
# The directory-name prefix says which repository the deposit came from:
#   dv-DVN-ABC123 -> DataverseID (whole name)
#   zenodo-12345  -> ZenodoID    (prefix stripped)
#   osf-abcde     -> OSFID       (prefix stripped)
#   wb-400        -> WorldBankID (prefix stripped)
#   anything else -> openICPSRID (whole name)
# Feed the result to ./tools/update_config.sh.

_sid_name="${1:?directory name required}"
case "$_sid_name" in
    dv-*)     export DataverseID="$_sid_name" ;;
    zenodo-*) export ZenodoID="${_sid_name#zenodo-}" ;;
    osf-*)    export OSFID="${_sid_name#osf-}" ;;
    wb-*)     export WorldBankID="${_sid_name#wb-}" ;;
    *)        export openICPSRID="$_sid_name" ;;
esac
unset _sid_name
