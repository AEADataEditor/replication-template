#!/usr/bin/env python3
"""
add-png.py: Append all PNG files from a directory to REPLICATION.md

Python equivalent of add-png.sh, for users without a bash shell.
Usage: add-png.py <directory>
"""

import os
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <directory>", file=sys.stderr)
        sys.exit(1)

    directory = Path(sys.argv[1])

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    replication_md = repo_root / "REPLICATION.md"

    if not replication_md.is_file():
        print(f"Error: REPLICATION.md not found at {replication_md}", file=sys.stderr)
        sys.exit(1)

    pngs = sorted(directory.glob("*.png"))

    if not pngs:
        print(f"No PNG files found in '{directory}'.", file=sys.stderr)
        sys.exit(0)

    with open(replication_md, "a") as f:
        for png in pngs:
            rel_path = os.path.relpath(png.resolve(), repo_root)
            f.write(f"\n**{png.name}**\n\n![]({rel_path})\n")

    print(f"Appended {len(pngs)} PNG(s) to {replication_md}")


if __name__ == "__main__":
    main()
