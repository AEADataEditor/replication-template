#!/usr/bin/env python3
"""
find_cran_date.py — Determine the minimum CRAN snapshot date for a set of pinned R packages.

Given a file that specifies R package versions (R script, renv.lock, DESCRIPTION, or CSV),
this tool:
  1. Parses the package/version pairs
  2. Queries the crandb API for each package version's publication date
  3. Computes the earliest date at which all versions existed simultaneously on CRAN
  4. Reports the matching rocker/verse container image and Posit Package Manager snapshot URL

Usage:
  python tools/find_cran_date.py <input_file> [--output <path>] [--verbose]

Examples:
  python tools/find_cran_date.py 209465/Code/0_setup.R
  python tools/find_cran_date.py renv.lock --output generated/notes-for-r.md
  python tools/find_cran_date.py packages.csv --verbose
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Known R release history (version → release date).
# Covers R 4.0.0 through 4.5.x; update as new versions are released.
# ---------------------------------------------------------------------------
R_RELEASE_HISTORY = [
    ("4.0.0", "2020-04-24"), ("4.0.1", "2020-06-06"), ("4.0.2", "2020-06-22"),
    ("4.0.3", "2020-10-10"), ("4.0.4", "2021-02-15"), ("4.0.5", "2021-03-31"),
    ("4.1.0", "2021-05-18"), ("4.1.1", "2021-08-10"), ("4.1.2", "2021-11-01"),
    ("4.1.3", "2022-03-10"), ("4.2.0", "2022-04-22"), ("4.2.1", "2022-06-23"),
    ("4.2.2", "2022-10-31"), ("4.2.3", "2023-03-15"), ("4.3.0", "2023-04-21"),
    ("4.3.1", "2023-06-16"), ("4.3.2", "2023-10-31"), ("4.3.3", "2024-02-29"),
    ("4.4.0", "2024-04-24"), ("4.4.1", "2024-06-14"), ("4.4.2", "2024-10-31"),
    ("4.4.3", "2025-02-28"), ("4.5.0", "2025-04-11"), ("4.5.1", "2025-07-31"),
    ("4.5.2", "2025-10-31"), ("4.5.3", "2026-01-31"),
]

CACHE_DIR = Path.home() / ".cache" / "cran-pkg-dates"
PPM_BASE = "https://packagemanager.posit.co/cran"
CRANDB_BASE = "https://crandb.r-pkg.org"
PPM_API_BASE = "https://packagemanager.posit.co/cran/__api__/repos/1/packages"
USER_AGENT = "find_cran_date/1.0 (github.com/AEADataEditor)"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------

def _cache_path(pkg, version):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", f"{pkg}_{version}")
    return CACHE_DIR / f"{safe}.json"


def _cache_read(pkg, version):
    p = _cache_path(pkg, version)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def _cache_write(pkg, version, data):
    try:
        _cache_path(pkg, version).write_text(json.dumps(data))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Format auto-detection
# ---------------------------------------------------------------------------

def detect_format(filepath):
    name = Path(filepath).name.lower()
    if name == "renv.lock":
        return "renv_lock"
    if name == "description":
        return "description"
    ext = Path(filepath).suffix.lower()
    if ext in (".r",):
        return "r_script"
    if ext in (".lock",):
        return "renv_lock"
    if ext in (".csv", ".txt"):
        return "csv"
    # Fallback: try JSON parse
    try:
        with open(filepath) as f:
            json.load(f)
        return "renv_lock"
    except Exception:
        return "r_script"


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_r_script(filepath):
    """
    Extract (package, version) pairs from R scripts.
    Handles:
      - remotes::install_version("pkg", version = "x.y.z")
      - Named vector pattern: pkg = "x.y.z"  (within pkgs_versions = c(...))
      - install.packages("pkg") — no version, included with version=None
    """
    text = Path(filepath).read_text()
    packages = {}

    # Pattern 1: remotes::install_version("pkg", version = "x.y.z")
    for m in re.finditer(
        r'(?:remotes|devtools)::install_version\(\s*["\']([^"\']+)["\']'
        r'.*?version\s*=\s*["\']([^"\']+)["\']',
        text, re.DOTALL
    ):
        packages[m.group(1)] = m.group(2)

    # Pattern 2: named vector  pkg = "x.y.z"  inside c(...)
    # Find c(...) blocks that look like version vectors
    c_blocks = re.findall(r'c\s*\((.*?)\)', text, re.DOTALL)
    for block in c_blocks:
        pairs = re.findall(r'(\w[\w.]*)\s*=\s*["\']([0-9][^"\']*)["\']', block)
        if len(pairs) >= 3:  # heuristic: a version vector has several entries
            for pkg, ver in pairs:
                packages[pkg] = ver

    # Pattern 3: install.packages("pkg") — no pinned version
    for m in re.finditer(r'install\.packages\s*\(\s*["\']([^"\']+)["\']', text):
        pkg = m.group(1)
        if pkg not in packages:
            packages[pkg] = None

    return [(pkg, ver) for pkg, ver in packages.items()]


def parse_renv_lock(filepath):
    data = json.loads(Path(filepath).read_text())
    pkgs = data.get("Packages", {})
    result = []
    for name, info in pkgs.items():
        version = info.get("Version")
        source = info.get("Source", "Repository")
        result.append((name, version, source))
    return result  # returns (name, version, source) triples


def parse_description(filepath):
    text = Path(filepath).read_text()
    packages = {}
    in_deps = False
    for line in text.splitlines():
        if re.match(r'^(Imports|Depends|Suggests)\s*:', line):
            in_deps = True
            line = re.sub(r'^[A-Za-z]+\s*:', '', line)
        elif re.match(r'^\S', line) and in_deps:
            in_deps = False
        if in_deps:
            for m in re.finditer(r'(\w[\w.]*)\s*(?:\(\s*[><=]+\s*([0-9][^)]*)\))?', line):
                pkg = m.group(1).strip()
                ver = m.group(2).strip() if m.group(2) else None
                if pkg and pkg != "R":
                    packages[pkg] = ver
    return [(pkg, ver) for pkg, ver in packages.items()]


def parse_csv(filepath):
    packages = []
    for line in Path(filepath).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'([A-Za-z][\w.]*)\s*[=,]+\s*([0-9][^\s]*)', line)
        if m:
            packages.append((m.group(1), m.group(2)))
        else:
            m2 = re.match(r'([A-Za-z][\w.]*)', line)
            if m2:
                packages.append((m2.group(1), None))
    return packages


def parse_file(filepath):
    """
    Returns list of dicts: {pkg, version, source}
    source is "CRAN" for most packages, or something else if detectable.
    """
    fmt = detect_format(filepath)
    results = []

    if fmt == "renv_lock":
        for name, version, source in parse_renv_lock(filepath):
            results.append({"pkg": name, "version": version, "source": source})

    elif fmt == "r_script":
        for pkg, version in parse_r_script(filepath):
            results.append({"pkg": pkg, "version": version, "source": "CRAN"})

    elif fmt == "description":
        for pkg, version in parse_description(filepath):
            results.append({"pkg": pkg, "version": version, "source": "CRAN"})

    elif fmt == "csv":
        for pkg, version in parse_csv(filepath):
            results.append({"pkg": pkg, "version": version, "source": "CRAN"})

    # Also detect GitHub installs in R scripts
    if fmt == "r_script":
        text = Path(filepath).read_text()
        for m in re.finditer(
            r'(?:devtools|remotes)::install_github\s*\(\s*["\']([^"\']+)["\']', text
        ):
            pkg_path = m.group(1)
            pkg_name = pkg_path.split("/")[-1]
            for r in results:
                if r["pkg"] == pkg_name:
                    r["source"] = f"GitHub: {pkg_path}"
                    break
            else:
                results.append({"pkg": pkg_name, "version": None, "source": f"GitHub: {pkg_path}"})

    return results


# ---------------------------------------------------------------------------
# CRAN date lookup
# ---------------------------------------------------------------------------

def lookup_package_date(pkg, version, verbose=False):
    """
    Returns ISO date string "YYYY-MM-DD" or None.
    Tries PPM API first, falls back to crandb.
    Results are disk-cached.
    """
    cached = _cache_read(pkg, version)
    if cached is not None:
        if verbose:
            print(f"  [cache] {pkg} {version} → {cached.get('date')}", file=sys.stderr)
        return cached.get("date")

    date = None

    # Primary: PPM API
    url_ppm = f"{PPM_API_BASE}/{pkg}"
    data = _fetch_json(url_ppm)
    if data:
        # PPM returns a list of version objects or a single object
        versions_list = data if isinstance(data, list) else [data]
        for entry in versions_list:
            if entry.get("version") == version or entry.get("Version") == version:
                date = (entry.get("date") or entry.get("Date") or "")[:10]
                break
        # If PPM returned a single package object directly
        if not date and isinstance(data, dict):
            if data.get("version") == version or data.get("Version") == version:
                date = (data.get("date") or data.get("Date") or "")[:10]
    time.sleep(0.05)

    # Fallback: crandb
    if not date:
        url_cdb = f"{CRANDB_BASE}/{pkg}/{version}"
        data2 = _fetch_json(url_cdb)
        if data2:
            raw = data2.get("date") or data2.get("Date/Publication") or ""
            date = raw[:10] if raw else None
        time.sleep(0.05)

    if date:
        _cache_write(pkg, version, {"date": date})
    else:
        if verbose:
            print(f"  [warn] could not find date for {pkg} {version}", file=sys.stderr)

    return date


# ---------------------------------------------------------------------------
# R version lookup
# ---------------------------------------------------------------------------

def find_r_version_for_date(min_date):
    """Return the highest R version released on or before min_date."""
    valid = [(ver, d) for ver, d in R_RELEASE_HISTORY if d <= min_date]
    if not valid:
        return None
    return max(valid, key=lambda x: x[1])[0]


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def write_markdown(output_path, input_file, pkg_dates, skipped, bottleneck_date,
                   fudge, ppm_date, bottlenecks, r_version):
    ppm_url = f"{PPM_BASE}/{ppm_date}"
    rocker_image = f"rocker/verse:{r_version}" if r_version else "unknown"

    # Sort packages by date descending for the table
    dated = sorted(
        [(pkg, ver, date) for (pkg, ver), date in pkg_dates.items()],
        key=lambda x: x[2],
        reverse=True,
    )

    bottleneck_keys = {(pkg, ver) for pkg, ver, _ in bottlenecks}

    lines = []
    lines.append("### R Environment Notes")
    lines.append("")
    lines.append(
        f"The replication package specifies {len(pkg_dates) + len(skipped)} R packages, "
        f"of which {len(pkg_dates)} have pinned CRAN versions. "
        f"Publication dates were retrieved from the [crandb API](https://crandb.r-pkg.org/)."
    )
    lines.append("")
    lines.append("#### Conclusion")
    lines.append("")
    lines.append(
        f"The earliest date at which all pinned package versions simultaneously existed "
        f"on CRAN is **{bottleneck_date}**, determined by the latest-published package(s): "
        + ", ".join(f"`{pkg}` {ver}" for pkg, ver, _ in bottlenecks) + "."
        + f" A fudge factor of {fudge} day(s) is added to ensure packages published on that date are included."
    )
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    lines.append(f"| Bottleneck date | {bottleneck_date} |")
    lines.append(f"| Fudge factor | {fudge} day(s) |")
    lines.append(f"| Snapshot date (bottleneck + fudge) | {ppm_date} |")
    lines.append(f"| R version current on that date | R {r_version} |" if r_version else "| R version | unknown |")
    lines.append(f"| Recommended rocker image | `{rocker_image}` |")
    lines.append(f"| Posit Package Manager CRAN URL | `{ppm_url}` |")
    lines.append("")
    lines.append("To reproduce this environment, add the following to your R setup code:")
    lines.append("")
    lines.append("```r")
    lines.append(f'ppm.fudge   <- {fudge}L  # days added as safety margin to bottleneck date {bottleneck_date}')
    lines.append(f'ppm.date    <- as.character(as.Date("{bottleneck_date}") + ppm.fudge)')
    lines.append('os.codename <- system("lsb_release -cs", intern = TRUE)')
    lines.append('options(repos = c(CRAN = sprintf("https://packagemanager.posit.co/cran/%s/bin/linux/%s-%s/%s",')
    lines.append('  ppm.date, os.codename, R.version["arch"], substr(getRversion(), 1, 3))))')
    lines.append("```")
    lines.append("")

    if skipped:
        lines.append(
            "The following packages are not on CRAN and are excluded from the date calculation:"
        )
        lines.append("")
        lines.append("| Package | Source |")
        lines.append("|---------|--------|")
        for pkg, ver, source in skipped:
            lines.append(f"| {pkg} | {source} |")
        lines.append("")

    lines.append("#### Package Publication Dates")
    lines.append("")
    lines.append(
        "Packages are sorted by publication date (most recent first). "
        "Bottleneck packages (latest publication date) are marked with ★."
    )
    lines.append("")
    lines.append("| Package | Version | Published |")
    lines.append("|---------|---------|-----------|")
    for pkg, ver, date in dated:
        star = " ★" if (pkg, ver) in bottleneck_keys else ""
        lines.append(f"| {pkg}{star} | {ver} | {date} |")

    content = "\n".join(lines) + "\n"

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(content)
        print(f"Written to {output_path}")
    else:
        print(content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Find the earliest CRAN snapshot date for a set of pinned R packages."
    )
    parser.add_argument("input_file", help="R script, renv.lock, DESCRIPTION, or CSV file")
    parser.add_argument(
        "--output", "-o",
        help="Write Markdown report to this path (default: print to stdout)",
        default=None,
    )
    parser.add_argument(
        "--fudge", "-f",
        type=int,
        default=2,
        metavar="DAYS",
        help="Days to add to the bottleneck date as a safety margin (default: 2)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-package status to stderr",
    )
    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Parse
    entries = parse_file(args.input_file)
    if not entries:
        print("No packages found in input file.", file=sys.stderr)
        sys.exit(1)

    # Split into CRAN vs non-CRAN
    cran_entries = [e for e in entries if e["source"] in ("CRAN", "Repository") and e["version"]]
    skipped = []
    for e in entries:
        if e["source"] not in ("CRAN", "Repository"):
            skipped.append((e["pkg"], e["version"], e["source"]))
        elif not e["version"]:
            skipped.append((e["pkg"], e["version"], "no version pinned"))

    print(
        f"Querying CRAN dates for {len(cran_entries)} packages "
        f"({len(skipped)} skipped)...",
        file=sys.stderr,
    )

    # Lookup dates
    pkg_dates = {}
    not_found = []
    for i, entry in enumerate(cran_entries, 1):
        pkg, ver = entry["pkg"], entry["version"]
        if args.verbose:
            print(f"  [{i}/{len(cran_entries)}] {pkg} {ver}", file=sys.stderr)
        date = lookup_package_date(pkg, ver, verbose=args.verbose)
        if date:
            pkg_dates[(pkg, ver)] = date
        else:
            not_found.append((pkg, ver, "not found on CRAN"))

    skipped.extend(not_found)

    if not pkg_dates:
        print("No package dates found.", file=sys.stderr)
        sys.exit(1)

    # Compute minimum viable date
    max_date = max(pkg_dates.values())
    bottlenecks = [(pkg, ver, date) for (pkg, ver), date in pkg_dates.items() if date == max_date]

    fudged_date = (datetime.strptime(max_date, "%Y-%m-%d") + timedelta(days=args.fudge)).strftime("%Y-%m-%d")
    r_version = find_r_version_for_date(fudged_date)

    # Print summary to stderr
    print(f"\nBottleneck: {', '.join(f'{p} {v}' for p, v, _ in bottlenecks)} ({max_date})", file=sys.stderr)
    print(f"Snapshot date: {fudged_date} (bottleneck + {args.fudge} day fudge)", file=sys.stderr)
    print(f"Rocker image:  rocker/verse:{r_version}", file=sys.stderr)
    print(f"PPM CRAN URL:  {PPM_BASE}/{fudged_date}", file=sys.stderr)

    write_markdown(
        output_path=args.output,
        input_file=args.input_file,
        pkg_dates=pkg_dates,
        skipped=skipped,
        bottleneck_date=max_date,
        fudge=args.fudge,
        ppm_date=fudged_date,
        bottlenecks=bottlenecks,
        r_version=r_version,
    )


if __name__ == "__main__":
    main()
