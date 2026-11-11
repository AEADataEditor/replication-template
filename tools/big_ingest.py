#!/usr/bin/env python3
"""
Helpers for handing a deposit that is too big for the regular ingest pipeline
over to the "big" ingest pipeline.

Usage:
    big_ingest.py record-size <project-dir> [--cache-dir cache] [--out generated/deposit-size.csv]
                              [--limit-mb N]
    big_ingest.py needs-4x [--size-file generated/deposit-size.csv]
                           [--threshold-mb N] [--margin-mb N]
    big_ingest.py set-vm-size <pipelines-yml> <pipeline-name> <size>
    big_ingest.py pipeline-variables [--config config.yml]
    big_ingest.py -h|--help

Subcommands:
    record-size          Write the sizes of the deposit to a CSV file in generated/
                         (so later steps and the final commit can reuse it):
                         zip_bytes (the ZIP, 0 if there is none), unzipped_bytes,
                         and small_bytes (files not larger than the limit, which
                         are the ones git stores a copy of; the limit is
                         config.yml's limitsize, in MB). The ZIP is looked for as
                         <project-dir>.zip, then <cache-dir>/<project-dir>.zip.
                         Without an unpacked directory, the file sizes are read
                         from the ZIP's central directory.
    needs-4x             Exit 0 if the deposit does not fit on the disk of a 2x
                         worker, 1 if it does, 2 on a configuration error.
                         Space needed = max(zip + unzipped,      # while unpacking
                                            unzipped + small)    # while committing
                                        + margin
                         compared with the threshold (the measured free space of
                         the build volume). A missing or unreadable size file
                         counts as "does not fit" (the ZIP did not even fit into
                         the cache). Defaults come from config.yml keys
                         bigingest_threshold_mb and bigingest_margin_mb.
    set-vm-size          Set `size:` of the first step of the given custom
                         pipeline in bitbucket-pipelines.yml, in place, leaving
                         the rest of the file byte-identical. Exit 0 if changed,
                         1 if it already had that size.
    pipeline-variables   Print the PIPELINE_VARIABLES JSON for
                         atlassian/trigger-pipeline, from config.yml and the
                         environment (jiraticket, openICPSRID, ZenodoID, ...).
"""

import argparse
import csv
import json
import os
import re
import sys
import zipfile

BYTES_PER_MB = 1024 * 1024
DEFAULT_SIZE_FILE = os.path.join("generated", "deposit-size.csv")

# pipeline variable -> (environment variable, config.yml key)
PIPELINE_VARIABLES = (
    ("jiraticket", "jiraticket", "jiraticket"),
    ("openICPSRID", "openICPSRID", "openicpsr"),
    ("ZenodoID", "ZenodoID", "zenodo"),
    ("WorldBankID", "WorldBankID", "worldbank"),
    ("DataverseID", "DataverseID", "dataverse"),
)


def read_config(path):
    """Top-level `key: value` pairs of config.yml (keys lower-cased)."""
    values = {}
    if not os.path.isfile(path):
        return values
    with open(path) as fh:
        for line in fh:
            m = re.match(r"^([A-Za-z_][\w]*):[ \t]*(.*?)[ \t]*$", line)
            if m and not m.group(2).startswith("#"):
                value = re.sub(r"[ \t]+#.*$", "", m.group(2))  # inline comment
                values[m.group(1).lower()] = value.strip("\"'")
    return values


def dir_file_sizes(directory):
    """Sizes of the files under directory (symlinks excluded)."""
    for root, _dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            if not os.path.islink(path):
                yield os.path.getsize(path)


def zip_file_sizes(zip_path):
    """Uncompressed sizes of the files in a ZIP, from its central directory."""
    with zipfile.ZipFile(zip_path) as zf:
        return [info.file_size for info in zf.infolist() if not info.is_dir()]


def record_size(project_dir, cache_dir, out, limit_mb):
    name = os.path.basename(os.path.normpath(project_dir))
    zip_path = next((p for p in (f"{name}.zip", os.path.join(cache_dir, f"{name}.zip"))
                     if os.path.isfile(p)), None)
    zip_bytes = os.path.getsize(zip_path) if zip_path else 0
    if os.path.isdir(project_dir):
        sizes = list(dir_file_sizes(project_dir))
    elif zip_path:
        sizes = zip_file_sizes(zip_path)
    else:
        raise SystemExit(f"Neither {project_dir}/ nor {name}.zip found")
    limit = limit_mb * BYTES_PER_MB
    data = {"project": name, "zip_bytes": zip_bytes, "unzipped_bytes": sum(sizes),
            "small_bytes": sum(s for s in sizes if s <= limit)}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(data))
        writer.writeheader()
        writer.writerow(data)
    return data


