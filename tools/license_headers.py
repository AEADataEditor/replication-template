#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

"""Add or verify license/copyright/author headers on the repository's scripts.

Each script written in this repository starts (after any shebang, encoding, or
Stata ``*!`` version line) with a header in its language's comment syntax:

    # SPDX-License-Identifier: BSD-3-Clause
    # Copyright (c) 2019-2026 Lars Vilhuber and contributors.
    # Author(s): Lars Vilhuber, Jane Doe
    # Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

Copyright years and authors come from ``git log --follow`` (bots excluded,
identities mapped through ``aliases``, commits listed in ``ignore_commits``
skipped), plus any legacy ``Author:`` line already in the file.

Configuration lives in ``.license-headers.json`` at the repository root:
``holder``, ``include``/``exclude`` (path prefixes), ``aliases`` (git email or
name -> display name), ``bots`` (regexes on "name <email>"), ``ignore_commits``,
``default_author``. Files whose header declares a different SPDX license
(ingested code) are left alone.

Usage:
    python3 <this script>            # add missing headers
    python3 <this script> --refresh  # also recompute existing BSD headers
    python3 <this script> --check    # exit 1 if a script lacks a complete header
    python3 <this script> --list     # print file, years, authors
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

SPDX = "SPDX-License-Identifier: BSD-3-Clause"
LICENSED = "Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root."
CONFIG = ".license-headers.json"
HEAD_LINES = 25  # header must appear within this many lines

# extension -> (line prefix, line suffix)
STYLES = {
    ".sh": ("# ", ""), ".bash": ("# ", ""), ".py": ("# ", ""), ".R": ("# ", ""),
    ".r": ("# ", ""), ".jl": ("# ", ""), ".ps1": ("# ", ""), ".pl": ("# ", ""),
    ".rb": ("# ", ""), ".do": ("* ", ""), ".ado": ("* ", ""), ".m": ("% ", ""),
    ".js": ("// ", ""), ".ts": ("// ", ""), ".sas": ("/* ", " */"),
}

# Header lines written by earlier versions (#161) or by hand, removed on (re)write.
LEGACY = [
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*SPDX-License-Identifier:\s*BSD-3-Clause\s*(\*/)?\s*$"),
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*Copyright \(c\) .*Lars Vilhuber.*$"),
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*Licensed under the BSD 3-Clause License.*$"),
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*Licensed under BSD-3 license\s*$", re.I),
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*\(C\)\s*\d{4}\s*$", re.I),
    re.compile(r"^\s*(#|\*|%|//|/\*)\s*Author\(s\):.*$"),
]
LEGACY_AUTHOR = re.compile(r"^\s*(?:#|\*|%|//)\s*Author:\s*(.+?)\s*$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def load_config(root):
    with open(os.path.join(root, CONFIG), encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg.setdefault("include", [""])
    cfg.setdefault("exclude", [])
    cfg.setdefault("aliases", {})
    cfg.setdefault("bots", [])
    cfg.setdefault("ignore_commits", [])
    cfg.setdefault("default_author", "")
    return cfg


def style_for(path):
    """Comment style for a script, or None if it is not a script."""
    ext = os.path.splitext(path)[1]
    if ext in STYLES:
        return STYLES[ext]
    if ext == "" and os.path.isfile(path):
        with open(path, "rb") as fh:
            first = fh.readline()
        if re.match(rb"^#!.*\b(ba|z|k|da)?sh\b", first) or re.match(rb"^#!.*python", first):
            return ("# ", "")
    return None


def selected(path, cfg):
    def hit(prefixes):
        return any(path == p or path.startswith(p) if p else True for p in prefixes)
    return hit(cfg["include"]) and not any(path == p or path.startswith(p) for p in cfg["exclude"])


def scripts(cfg):
    for path in git("ls-files").splitlines():
        if selected(path, cfg) and os.path.isfile(path) and style_for(path):
            yield path


def canonical(name, email, cfg):
    who = f"{name} <{email}>"
    if any(re.search(rx, who) for rx in cfg["bots"]):
        return None
    return cfg["aliases"].get(email) or cfg["aliases"].get(name) or name


def history(path, cfg):
    """(years, authors in order of first commit) from git history."""
    out = git("log", "--follow", "--no-merges", "--format=%H|%an|%ae|%ad",
              "--date=format:%Y", "--", path)
    ignore = tuple(cfg["ignore_commits"])
    years, authors = [], []
    for line in reversed(out.splitlines()):
        sha, name, email, year = line.split("|", 3)
        if ignore and sha.startswith(ignore):
            continue
        years.append(int(year))
        who = canonical(name, email, cfg)
        if who and who not in authors:
            authors.append(who)
    return years, authors


def year_span(years):
    if not years:
        years = [datetime.date.today().year]
    lo, hi = min(years), max(years)
    return str(lo) if lo == hi else f"{lo}-{hi}"


def split_lines(text):
    lines = text.splitlines(keepends=True)
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    return lines, eol


def insert_at(lines, path):
    """Index after shebang / encoding / Stata version lines."""
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if i < len(lines) and re.match(r"^#.*coding[:=]", lines[i]):
        i += 1
    if path.endswith((".ado", ".do")):
        while i < len(lines) and lines[i].startswith("*!"):
            i += 1
    return i


COMMENT = r"^\s*(?:#|\*|%|//|/\*)\s*"


def foreign_spdx(text):
    m = re.search(COMMENT + r"SPDX-License-Identifier:\s*(\S+)",
                  "\n".join(text.splitlines()[:HEAD_LINES]), re.M)
    return bool(m) and m.group(1) != "BSD-3-Clause"


def has_complete_header(text):
    """True if the leading lines hold the SPDX, copyright, and author comments."""
    head = text.splitlines()[:HEAD_LINES]
    return (any(re.match(COMMENT + re.escape(SPDX), l) for l in head)
            and any(re.match(COMMENT + r"Copyright \(c\) \d{4}", l) for l in head)
            and any(re.match(COMMENT + r"Author\(s\): \S", l) for l in head))


def build_header(path, cfg, legacy_authors):
    years, authors = history(path, cfg)
    for a in reversed(legacy_authors):
        a = cfg["aliases"].get(a, a)
        if a in authors:
            authors.remove(a)
        authors.insert(0, a)
    if not authors and cfg["default_author"]:
        authors = [cfg["default_author"]]
    pre, suf = style_for(path)
    body = [SPDX,
            f"Copyright (c) {year_span(years)} {cfg['holder']}.",
            "Author(s): " + ", ".join(authors),
            LICENSED]
    return [pre + b + suf for b in body], years, authors


def rewrite(path, cfg):
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    lines, eol = split_lines(text)
    i = insert_at(lines, path)
    # Drop any legacy header lines in the leading comment block, keeping authors.
    legacy_authors, j = [], i
    kept_prefix = lines[:i]
    rest = lines[i:]
    k = 0
    while k < len(rest) and k < 8:
        s = rest[k].rstrip("\r\n")
        m = LEGACY_AUTHOR.match(s)
        if m:
            legacy_authors.append(m.group(1))
            k += 1
        elif any(rx.match(s) for rx in LEGACY):
            k += 1
        elif k and re.match(r"^\s*(#|\*|%|//)\s*$", s):
            k += 1  # bare comment line that closed the old header
        else:
            break
    if k and k < len(rest) and not rest[k].strip():
        k += 1  # blank line that followed the old header
    rest = rest[k:]
    header, _, _ = build_header(path, cfg, legacy_authors)
    new = kept_prefix + [h + eol for h in header]
    if rest and rest[0].strip():
        new.append(eol)
    new += rest
    out = "".join(new)
    if out != text:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="fail if a script lacks a complete header")
    g.add_argument("--refresh", action="store_true", help="recompute existing BSD headers too")
    g.add_argument("--list", action="store_true", help="print each script's years and authors")
    args = ap.parse_args(argv)

    root = git("rev-parse", "--show-toplevel").strip()
    os.chdir(root)
    cfg = load_config(root)
    bad, changed = [], 0
    for path in scripts(cfg):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        if foreign_spdx(text):
            continue  # ingested code under its upstream license
        if args.list:
            years, authors = history(path, cfg)
            print(f"{path}\t{year_span(years)}\t{', '.join(authors)}")
        elif args.check:
            if not has_complete_header(text):
                bad.append(path)
        elif args.refresh or not has_complete_header(text):
            if rewrite(path, cfg):
                changed += 1
                print("updated:", path)
    if args.check:
        for p in bad:
            print(f"missing or incomplete license header: {p}", file=sys.stderr)
        if bad:
            print(f"Run: python3 {os.path.relpath(__file__, root)}", file=sys.stderr)
        return 1 if bad else 0
    if not args.list:
        print(f"{changed} files updated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
