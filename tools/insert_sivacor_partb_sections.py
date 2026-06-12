#!/usr/bin/env python3
"""Insert SIVACOR sections into an existing Part B Markdown template."""

import argparse
import re
import sys


def read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content.rstrip())
        handle.write("\n")


def insert_after_replication_steps(content, insert_text):
    marker = "## Replication steps"
    pos = content.find(marker)
    if pos == -1:
        raise ValueError("Could not find '## Replication steps' section")

    next_heading = content.find("\n## ", pos + len(marker))
    section_end = next_heading if next_heading != -1 else len(content)
    replacement = marker + "\n\n" + insert_text.strip() + "\n\n"
    return content[:pos] + replacement + content[section_end:].lstrip()


def replace_computing_environment(content, insert_text):
    marker = "## Computing Environment of the Replicator"
    pos = content.find(marker)
    if pos == -1:
        raise ValueError("Could not find '## Computing Environment of the Replicator' section")

    next_heading = content.find("\n## ", pos + len(marker))
    section_end = next_heading if next_heading != -1 else len(content)
    replacement = marker + "\n\n" + insert_text.strip() + "\n\n"
    return content[:pos] + replacement + content[section_end:].lstrip()


def insert_after_findings_intro(content, insert_text):
    marker = "## Findings"
    pos = content.find(marker)
    if pos == -1:
        raise ValueError("Could not find '## Findings' section")

    first_subheading = content.find("\n### ", pos + len(marker))
    if first_subheading == -1:
        raise ValueError("Could not find first Findings subsection")

    return content[:first_subheading].rstrip() + "\n\n" + insert_text + "\n\n" + content[first_subheading:].lstrip()


def remove_existing_sivacor_sections(content):
    content = re.sub(
        r"\nThe AEA reviewer did not rerun the author code\. The SIVACOR TRO records the following execution environment:\n\n.*?(?=\n## Replication steps)",
        "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"\n\*\*SIVACOR automated execution summary\*\*.*?(?=\n- \[ \] The reproducibility check|\n> INSTRUCTIONS: provide details|\n## Findings)",
        "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"\n### SIVACOR-generated files\n\n.*?(?=\n### |\n## )",
        "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"\n## Appendix\n\n### SIVACOR arrangement comparison\n\n.*\Z",
        "\n",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"\n## Appendix: SIVACOR arrangement comparison\n\n.*\Z",
        "\n",
        content,
        flags=re.DOTALL,
    )
    return content


def main():
    parser = argparse.ArgumentParser(description="Insert generated SIVACOR Part B sections into a Markdown template.")
    parser.add_argument("--template", required=True, help="Existing Part B Markdown template")
    parser.add_argument("--computing-environment", required=True, help="Generated SIVACOR computing environment Markdown")
    parser.add_argument("--replication-steps", required=True, help="Generated SIVACOR replication steps Markdown")
    parser.add_argument("--findings", required=True, help="Generated SIVACOR findings Markdown")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing")
    args = parser.parse_args()

    content = remove_existing_sivacor_sections(read_file(args.template))
    content = replace_computing_environment(content, read_file(args.computing_environment).strip())
    content = insert_after_replication_steps(content, read_file(args.replication_steps).strip())
    content = insert_after_findings_intro(content, read_file(args.findings).strip())

    if args.dry_run:
        print(content)
    else:
        write_file(args.output, content)
        print(f"Successfully wrote {args.output}.", file=sys.stderr)


if __name__ == "__main__":
    main()
