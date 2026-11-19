* SPDX-License-Identifier: BSD-3-Clause
* Copyright (c) 2020-2023 Lars Vilhuber and contributors.
* Author(s): Lars Vilhuber
* Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

/* convert graphs */
/* simply copy this program into the folder
   with GPH files, and run it (command line/
   right-click mode) */

global rootdir "."

cd "$rootdir"

local files : dir "$rootdir" files "*.gph"
local files: subinstr local files ".gph" "", all

foreach fig in `files' {
    graph use `fig'
    graph export `fig'.pdf, replace
    graph export `fig'.png, replace
}
