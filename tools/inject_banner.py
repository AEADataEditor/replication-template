#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# Adapted from SIVACOR/documentation (https://github.com/SIVACOR/documentation),
# licensed CC-BY-4.0. Not covered by this repository's BSD-3-Clause LICENSE.

"""Bake a dismissable site-wide banner into the built MyST HTML.

The same file is used by AEADataEditor/replication-template-development (tools/inject_banner.py)
and AEADataEditor/editor-scripts (.github/scripts/inject_banner.py); keep the
copies identical.

Why a post-build step: the MyST book-theme exposes no hook for custom ``<head>``
content -- ``template.yml`` offers only ``style`` (a CSS file) and a ``footer``
part -- and a CSS-only banner cannot be dismissed. So the CSS *and* the JS are
inserted here, after ``myst build --html`` and before the site is uploaded.
Everything is inlined at build time; nothing is fetched at runtime.

Usage (from the repository root)::

    python3 <this script> [--config docs/banner.yml] [--html-dir docs/_build/html]
    python3 <this script> --preview "PR #42, commit abc1234, 2026-11-19 03:00 UTC" \\
        --live-url https://aeadataeditor.github.io/<site>/

Without ``--preview``, a missing config, ``enabled: false``, or an empty message
is a no-op with exit status 0, so the docs workflow can call this
unconditionally. Re-running over an already-injected tree is also a no-op.

``--preview`` is for builds published somewhere other than the live site (the
Cloudflare Pages PR previews): it always raises a banner saying so, stamped
with the given text. If the config is enabled as well, the preview note is
prepended to that announcement rather than replacing it. ``--live-url`` adds a
link to the live site to the preview banner (unless the announcement has its
own link).

Config file (optional; YAML)::

    enabled: true
    level: warning          # info | warning | critical (colour scheme)
    message: Plain text, no markup.
    link: ''                # optional call-to-action URL
    link_text: ''
    expires: ''             # optional ISO-8601 with offset; hidden client-side after it
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

MARKER = "aea-banner-style"
HEAD_CLOSE = re.compile(r"</head\s*>", re.IGNORECASE)

# Height of the theme's sticky page header, which the theme itself hardcodes as
# `h-[60px]` plus `style="top:60px"` on the sidebar/outline panels.
HEADER_H = "60px"

# The banner is `position: fixed`, so everything the theme pins to the top of the
# viewport has to move down by its height. These three selectors are the coupling
# to the book-theme's markup; if a theme upgrade renames them the banner still
# shows and stays dismissable, it just overlaps the header again.
#
#   body > div.sticky.top-0          -- the page header
#   .xl\:article-grid.fixed          -- the table-of-contents sidebar
#   .lg\:col-margin-right            -- the in-page outline (top:60px)
#
# The sidebar gets an inline `top` computed by the theme (60px, plus the height
# of the theme's own `banner` part while it is in view), so it is pushed down
# with margin-top rather than by overriding that `top`.
LAYOUT_CSS = f"""
html.aea-banner-open body {{
  padding-top: var(--aea-banner-h, 0px);
}}
html.aea-banner-open body > div.sticky.top-0 {{
  top: var(--aea-banner-h, 0px) !important;
}}
html.aea-banner-open .xl\\:article-grid.fixed {{
  margin-top: var(--aea-banner-h, 0px);
}}
html.aea-banner-open .lg\\:col-margin-right {{
  top: calc({HEADER_H} + var(--aea-banner-h, 0px)) !important;
}}
"""

BANNER_CSS = """
#aea-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.25rem 0.75rem;
  padding: 0.55rem 2.75rem;
  font-size: 0.9rem;
  line-height: 1.4;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}
