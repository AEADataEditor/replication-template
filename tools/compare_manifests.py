#!/usr/bin/env python3
"""
Compare two SHA256 manifests (previous vs. current) and report what changed
in a meaningful way.

Each file in the current manifest falls into exactly one category:

- unchanged:         same path, same checksum
- content changed:   same path, different checksum
- renamed:           same checksum, different file name (possibly also in a
                     different directory)
- moved:             same checksum and file name, different directory. Not a
                     substantive change; reported grouped by directory.
- moved and changed: path gone, and a file with the same (unique) name
                     appears elsewhere with a different checksum
- added / removed:   everything else

Usage: python compare_manifests.py <previous> <current> [--summary-file FILE]

The detailed report (Markdown) goes to stdout; --summary-file also writes a
short summary.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import PurePosixPath

# Maximum entries per category in the short summary.
SUMMARY_LIMIT = 25


def normalize(path):
    """Strip a leading './' so './a/b' and 'a/b' compare equal."""
    return path[2:] if path.startswith("./") else path


def parse_manifest(filepath):
    """Return {path: checksum} from a sha256sum-style manifest."""
    entries = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                print(f"Warning: skipping malformed line {line_num} in {filepath}: {line}",
                      file=sys.stderr)
                continue
            checksum, filename = parts
            if filename.startswith("*"):  # binary-mode marker
                filename = filename[1:]
            entries[normalize(filename)] = checksum.lower()
    return entries


def _name(path):
    return PurePosixPath(path).name


def _parent(path):
    parent = str(PurePosixPath(path).parent)
    return "." if parent in ("", ".") else parent


def compare(old, new):
    """Classify differences between two {path: checksum} dicts."""
    result = {
        "n_old": len(old), "n_new": len(new),
        "unchanged": 0, "content_changed": [], "renamed": [], "moved": [],
        "moved_changed": [], "added": [], "removed": [],
    }

    common = old.keys() & new.keys()
    for path in sorted(common):
        if old[path] == new[path]:
            result["unchanged"] += 1
        else:
            result["content_changed"].append(path)

    removed = sorted(old.keys() - common)
    added = sorted(new.keys() - common)

    # Pair removed and added paths that carry identical content.
    removed_by_sum = defaultdict(list)
    for path in removed:
        removed_by_sum[old[path]].append(path)
    added_by_sum = defaultdict(list)
    for path in added:
        added_by_sum[new[path]].append(path)

    paired_old, paired_new = set(), set()
    for checksum in sorted(removed_by_sum.keys() & added_by_sum.keys()):
        olds, news = list(removed_by_sum[checksum]), list(added_by_sum[checksum])
        # Prefer pairs that keep the file name (moves), then pair the rest (renames).
        for o in list(olds):
            match = next((n for n in news if _name(n) == _name(o)), None)
            if match:
                result["moved"].append((o, match))
                olds.remove(o)
                news.remove(match)
        for o, n in zip(olds, news):
            result["renamed"].append((o, n))
    for o, n in result["moved"] + result["renamed"]:
        paired_old.add(o)
        paired_new.add(n)

    rest_old = [p for p in removed if p not in paired_old]
    rest_new = [p for p in added if p not in paired_new]

    # Same file name, unique on both sides, different content: moved and changed.
    old_names = defaultdict(list)
    for p in rest_old:
        old_names[_name(p)].append(p)
    new_names = defaultdict(list)
    for p in rest_new:
        new_names[_name(p)].append(p)
    for name in sorted(old_names.keys() & new_names.keys()):
        if len(old_names[name]) == 1 and len(new_names[name]) == 1:
            o, n = old_names[name][0], new_names[name][0]
            result["moved_changed"].append((o, n))
            rest_old.remove(o)
            rest_new.remove(n)

    # Added files whose content already existed elsewhere are copies.
    old_by_sum = defaultdict(list)
    for path, checksum in old.items():
        old_by_sum[checksum].append(path)
    result["added"] = [(p, sorted(old_by_sum.get(new[p], []))[:1]) for p in rest_new]
    result["removed"] = rest_old
    result["old_dirs"] = _all_dirs(old)
    result["new_dirs"] = _all_dirs(new)

    result["renamed"].sort()
    result["moved"].sort()
    result["moved_changed"].sort()
    return result


def _all_dirs(paths):
    """Every directory (and ancestor) that contains at least one file."""
    dirs = set()
    for p in paths:
        dirs.update(str(a) for a in PurePosixPath(p).parents if str(a) != ".")
    return dirs


def roll_up(paths, dirs_on_other_side):
    """Group paths under the highest ancestor directory that does not exist on
    the other side (a wholly new or wholly removed directory).

    Returns (groups, singles): groups is a sorted list of (directory, count)
    for directories holding 2+ such files; singles are the remaining paths.
    """
    by_dir = defaultdict(list)
    singles = []
    for p in paths:
        top = next((str(a) for a in reversed(PurePosixPath(p).parents)
                    if str(a) != "." and str(a) not in dirs_on_other_side), None)
        if top is None:
            singles.append(p)
        else:
            by_dir[top].append(p)
    groups = []
    for d, members in sorted(by_dir.items()):
        if len(members) > 1:
            groups.append((d, len(members)))
        else:
            singles.extend(members)
    return groups, sorted(singles)


def group_moves(moves):
    """Group (old, new) moves by (old directory, new directory)."""
    groups = defaultdict(int)
    for o, n in moves:
        groups[(_parent(o), _parent(n))] += 1
    return sorted(groups.items())


def n_meaningful(r):
    return (len(r["content_changed"]) + len(r["renamed"]) + len(r["moved_changed"])
            + len(r["added"]) + len(r["removed"]))


def counts_table(r):
    rows = [
        ("Files in previous manifest", r["n_old"]),
        ("Files in current manifest", r["n_new"]),
        ("Unchanged (same path and content)", r["unchanged"]),
        ("**Content changed** (same path)", len(r["content_changed"])),
        ("**Renamed** (same content, new name)", len(r["renamed"])),
        ("**Moved and changed** (same name, new location, new content)", len(r["moved_changed"])),
        ("**Added**", len(r["added"])),
        ("**Removed**", len(r["removed"])),
        ("Moved only (same name and content, new location)", len(r["moved"])),
    ]
    lines = ["| Category | Files |", "|---|---:|"]
    lines += [f"| {label} | {count} |" for label, count in rows]
    return "\n".join(lines)


def _fmt_added(path, copy_of):
    return f"`{path}` (identical to `{copy_of[0]}`)" if copy_of else f"`{path}`"


def _dir_item(d, n, kind):
    return f"`{d}/` ({kind} directory, {n} files)"


def category_items(r):
    """Yield (heading, file count, [markdown list items]) per meaningful category.

    Added/removed files that make up a wholly new/removed directory are listed
    as that directory, so a new ado/ tree is one line rather than hundreds.
    """
    yield "Content changed", len(r["content_changed"]), [f"`{p}`" for p in r["content_changed"]]
    yield "Renamed", len(r["renamed"]), [f"`{o}` → `{n}`" for o, n in r["renamed"]]
    yield ("Moved and changed", len(r["moved_changed"]),
           [f"`{o}` → `{n}`" for o, n in r["moved_changed"]])
    copies = dict(r["added"])
    groups, singles = roll_up(copies, r["old_dirs"])
    yield ("Added", len(r["added"]),
           [_dir_item(d, n, "new") for d, n in groups] + [_fmt_added(p, copies[p]) for p in singles])
    groups, singles = roll_up(r["removed"], r["new_dirs"])
    yield ("Removed", len(r["removed"]),
           [_dir_item(d, n, "removed") for d, n in groups] + [f"`{p}`" for p in singles])


def render_report(r):
    out = [counts_table(r), ""]
    if n_meaningful(r) == 0:
        out.append(f"No files were added, removed, renamed, or changed in content "
                   f"({r['unchanged']} files identical"
                   + (f", {len(r['moved'])} moved without changes" if r["moved"] else "")
                   + ").")
        out.append("")
    for heading, n, items in category_items(r):
        if items:
            out += [f"**{heading}** ({n}):", ""] + [f"- {i}" for i in items] + [""]
    if r["moved"]:
        out += [f"**Moved only** ({len(r['moved'])} files, same name and content; "
                "not a substantive change), by directory:", ""]
        out += [f"- `{o}/` → `{n}/` ({c} file{'s' if c != 1 else ''})"
                for (o, n), c in group_moves(r["moved"])]
        out.append("")
    return "\n".join(out)


def render_summary(r, previous_name, current_name):
    out = ["# Manifest Comparison Summary", "",
           f"Previous: `{previous_name}`  ",
           f"Current: `{current_name}`", "",
           counts_table(r), ""]
    if n_meaningful(r) == 0:
        out += ["No meaningful changes (no files added, removed, renamed, or changed in content).", ""]
        return "\n".join(out)
    out += ["## Meaningful changes", ""]
    for heading, n, items in category_items(r):
        if not items:
            continue
        out += [f"**{heading}** ({n}):", ""]
        out += [f"- {i}" for i in items[:SUMMARY_LIMIT]]
        if len(items) > SUMMARY_LIMIT:
            out.append(f"- ... and {len(items) - SUMMARY_LIMIT} more entries (see `manifest-comparison.md`)")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report meaningful changes between two SHA256 manifests",
        epilog="Example: python compare_manifests.py generated/manifest.2026-11-03.sha256 "
               "generated/manifest.2026-11-06.sha256 --summary-file generated/manifest-cmp-summary.md",
    )
    parser.add_argument("manifest1", help="Previous SHA256 manifest")
    parser.add_argument("manifest2", help="Current SHA256 manifest")
    parser.add_argument("--summary-file", help="Also write a short summary to this file")
    args = parser.parse_args(argv)

    try:
        old = parse_manifest(args.manifest1)
        new = parse_manifest(args.manifest2)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    result = compare(old, new)
    print(render_report(result))
    if args.summary_file:
        with open(args.summary_file, "w", encoding="utf-8") as f:
            f.write(render_summary(result, PurePosixPath(args.manifest1).name,
                                   PurePosixPath(args.manifest2).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