def space_needed(zip_bytes, unzipped_bytes, small_bytes, margin_bytes):
    """Peak disk use: unpacking holds ZIP + files, committing holds files + git's copy of the small ones."""
    return max(zip_bytes + unzipped_bytes, unzipped_bytes + small_bytes) + margin_bytes


def exceeds(size_file, threshold_mb, margin_mb):
    """True if the space needed is above the threshold (or the size is unknown)."""
    try:
        with open(size_file, newline="") as fh:
            data = next(csv.DictReader(fh))
        zip_bytes, unzipped = int(data["zip_bytes"]), int(data["unzipped_bytes"])
        small = int(data["small_bytes"]) if data.get("small_bytes") else unzipped  # bound: git copies everything
        needed = space_needed(zip_bytes, unzipped, small, margin_mb * BYTES_PER_MB)
    except (OSError, ValueError, KeyError, StopIteration):
        return True
    return needed > threshold_mb * BYTES_PER_MB


def set_vm_size(yml_path, pipeline, size):
    """Edit `size:` in the first step of custom pipeline `pipeline`. True if changed."""
    with open(yml_path) as fh:
        lines = fh.read().splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines)
                  if re.match(rf"^\s+{re.escape(pipeline)}:\s*(#.*)?$", l)), None)
    if start is None:
        raise SystemExit(f"Pipeline {pipeline} not found in {yml_path}")
    indent = len(lines[start]) - len(lines[start].lstrip())
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line.lstrip().startswith("#") and \
                len(line) - len(line.lstrip()) <= indent:
            break  # next pipeline
        m = re.match(r"^(\s+size:\s*)(\S+)(.*)$", line, re.S)
        if m:
            if m.group(2) == size:
                return False
            lines[i] = f"{m.group(1)}{size}{m.group(3)}"
            with open(yml_path, "w") as fh:
                fh.writelines(lines)
            return True
    raise SystemExit(f"No `size:` found in pipeline {pipeline}")


def pipeline_variables(config_path, environ):
    config = read_config(config_path)
    out = []
    for var, env_key, cfg_key in PIPELINE_VARIABLES:
        value = environ.get(env_key) or config.get(cfg_key)
        if value:
            out.append({"key": var, "value": value})
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("record-size")
    s.add_argument("project_dir")
    s.add_argument("--cache-dir", default="cache")
    s.add_argument("--out", default=DEFAULT_SIZE_FILE)
    s.add_argument("--config", default="config.yml")
    s.add_argument("--limit-mb", type=float, help="default: limitsize from config.yml")

    s = sub.add_parser("needs-4x")
    s.add_argument("--size-file", default=DEFAULT_SIZE_FILE)
    s.add_argument("--config", default="config.yml")
    s.add_argument("--threshold-mb", type=float)
    s.add_argument("--margin-mb", type=float)

    s = sub.add_parser("set-vm-size")
    s.add_argument("pipelines_yml")
    s.add_argument("pipeline")
    s.add_argument("size")

    s = sub.add_parser("pipeline-variables")
    s.add_argument("--config", default="config.yml")

    args = p.parse_args(argv)

    if args.cmd == "record-size":
        limit = args.limit_mb if args.limit_mb is not None else read_config(args.config).get("limitsize")
        try:
            limit = float(limit)
        except (TypeError, ValueError):
            print("limitsize must be set to a number in config.yml (or pass --limit-mb)", file=sys.stderr)
            return 2
        data = record_size(args.project_dir, args.cache_dir, args.out, limit)
        print(f"Recorded in {args.out}: zip {data['zip_bytes'] / BYTES_PER_MB:.0f} MB, "
              f"unzipped {data['unzipped_bytes'] / BYTES_PER_MB:.0f} MB, "
              f"files up to {limit:.0f} MB {data['small_bytes'] / BYTES_PER_MB:.0f} MB")
        return 0
    if args.cmd == "needs-4x":
        config = read_config(args.config)
        threshold = args.threshold_mb if args.threshold_mb is not None else config.get("bigingest_threshold_mb")
        margin = args.margin_mb if args.margin_mb is not None else config.get("bigingest_margin_mb")
        if threshold is None or margin is None:
            print("bigingest_threshold_mb and bigingest_margin_mb must be set in config.yml "
                  "(or passed as options)", file=sys.stderr)
            return 2
        try:
            threshold, margin = float(threshold), float(margin)
        except ValueError:
            print(f"Threshold/margin must be numbers, got {threshold!r}/{margin!r}", file=sys.stderr)
            return 2
        return 0 if exceeds(args.size_file, threshold, margin) else 1
    if args.cmd == "set-vm-size":
        return 0 if set_vm_size(args.pipelines_yml, args.pipeline, args.size) else 1
    if args.cmd == "pipeline-variables":
        print(json.dumps(pipeline_variables(args.config, os.environ)))
        return 0


if __name__ == "__main__":
    sys.exit(main())
