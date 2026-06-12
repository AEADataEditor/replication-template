#!/usr/bin/env python3
"""Insert SIVACOR appendix material into generated/REPLICATION_appendix.md."""

import argparse
import os
import re
import sys


SECTION_PATTERN = re.compile(
    r"\n## Appendix: SIVACOR arrangement comparison\n\n.*?(?=\n## Appendix: |\Z)",
    flags=re.DOTALL,
)


def read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def normalize_heading(content):
    return re.sub(r"\A### SIVACOR arrangement comparison", "## Appendix: SIVACOR arrangement comparison", content.strip())


def update_appendix(existing_content, sivacor_content):
    section = normalize_heading(sivacor_content)
    if existing_content.strip():
        base = SECTION_PATTERN.sub("", existing_content).rstrip()
        return base + "\n\n" + section + "\n"
    return "# Automatically Generated Appendices\n\n> No action is required, unless indicated in the main body of the report.\n\n" + section + "\n"


def main():
    parser = argparse.ArgumentParser(description="Add SIVACOR arrangement comparison to generated appendix.")
    parser.add_argument("--appendix", default="generated/REPLICATION_appendix.md", help="Generated appendix file to update")
    parser.add_argument("--sivacor-appendix", required=True, help="Generated SIVACOR appendix snippet")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing")
    args = parser.parse_args()

    sivacor_content = read_file(args.sivacor_appendix)
    existing_content = read_file(args.appendix) if os.path.exists(args.appendix) else ""
    updated = update_appendix(existing_content, sivacor_content)

    if args.dry_run:
        print(updated)
    else:
        os.makedirs(os.path.dirname(args.appendix) or ".", exist_ok=True)
        write_file(args.appendix, updated)
        print(f"Successfully updated {args.appendix}.", file=sys.stderr)


if __name__ == "__main__":
    main()
