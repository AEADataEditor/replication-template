#!/usr/bin/env python3
"""
parse-stata-logs.py

Parse Stata system log files (system-*.log) and extract system information:
- Stata version details
- Processor/core licensing and availability

Usage:
    python parse-stata-logs.py <root_folder>
"""

import sys
import re
from pathlib import Path


# Keys to extract from the creturn list block, with friendly labels
KEYS = {
    "c(stata_name)":       "Stata name",
    "c(stata_version)":    "Stata version",
    "c(version)":          "Version (set)",
    "c(born_date)":        "Build date",
    "c(edition_real)":     "Edition",
    "c(processors_lic)":   "Processors (licensed)",
    "c(processors_max)":   "Processors (max usable)",
}

# Regex: match a creturn value line, e.g.:
#     c(stata_version) = 19.5
# or  c(born_date) = "15 Apr 2026"
# Values may be truncated with ".." — we capture as-is.
_VALUE_RE = re.compile(
    r'^\s*(c\(\w+\))\s*=\s*(.+?)(?:\s+\(.*\))?\s*$'
)


def extract_log_header(lines):
    """Return the log open date/time from the header block."""
    for line in lines[:20]:
        m = re.search(r'opened on:\s+(.+)', line)
        if m:
            return m.group(1).strip()
    return None


def parse_creturn_block(lines):
    """Scan all lines and collect wanted creturn values."""
    results = {}
    in_block = False
    for line in lines:
        if re.match(r'^\.\s+creturn list', line):
            in_block = True
            continue
        if in_block:
            # End of block heuristic: next Stata command
            if re.match(r'^\.\s+\S', line) and not re.match(r'^\.\s+creturn', line):
                break
            m = _VALUE_RE.match(line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"')
                if key in KEYS:
                    results[key] = val
    return results


def process_file(path):
    """Return a dict with log metadata and extracted values, or None on error."""
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        print(f"  Warning: cannot read {path}: {exc}", file=sys.stderr)
        return None

    lines = text.splitlines()
    opened_on = extract_log_header(lines)
    values = parse_creturn_block(lines)

    return {
        "path": path,
        "opened_on": opened_on,
        "values": values,
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <root_folder>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    log_files = sorted(root.rglob("system-*.log")) + sorted(root.rglob("system_*.log")) + sorted(root.rglob("system__*.log"))
    # Deduplicate while preserving order
    seen = set()
    unique_logs = []
    for f in log_files:
        if f not in seen:
            seen.add(f)
            unique_logs.append(f)
    log_files = unique_logs

    if not log_files:
        print(f"No system log files found under {root}.")
        sys.exit(0)

    print(f"# Stata System Information\n")
    print(f"Root folder: `{root.resolve()}`\n")
    print(f"Found **{len(log_files)}** system log file(s).\n")

    # Collect all results, group by unique value fingerprint
    # fingerprint key: frozenset of (creturn_key, value) pairs
    groups = {}   # fingerprint -> {"vals": dict, "files": [rel_path, ...]}

    for logfile in log_files:
        rel = str(logfile.relative_to(root) if logfile.is_relative_to(root) else logfile)
        info = process_file(logfile)
        if info is None:
            groups.setdefault("__unreadable__", {"vals": None, "files": []})["files"].append(rel)
            continue

        vals = info["values"]
        fingerprint = frozenset(vals.items())
        if fingerprint not in groups:
            groups[fingerprint] = {"vals": vals, "files": []}
        groups[fingerprint]["files"].append(rel)

    for fingerprint, group in groups.items():
        print(f"---\n")
        files = group["files"]
        if len(files) == 1:
            print(f"## `{files[0]}`\n")
        else:
            print(f"## Seen in {len(files)} log file(s)\n")
            for f in files:
                print(f"- `{f}`")
            print()

        if fingerprint == "__unreadable__":
            print("- *(could not read file)*\n")
            continue

        vals = group["vals"]
        if not vals:
            print("- *(no creturn list block found)*\n")
            continue

        # Combine stata_name and stata_version on one line
        name = vals.get("c(stata_name)")
        version = vals.get("c(stata_version)")
        if name and version:
            print(f"- Stata (c(stata_name) c(stata_version)): {name} {version}")
        elif name:
            print(f"- Stata (c(stata_name)): {name}")
        elif version:
            print(f"- Stata version (c(stata_version)): {version}")

        for key in ["c(version)", "c(born_date)", "c(edition_real)"]:
            if key in vals:
                print(f"- {KEYS[key]} ({key}): {vals[key]}")

        for key in ["c(processors_lic)", "c(processors_max)"]:
            if key in vals:
                print(f"- {KEYS[key]} ({key}): {vals[key]}")

        print()


if __name__ == "__main__":
    main()
