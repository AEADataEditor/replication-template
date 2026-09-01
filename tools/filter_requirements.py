"""Post-process the pipreqs scan against an author-provided requirements.txt.

Authors working in conda environments often ship a `pip freeze` of their entire
Anaconda installation: hundreds of packages, many with non-portable
`name @ file:///...` references to local conda build directories. Such a file
is not usable with `pip install -r` and drowns the report in noise.

This tool:
  - detects whether the author file is such an environment dump;
  - if so, intersects it with the pipreqs scan (packages actually imported),
    keeping author version pins where recoverable, and rewrites the scanned
    requirements file with the result;
  - writes generated/python-deps.csv (the source for the report appendix);
  - writes a software-warnings fragment for the top of the report whenever
    a scan was run.
"""

import argparse
import os
import re
import sys

# Packages that only appear in requirements files frozen from a full
# conda/Anaconda installation, never in a hand-curated dependency list.
CONDA_INFRA_PACKAGES = {
    "conda",
    "conda-build",
    "conda-pack",
    "conda-token",
    "anaconda-client",
    "anaconda-navigator",
    "anaconda-project",
    "anaconda-anon-usage",
    "menuinst",
    "navigator-updater",
}

PYTHON_APPENDIX_ANCHOR = "#appendix-candidate-python-packages-if-any-based-on-scan"

NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
PIN_RE = re.compile(r"==\s*([^\s;#]+)")


def normalize(name):
    """PEP 503 name normalization."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(path):
    """Return (entries, has_file_refs). entries maps normalized name ->
    (original name, pinned version or None)."""
    entries = {}
    has_file_refs = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            if "@ file:" in line or "@file:" in line:
                has_file_refs = True
            m = NAME_RE.match(line)
            if not m:
                continue
            name = m.group(1)
            pin = None
            if "@" not in line:
                pin_match = PIN_RE.search(line)
                if pin_match:
                    pin = pin_match.group(1)
            entries[normalize(name)] = (name, pin)
    return entries, has_file_refs


def is_environment_dump(entries, has_file_refs):
    infra_hits = CONDA_INFRA_PACKAGES.intersection(entries)
    return has_file_refs or len(infra_hits) >= 2


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def write_deps_csv(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("Packages\n")
        for line in lines:
            f.write(line + "\n")


def write_warning(path, escalated):
    if escalated:
        text = (
            "> [NOTE] The author-provided `requirements.txt` appears to be a dump of a full "
            "conda/Anaconda environment (it contains non-portable `file:///` references and/or "
            "distribution-wide packages) and cannot be used with `pip install -r`. We generated "
            "a `requirements-generated.txt` restricted to the packages actually imported by the "
            "code, keeping the author's version pins where available. Please verify it against "
            "the README, and consider replacing the provided `requirements.txt` with it. See "
            "[Appendix: Candidate Python packages]"
            f"({PYTHON_APPENDIX_ANCHOR}).\n"
        )
    else:
        text = (
            "> [NOTE] Python code was detected and scanned. Please compare the identified "
            "packages against the requirements stated in the README. See "
            "[Appendix: Candidate Python packages]"
            f"({PYTHON_APPENDIX_ANCHOR}).\n"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", required=True,
                        help="Path to the author-provided requirements.txt (may not exist)")
    parser.add_argument("--scanned", required=True,
                        help="Path to the pipreqs output (rewritten in place when filtering)")
    parser.add_argument("--deps-csv", required=True,
                        help="Path to write the python-deps.csv used by the report")
    parser.add_argument("--warnings", required=True,
                        help="Path to write the software-warnings fragment")
    args = parser.parse_args()

    scan_ran = os.path.isfile(args.scanned)
    author_exists = os.path.isfile(args.author)

    if not scan_ran:
        # No scan: no warning fragment; keep the old behavior of reporting the
        # author file as-is when present.
        if author_exists:
            write_deps_csv(args.deps_csv, read_lines(args.author))
        print("No pipreqs output found; nothing to filter.")
        return

    scanned_lines = read_lines(args.scanned)
    scanned_entries, _ = parse_requirements(args.scanned)

    if not author_exists:
        write_deps_csv(args.deps_csv, scanned_lines)
        write_warning(args.warnings, escalated=False)
        print("No author requirements.txt; using scanned requirements.")
        return

    author_entries, has_file_refs = parse_requirements(args.author)

    if not is_environment_dump(author_entries, has_file_refs):
        write_deps_csv(args.deps_csv, read_lines(args.author))
        write_warning(args.warnings, escalated=False)
        print("Author requirements.txt looks curated; reporting it unchanged.")
        return

    # Environment dump: intersect the scan with the author file, preferring
    # author version pins where they survive (conda file:/// lines carry none).
    filtered = []
    for line in scanned_lines:
        m = NAME_RE.match(line)
        if not m:
            filtered.append(line)
            continue
        key = normalize(m.group(1))
        author_entry = author_entries.get(key)
        if author_entry and author_entry[1]:
            filtered.append(f"{author_entry[0]}=={author_entry[1]}")
        else:
            filtered.append(line)

    with open(args.scanned, "w", encoding="utf-8") as f:
        for line in filtered:
            f.write(line + "\n")
    write_deps_csv(args.deps_csv, filtered)
    write_warning(args.warnings, escalated=True)
    print(f"Author requirements.txt is a conda environment dump "
          f"({len(author_entries)} packages); "
          f"filtered to {len(filtered)} scanned packages.")


if __name__ == "__main__":
    sys.exit(main())
