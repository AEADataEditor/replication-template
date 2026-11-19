#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# Post-process the MyST HTML build before it is published:
#  - add noindex/noai robots meta and a link to AGENTS.md to every page
#    (MyST has no option for extra <head> tags). They go at the end of
#    <head>: React hydrates the whole document, and tags inserted before the
#    theme's own make it re-render the page, dropping other injected markup.
#  - replace the CURRENTYEAR placeholder (copyright line in
#    _parts/sidebar-footer.md) with the build year, in both the HTML and the
#    JSON page data, so that server and client render the same text,
#  - publish docs/AGENTS.public.md as AGENTS.md at the site root,
#  - replace MyST's permissive robots.txt.
# Usage: BASE_URL=/site-path bash docs/_postbuild.sh docs/_build/html
set -euo pipefail

html="${1:?usage: $0 <html build dir>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base="${BASE_URL:-}"
marker='<meta name="robots" content="noindex'
tags='<meta name="robots" content="noindex, nofollow, noarchive, noai, noimageai"/><link rel="help" type="text/markdown" href="'"$base"'/AGENTS.md" title="Notice to AI agents and LLMs"/>'

find "$html" -name '*.html' -print0 | while IFS= read -r -d '' f; do
  grep -q "$marker" "$f" || sed -i "s|</head>|$tags</head>|" "$f"
done

find "$html" \( -name '*.html' -o -name '*.json' \) -print0 \
  | { xargs -0 grep -lZ CURRENTYEAR || true; } \
  | xargs -0 -r sed -i "s/CURRENTYEAR/$(date -u +%Y)/g"

cp "$here/AGENTS.public.md" "$html/AGENTS.md"

cat > "$html/robots.txt" <<'ROBOTS'
# Internal documentation of the AEA Data Editor. Do not index or crawl.
# See AGENTS.md for guidance to AI agents.
User-agent: *
Disallow: /
ROBOTS
