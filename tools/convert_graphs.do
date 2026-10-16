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