#aea-banner p {
  margin: 0;
}
#aea-banner a {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
}
#aea-banner button {
  position: absolute;
  top: 50%;
  right: 0.35rem;
  transform: translateY(-50%);
  padding: 0.1rem 0.45rem;
  border: 0;
  border-radius: 4px;
  background: none;
  color: inherit;
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
}
#aea-banner button:hover {
  background: rgba(0, 0, 0, 0.15);
}
#aea-banner button:focus-visible {
  outline: 3px solid currentColor;
  outline-offset: 1px;
}
#aea-banner[data-level="info"] {
  background: #0b5cad;
  color: #fff;
}
#aea-banner[data-level="warning"] {
  background: #ffcc00;
  color: #333;
}
#aea-banner[data-level="critical"] {
  background: #b3261e;
  color: #fff;
}
"""

BANNER_JS = """
(function () {
  var cfg = __CFG__;
  var KEY = "aea:banner-dismissed";

  if (cfg.expires) {
    var deadline = Date.parse(cfg.expires);
    if (!isNaN(deadline) && deadline <= Date.now()) return;
  }
  try {
    if (window.localStorage.getItem(KEY) === cfg.id) return;
  } catch (e) {
    /* storage blocked: show the banner, just do not remember the dismissal */
  }

  var root = document.documentElement;
  var bar = null;
  var pending = false;

  function measure() {
    pending = false;
    root.style.setProperty("--aea-banner-h", bar.offsetHeight + "px");
    root.style.scrollPaddingTop = bar.offsetHeight + __HEADER_H__ + "px";
  }

  function queueMeasure() {
    if (pending) return;
    pending = true;
    window.requestAnimationFrame(measure);
  }

  function dismiss() {
    try {
      window.localStorage.setItem(KEY, cfg.id);
    } catch (e) {
      /* ignore */
    }
    window.removeEventListener("resize", queueMeasure);
    root.classList.remove("aea-banner-open");
    root.style.removeProperty("--aea-banner-h");
    root.style.scrollPaddingTop = __HEADER_H__ + "px";
    if (bar && bar.parentNode) bar.parentNode.removeChild(bar);
  }

  function mount() {
    if (document.getElementById("aea-banner")) return;

    bar = document.createElement("div");
    bar.id = "aea-banner";
    bar.setAttribute("role", "region");
    bar.setAttribute("aria-label", "Site announcement");
    bar.setAttribute("data-level", cfg.level);

    var text = document.createElement("p");
    text.textContent = cfg.message;
    bar.appendChild(text);

    if (cfg.link) {
      var link = document.createElement("a");
      link.href = cfg.link;
      link.textContent = cfg.link_text || "Learn more";
      bar.appendChild(link);
    }

    var close = document.createElement("button");
    close.type = "button";
    close.setAttribute("aria-label", "Dismiss announcement");
    close.textContent = "\\u00d7";
    close.addEventListener("click", dismiss);
    bar.appendChild(close);

    document.body.appendChild(bar);
    root.classList.add("aea-banner-open");
    measure();
    window.addEventListener("resize", queueMeasure);
  }

  // The theme is a hydrated React app that owns `document`, so mount only once
  // hydration is done -- an extra <body> child added earlier would show up in a
  // hydration diff.
  if (document.readyState === "complete") mount();
  else window.addEventListener("load", mount);
})();
"""

LEVELS = ("info", "warning", "critical")

PREVIEW_NOTE = "Preview build ({built_at}) -- this is not the live site."
LIVE_LINK_TEXT = "Go to the live site"


def build_snippet(cfg: dict) -> str:
    """Render the <style> + <script> pair injected into every page's <head>."""
    payload = {
        "id": cfg["id"],
        "level": cfg["level"],
        "message": cfg["message"],
        "link": cfg["link"],
        "link_text": cfg["link_text"],
        "expires": cfg["expires"],
    }
    # `<` escaped so the payload can never terminate the <script> element.
    as_json = json.dumps(payload, sort_keys=True).replace("<", "\\u003c")
    script = BANNER_JS.replace("__CFG__", as_json).replace(
        "__HEADER_H__", HEADER_H.removesuffix("px")
    )
    return (
        f'<style id="{MARKER}">{LAYOUT_CSS}{BANNER_CSS}</style>'
        f"<script>{script}</script>"
    )


