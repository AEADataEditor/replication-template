#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

"""Syntax-check the repository's shell scripts and YAML files.

Shell scripts (``automations/*.sh``, ``tools/*.sh``, ``build/*.sh``) are checked
with ``bash -n``; ``*.yml``/``*.yaml`` files tracked in the repository's
top level, ``docs/`` and ``.github/`` are parsed with PyYAML. Exits non-zero
and lists every offending file if anything fails to parse.

Usage: python3 tools/check_syntax.py [--root DIR]
"""
import argparse
import glob
import os
import subprocess
import sys

import yaml

SHELL_GLOBS = ["automations/*.sh", "tools/*.sh", "build/*.sh"]
YAML_GLOBS = ["*.yml", "*.yaml", "docs/*.yml", ".github/**/*.yml"]


def find_files(root, patterns):
    found = set()
    for pattern in patterns:
        found.update(glob.glob(os.path.join(root, pattern), recursive=True))
    return sorted(found)


def check_shell(path):
    result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
    return None if result.returncode == 0 else result.stderr.strip()


def check_yaml(path):
    try:
        with open(path, encoding="utf-8") as handle:
            list(yaml.safe_load_all(handle))
    except yaml.YAMLError as exc:
        return str(exc)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--root", default=default_root)
    args = parser.parse_args(argv)

    failures = []
    for path in find_files(args.root, SHELL_GLOBS):
        error = check_shell(path)
        if error:
            failures.append((path, error))
    for path in find_files(args.root, YAML_GLOBS):
        error = check_yaml(path)
        if error:
            failures.append((path, error))

    for path, error in failures:
        print(f"FAIL {os.path.relpath(path, args.root)}\n{error}\n")
    if failures:
        return 1
    print("All shell and YAML files parse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
