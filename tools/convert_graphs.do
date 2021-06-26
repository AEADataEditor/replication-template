/* convert graphs */

include "config.do"

cd "$rootdir"

local files : dir "$rootdir" files "*.gph"
local files: subinstr local files ".gph" "", all

foreach fig in `files' {
    graph use `fig'
    graph export `fig'.pdf, replace
}