def with_id(cfg: dict) -> dict:
    """Attach the dismissal key, derived from the content.

    A *new* announcement therefore reappears for readers who dismissed the
    previous one; a preview note carries its build stamp, so every fresh preview
    shows it again.
    """
    digest = hashlib.sha256(
        "\x1f".join([cfg["level"], cfg["message"], cfg["link"], cfg["link_text"]]).encode()
    ).hexdigest()[:12]
    return {**cfg, "id": digest}


def preview_config(built_at: str, announcement: dict | None, live_url: str = "") -> dict:
    """Banner for a preview deploy: the preview note, merged with any announcement."""
    note = PREVIEW_NOTE.format(built_at=built_at.strip())
    live_url = live_url.strip()
    if announcement is None:
        return with_id(
            {
                "level": "info",
                "message": note,
                "link": live_url,
                "link_text": LIVE_LINK_TEXT if live_url else "",
                "expires": "",
            }
        )
    merged = {**announcement, "message": f"{note} {announcement['message']}"}
    if live_url and not merged["link"]:
        merged["link"], merged["link_text"] = live_url, LIVE_LINK_TEXT
    # A preview note is never allowed to expire with the announcement.
    merged["expires"] = ""
    return with_id(merged)


def load_config(path: Path) -> dict | None:
    """Return the normalized banner config, or None if no banner should show."""
    if not path.exists():
        print(f"{path} not found; no announcement banner.")
        return None

    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        sys.exit(f"{path}: expected a mapping, got {type(raw).__name__}")

    if not raw.get("enabled"):
        print(f"{path}: enabled is false; no announcement banner.")
        return None

    message = str(raw.get("message") or "").strip()
    if not message:
        print(f"{path}: enabled but message is empty; no announcement banner.")
        return None

    level = str(raw.get("level") or "warning").strip()
    if level not in LEVELS:
        sys.exit(f"{path}: level must be one of {', '.join(LEVELS)}, got {level!r}")

    cfg = {
        "level": level,
        "message": message,
        "link": str(raw.get("link") or "").strip(),
        "link_text": str(raw.get("link_text") or "").strip(),
        "expires": str(raw.get("expires") or "").strip(),
    }
    return with_id(cfg)


def inject(html_dir: Path, snippet: str, marker: str = MARKER) -> int:
    """Insert ``snippet`` before ``</head>`` of every page not already carrying ``marker``."""
    pages = sorted(html_dir.rglob("*.html"))
    if not pages:
        sys.exit(f"{html_dir}: no HTML files found -- was the site built?")

    touched = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if marker in text:
            continue
        # Callable replacement: the snippet contains backslash escapes that
        # re would otherwise try to interpret as template references.
        new_text, count = HEAD_CLOSE.subn(
            lambda match: snippet + match.group(0), text, count=1
        )
        if not count:
            print(f"  skipped (no </head>): {page.relative_to(html_dir)}")
            continue
        page.write_text(new_text, encoding="utf-8")
        touched += 1
    return touched


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=Path("docs/banner.yml"))
    parser.add_argument("--html-dir", type=Path, default=Path("docs/_build/html"))
    parser.add_argument(
        "--preview",
        metavar="BUILT_AT",
        help="always inject a 'preview build' banner stamped with this text, "
        "merged with the config's announcement if that is enabled",
    )
    parser.add_argument(
        "--live-url",
        default="",
        help="with --preview: link the banner to the live site",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    if args.preview:
        cfg = preview_config(args.preview, cfg, args.live_url)
    if cfg is None:
        return

    touched = inject(args.html_dir, build_snippet(cfg))
    print(
        f"Injected {cfg['level']} banner (id {cfg['id']}) into {touched} page(s) "
        f"under {args.html_dir}: {cfg['message']}"
    )


if __name__ == "__main__":
    main()
