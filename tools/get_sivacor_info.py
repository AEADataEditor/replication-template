#!/usr/bin/env python3
"""
Parse SIVACOR JSONLD files for information.

Usage:
    get_sivacor_info.py <jsonld_file> <keyword>
    get_sivacor_info.py --jsonld <file> --key <keyword>
    get_sivacor_info.py --jobid <job_id> --key <keyword>
    get_sivacor_info.py --jobid <job_id> --key <keyword> --report <report_file>
    get_sivacor_info.py --jobid <job_id> --key <keyword> --report <report_file> --dry-run
"""

import json
import argparse
import sys
import os
import glob
import re
from datetime import datetime
from collections import Counter


SUPPORTED_KEYWORDS = (
    "computing",
    "time",
    "partb",
    "partb-sivacor",
    "sivacor-computing-environment",
    "sivacor-replication-steps",
    "sivacor-findings",
    "sivacor-appendix",
)


def find_jsonld_by_jobid(jobid, search_dir="."):
    """Find JSONLD file by job ID."""
    patterns = [
        f"**/tro-{jobid}.jsonld",
        f"tro-{jobid}.jsonld",
    ]
    
    for pattern in patterns:
        matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)
        if matches:
            return matches[0]
    
    # Also search from current directory up
    search_dir = os.getcwd()
    for pattern in patterns:
        matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)
        if matches:
            return matches[0]
    
    return None


def find_log_file(kind, jobid=None, jsonld_file=None, search_dir="."):
    """Find stdout/stderr logs associated with a SIVACOR job."""
    candidates = []

    if jsonld_file:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(jsonld_file)))
        if jobid:
            candidates.append(os.path.join(base_dir, f"{kind}-{jobid}"))
        candidates.append(os.path.join(base_dir, kind))

    if jobid:
        patterns = [
            f"**/{kind}-{jobid}",
            f"{kind}-{jobid}",
        ]
        for pattern in patterns:
            matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)
            if matches:
                return matches[0]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def bytes_to_human_readable(bytes_value):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def pluralize(count, singular, plural=None):
    """Return a count with the correct singular/plural noun."""
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"


def get_root_node(jsonld_data):
    """Return the main TRO node from a JSON-LD document."""
    graph = jsonld_data.get("@graph", [])
    for node in graph:
        if not isinstance(node, dict):
            continue
        node_type = node.get("@type", [])
        if isinstance(node_type, str):
            node_type = [node_type]
        if "trov:TransparentResearchObject" in node_type or node.get("@id") == "tro":
            return node
    return graph[0] if graph and isinstance(graph[0], dict) else {}


def clean_comment(comment):
    """Remove extra spacing from TRO comment strings."""
    return re.sub(r"\s+", " ", comment or "").strip()


def clean_step_label(comment):
    """Convert SIVACOR step labels into simpler human-readable text."""
    label = clean_comment(comment)
    match = re.match(r"SIVACOR workflow execution \((.+)\) step (\d+)", label)
    if match:
        return f"`{match.group(1)}` (step {match.group(2)})"
    return f"`{label}`" if label else "the recorded workflow step"


def artifact_reference(location):
    """Return the artifact ID referenced by an arrangement location."""
    artifact = location.get("trov:artifact", {})
    if isinstance(artifact, dict):
        return artifact.get("@id", "")
    return artifact if isinstance(artifact, str) else ""


def artifact_hash(artifact):
    """Return a stable hash string for an artifact, if present."""
    hash_info = artifact.get("trov:hash", {})
    if isinstance(hash_info, dict):
        algorithm = hash_info.get("trov:hashAlgorithm", "")
        value = hash_info.get("trov:hashValue", "")
        return f"{algorithm}:{value}" if algorithm and value else value
    return ""


def build_artifact_map(root):
    """Map artifact IDs to metadata."""
    composition = root.get("trov:hasComposition", {})
    artifacts = composition.get("trov:hasArtifact", [])
    if isinstance(artifacts, dict):
        artifacts = [artifacts]

    artifact_map = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_id = artifact.get("@id", "")
        if artifact_id:
            artifact_map[artifact_id] = {
                "hash": artifact_hash(artifact),
                "mime": artifact.get("trov:mimeType", ""),
            }
    return artifact_map


def arrangement_path_map(arrangement, artifact_map):
    """Return path -> artifact metadata for one arrangement."""
    locations = arrangement.get("trov:hasArtifactLocation", [])
    if isinstance(locations, dict):
        locations = [locations]

    paths = {}
    for location in locations:
        if not isinstance(location, dict):
            continue
        path = location.get("trov:path")
        if not path:
            continue
        artifact_id = artifact_reference(location)
        metadata = artifact_map.get(artifact_id, {}).copy()
        metadata["artifact_id"] = artifact_id
        paths[path] = metadata
    return paths


def compare_arrangements(before, after):
    """Compare two TRO arrangements by path and artifact hash."""
    before_paths = set(before)
    after_paths = set(after)
    shared = before_paths & after_paths

    changed = []
    for path in sorted(shared):
        before_hash = before[path].get("hash", "")
        after_hash = after[path].get("hash", "")
        if before_hash and after_hash and before_hash != after_hash:
            changed.append(path)

    return {
        "added": sorted(after_paths - before_paths),
        "removed": sorted(before_paths - after_paths),
        "changed": changed,
        "unchanged": sorted(shared - set(changed)),
    }


def top_level_counter(paths):
    """Count paths by their top-level directory/file."""
    counts = Counter()
    for path in paths:
        first = path.split("/", 1)[0]
        counts[first] += 1
    return counts


def format_counter(counter, limit=8):
    """Format a counter compactly for Markdown prose."""
    if not counter:
        return "none"
    pieces = [f"{name} ({count})" for name, count in counter.most_common(limit)]
    remaining = len(counter) - limit
    if remaining > 0:
        pieces.append(f"{remaining} other top-level paths")
    return ", ".join(pieces)


def format_path_examples(paths, limit=12):
    """Format a bounded list of path examples."""
    if not paths:
        return ""
    examples = paths[:limit]
    output = [f"    - `{path}`" for path in examples]
    remaining = len(paths) - len(examples)
    if remaining > 0:
        output.append(f"    - ... and {pluralize(remaining, 'additional path')}")
    return "\n".join(output)


def format_duration_from_info(info):
    """Return a human-readable duration from performance timestamps."""
    if "StartedAt" not in info or "FinishedAt" not in info:
        return ""
    try:
        started = datetime.fromisoformat(info["StartedAt"].replace("Z", "+00:00"))
        finished = datetime.fromisoformat(info["FinishedAt"].replace("Z", "+00:00"))
        total_seconds = int((finished - started).total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    except Exception:
        return ""


def read_text_file(path):
    """Read a UTF-8-ish text file defensively."""
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def count_pattern(text, pattern):
    """Count regex matches in text, case-insensitively."""
    if not text:
        return 0
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def sample_matches(text, pattern, limit=3):
    """Return a few matching lines for a regex."""
    if not text:
        return []
    matches = []
    regex = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
    for line in text.splitlines():
        if regex.search(line):
            cleaned = line.strip()
            if cleaned and cleaned not in matches:
                matches.append(cleaned)
        if len(matches) >= limit:
            break
    return matches


def sample_priority_matches(text, patterns, limit=4):
    """Return a few matching lines, prioritizing more specific patterns first."""
    results = []
    for pattern in patterns:
        for match in sample_matches(text, pattern, limit=limit):
            if match not in results:
                results.append(match)
            if len(results) >= limit:
                return results
    return results


def assess_logs(stdout_text, stderr_text):
    """Classify the apparent run outcome from stdout/stderr."""
    combined = "\n".join(part for part in [stdout_text, stderr_text] if part)

    fatal_patterns = [
        r"traceback",
        r"execution halted",
        r"returned non-zero",
        r"^error:",
        r"^r\([1-9][0-9]*\)",
        r"command .* (unknown|unrecognized|not found)",
    ]
    warning_patterns = [
        r"warning",
        r"cannot open the connection",
        r"cannot be opened",
        r"no observations",
        r"file .* not found$",
    ]
    success_patterns = [
        r"end of do-file",
        r"Ran .* successfully",
        r"Successfully installed",
    ]

    fatal_count = sum(count_pattern(combined, pattern) for pattern in fatal_patterns)
    warning_count = sum(count_pattern(combined, pattern) for pattern in warning_patterns)
    success_count = sum(count_pattern(combined, pattern) for pattern in success_patterns)

    if fatal_count > 0 and success_count == 0:
        status = "likely_failed"
    elif fatal_count > 0 and success_count > 0:
        status = "completed_with_possible_issues"
    elif warning_count > 0:
        status = "completed_with_warnings"
    elif success_count > 0:
        status = "completed_cleanly"
    else:
        status = "unclear"

    return {
        "status": status,
        "fatal_count": fatal_count,
        "warning_count": warning_count,
        "success_count": success_count,
        "warning_examples": sample_priority_matches(
            combined,
            [
                r"cannot open the connection",
                r"cannot be opened",
                r"there were [0-9]+ warnings",
                r"no observations",
                r"warning message:",
                r"warning messages:",
            ],
            limit=4,
        ),
        "fatal_examples": sample_matches(combined, r"traceback|execution halted|returned non-zero|^error:|^r\([1-9][0-9]*\)|command .* (unknown|unrecognized|not found)", limit=4),
    }


def extract_log_assessment(jobid=None, jsonld_file=None, search_dir="."):
    """Find and assess stdout/stderr logs for a SIVACOR run."""
    stdout_path = find_log_file("stdout", jobid=jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    stderr_path = find_log_file("stderr", jobid=jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    stdout_text = read_text_file(stdout_path)
    stderr_text = read_text_file(stderr_path)

    assessment = assess_logs(stdout_text, stderr_text)
    assessment["stdout_path"] = stdout_path
    assessment["stderr_path"] = stderr_path
    return assessment


def extract_computing_info(jsonld_data):
    """Extract computing information from JSONLD data.
    
    Returns a list of dicts, one per performance, each containing all
    sivacor: fields plus '_id' and '_comment' metadata keys.
    """
    performances = []
    graph = jsonld_data.get("@graph", [])

    # Prefer structured extraction from trov:hasPerformance
    for node in graph:
        if isinstance(node, dict) and "trov:hasPerformance" in node:
            perfs = node["trov:hasPerformance"]
            if not isinstance(perfs, list):
                perfs = [perfs]
            for perf in perfs:
                info = {}
                info["_id"] = perf.get("@id", "")
                info["_comment"] = perf.get("rdfs:comment", "")
                for key, value in perf.items():
                    if key.startswith("sivacor:"):
                        info[key.replace("sivacor:", "")] = value
                performances.append(info)
            break

    # Fallback: recursive extraction (single performance, old behaviour)
    if not performances:
        info = {}

        def extract_from_dict(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if key.startswith("sivacor:"):
                        clean_key = key.replace("sivacor:", "")
                        if clean_key not in info:
                            info[clean_key] = value
                    elif isinstance(value, dict):
                        extract_from_dict(value)
                    elif isinstance(value, list):
                        for item in value:
                            extract_from_dict(item)
            elif isinstance(d, list):
                for item in d:
                    extract_from_dict(item)

        extract_from_dict(graph)
        if info:
            performances.append(info)

    return performances


def _format_single_computing(info, jobid=None):
    """Format a single performance's computing information."""
    output = []

    # SIVACOR Job ID
    if jobid:
        output.append(f"- SIVACOR Job ID: `{jobid}`")

    # Processor
    if "Processor" in info:
        output.append(f"- Processor: {info['Processor']}")

    # Number of CPUs
    if "NCPU" in info:
        output.append(f"- CPUs: {info['NCPU']}")

    # Total Memory
    if "MemTotal" in info:
        mem_gb = info['MemTotal'] / (1024**3)
        output.append(f"- Total Memory: {mem_gb:.1f} GB")

    # Operating System
    if "OperatingSystem" in info:
        os_str = info['OperatingSystem']
        if "OSVersion" in info:
            os_str += f" (Version {info['OSVersion']})"
        output.append(f"- Operating System: {os_str}")

    # Kernel Version
    if "KernelVersion" in info:
        output.append(f"- Kernel Version: {info['KernelVersion']}")

    # Docker Image
    if "ImageRepoTags" in info:
        tags = info['ImageRepoTags']
        if isinstance(tags, list) and tags:
            output.append(f"- Docker Image: `{tags[0]}`")

    # Max CPU Usage
    if "MaxCPUPercent" in info:
        output.append(f"- Max CPU Usage: {info['MaxCPUPercent']:.2f}%")

    # Max Memory Usage
    if "MaxMemoryUsage" in info:
        mem_used = bytes_to_human_readable(info['MaxMemoryUsage'])
        output.append(f"- Max Memory Usage: {mem_used}")

    # OS Type
    if "OSType" in info and "OSType" not in str(output):
        output.append(f"- OS Type: {info['OSType']}")

    return "\n".join(output)


def format_computing_info(performances, jobid=None):
    """Format computing information for all performances."""
    if not performances:
        return ""

    if len(performances) == 1:
        return _format_single_computing(performances[0], jobid)

    sections = []
    for i, info in enumerate(performances):
        comment = info.get("_comment", "")
        header = f"*Performance {i + 1}*" + (f": {comment}" if comment else "")
        body = _format_single_computing(info, jobid)
        sections.append(header + "\n" + body)

    return "\n\n".join(sections)


def _format_single_time(info, jobid=None):
    """Format timing information for a single performance."""
    output = []

    # SIVACOR Job ID
    if jobid:
        output.append(f"- SIVACOR Job ID: `{jobid}`")

    # Started At
    if "StartedAt" in info:
        output.append(f"- Started: {info['StartedAt']}")

    # Finished At
    if "FinishedAt" in info:
        output.append(f"- Finished: {info['FinishedAt']}")

    duration_str = format_duration_from_info(info)
    if duration_str:
        output.append(f"- Duration: {duration_str}")

    return "\n".join(output)


def format_time_info(performances, jobid=None):
    """Format timing information for all performances."""
    if not performances:
        return ""

    if len(performances) == 1:
        return _format_single_time(performances[0], jobid)

    sections = []
    for i, info in enumerate(performances):
        comment = info.get("_comment", "")
        header = f"*Performance {i + 1}*" + (f": {comment}" if comment else "")
        body = _format_single_time(info, jobid)
        sections.append(header + "\n" + body)

    return "\n\n".join(sections)


def format_step_summary(performances, jobid=None):
    """Format SIVACOR workflow steps for a Part B narrative."""
    output = []
    for i, info in enumerate(performances, start=1):
        comment = clean_comment(info.get("_comment", "")) or f"SIVACOR workflow step {i}"
        image = ""
        tags = info.get("ImageRepoTags")
        if isinstance(tags, list) and tags:
            image = tags[0]

        duration = format_duration_from_info(info)

        details = []
        if image:
            details.append(f"Docker image `{image}`")
        if duration:
            details.append(f"duration {duration}")
        if info.get("MaxMemoryUsage"):
            details.append(f"maximum memory {bytes_to_human_readable(info['MaxMemoryUsage'])}")

        suffix = f" ({'; '.join(details)})" if details else ""
        output.append(f"- Step {i}: {comment}{suffix}.")

    if not output and jobid:
        output.append(f"- SIVACOR Job ID: `{jobid}`.")
    return "\n".join(output)


def format_environment_sentence(performances):
    """Return a compact environment sentence for Part B."""
    if not performances:
        return ""

    first = performances[0]
    processor = first.get("Processor", "the SIVACOR processor")
    ncpu = first.get("NCPU")
    mem_total = first.get("MemTotal")
    os_name = first.get("OperatingSystem")

    pieces = []
    if processor:
        pieces.append(str(processor))
    if ncpu:
        pieces.append(f"{ncpu} CPUs")
    if mem_total:
        pieces.append(f"{mem_total / (1024 ** 3):.1f} GB memory")
    if os_name:
        pieces.append(str(os_name))

    images = []
    for info in performances:
        tags = info.get("ImageRepoTags")
        if isinstance(tags, list) and tags:
            images.append(tags[0])
    images = list(dict.fromkeys(images))
    image_text = ", ".join(f"`{image}`" for image in images)

    sentence = "The SIVACOR run used " + ", ".join(pieces) + "."
    if image_text:
        sentence += f" The workflow used container image(s): {image_text}."
    return sentence


def extract_tro_summary(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Extract the TRO details needed for an automated Part B summary."""
    root = get_root_node(jsonld_data)
    artifact_map = build_artifact_map(root)
    arrangements = root.get("trov:hasArrangement", [])
    if isinstance(arrangements, dict):
        arrangements = [arrangements]

    arrangement_infos = []
    for arrangement in arrangements:
        if not isinstance(arrangement, dict):
            continue
        paths = arrangement_path_map(arrangement, artifact_map)
        arrangement_infos.append({
            "id": arrangement.get("@id", ""),
            "comment": clean_comment(arrangement.get("rdfs:comment", "")),
            "paths": paths,
        })

    performances = extract_computing_info(jsonld_data)
    log_assessment = extract_log_assessment(jobid=jobid, jsonld_file=jsonld_file, search_dir=search_dir)

    return {
        "jobid": jobid,
        "name": root.get("schema:name", ""),
        "description": root.get("schema:description", ""),
        "date_created": root.get("schema:dateCreated", ""),
        "creator": root.get("schema:creator", ""),
        "created_with": root.get("trov:createdWith", {}),
        "vocabulary_version": root.get("trov:vocabularyVersion", ""),
        "arrangements": arrangement_infos,
        "performances": performances,
        "artifact_count": len(artifact_map),
        "log_assessment": log_assessment,
    }


def format_partb_summary(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Format a SIVACOR TRO as a Part B-ready Markdown summary."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    arrangements = summary["arrangements"]
    performances = summary["performances"]
    log_assessment = summary["log_assessment"]

    output = []
    output.append("**SIVACOR automated execution summary**")
    output.append("")

    if jobid:
        output.append(f"- This repository was submitted as a SIVACOR-generated repository under job ID `{jobid}`. The code was already executed by SIVACOR and was not rerun by the AEA reviewer.")
    else:
        output.append("- This repository was submitted as a SIVACOR-generated repository. The code was already executed by SIVACOR and was not rerun by the AEA reviewer.")

    environment = format_environment_sentence(performances)
    if environment:
        output.append(f"- {environment} SIVACOR recorded {pluralize(len(performances), 'workflow execution step')} in this TRO.")

    status_map = {
        "completed_cleanly": "The available SIVACOR logs suggest that the workflow completed without obvious execution errors.",
        "completed_with_warnings": "The available SIVACOR logs suggest that the workflow completed, but there were warnings or other non-fatal issues that should be reviewed.",
        "completed_with_possible_issues": "The available SIVACOR logs suggest that the workflow reached later steps, but there were issue signals in the logs that may indicate partial problems.",
        "likely_failed": "The available SIVACOR logs contain error signals without clear completion markers, so the run may have failed or stopped early.",
        "unclear": "The available SIVACOR logs do not provide enough information to classify the run outcome confidently.",
    }
    output.append(f"- {status_map.get(log_assessment['status'], status_map['unclear'])}")

    issue_examples = log_assessment["fatal_examples"] or log_assessment["warning_examples"]
    if issue_examples:
        rendered = "; ".join(f"`{example}`" for example in issue_examples[:3])
        output.append(f"- Log highlights: {rendered}.")

    if log_assessment["status"] == "completed_cleanly":
        output.append("- No manual intervention by the AEA reviewer is recorded in this SIVACOR-generated repository. In this workflow, Part B records execution status and observed issues during execution based on the SIVACOR TRO and associated stdout/stderr logs; it is not an exhaustive assessment of code correctness or replication success. Part C remains the human review of whether the deposited outputs match the manuscript and whether the code behavior is substantively correct.")
    elif log_assessment["status"] in {"completed_with_warnings", "completed_with_possible_issues", "likely_failed"}:
        output.append("- The TRO and logs do not show AEA-side code intervention, but the warning/error signals above should be reviewed to determine whether the SIVACOR run was fully successful, only partially successful, or produced outputs with caveats. In this workflow, Part B records execution status and observed issues during execution based on the SIVACOR TRO and associated stdout/stderr logs; it is not an exhaustive assessment of code correctness or replication success. Part C remains the human review of whether the deposited outputs match the manuscript and whether the code behavior is substantively correct.")

    if len(arrangements) >= 2 and performances:
        for i, info in enumerate(performances):
            before = arrangements[i] if i < len(arrangements) else None
            after = arrangements[i + 1] if i + 1 < len(arrangements) else None
            diff = compare_arrangements(before["paths"], after["paths"]) if before and after else {"added": [], "removed": [], "changed": []}
            step_comment = clean_step_label(info.get("_comment", "")) if info.get("_comment") else f"workflow step {i + 1}"
            tags = info.get("ImageRepoTags")
            image = tags[0] if isinstance(tags, list) and tags else ""
            duration = format_duration_from_info(info)
            mem = bytes_to_human_readable(info["MaxMemoryUsage"]) if info.get("MaxMemoryUsage") else ""

            sentence = f"- Step {i + 1} ran {step_comment}"
            if image:
                sentence += f" in Docker image `{image}`"
            if before and after:
                sentence += f", using the \"{before['comment']}\" arrangement ({len(before['paths'])} paths) and producing the \"{after['comment']}\" arrangement ({len(after['paths'])} paths)"
            details = []
            if duration:
                details.append(f"duration {duration}")
            if mem:
                details.append(f"maximum memory {mem}")
            if details:
                sentence += f" ({'; '.join(details)})"
            sentence += "."
            output.append(sentence)

            added_counter = format_counter(top_level_counter(diff["added"]))
            output.append(f"- Step {i + 1} recorded {pluralize(len(diff['added']), 'new path')}, {pluralize(len(diff['removed']), 'removed path')}, and {pluralize(len(diff['changed']), 'modified path')}. New paths were concentrated in {added_counter}.")

            example_paths = diff["added"][:4]
            if example_paths:
                rendered = ", ".join(f"`{path}`" for path in example_paths)
                output.append(f"- Examples from step {i + 1}: {rendered}.")

    output.append("- Part C should compare the output files deposited through SIVACOR with the tables, figures, and other results reported in the manuscript, and should evaluate whether any warnings or possible bugs affected substantive code behavior.")

    return "\n".join(output)


def arrangement_sort_key(arrangement):
    """Sort arrangements by their numeric TRO ID when possible."""
    match = re.search(r"/(\d+)$", arrangement.get("id", ""))
    if match:
        return int(match.group(1))
    return 0


def format_output_examples(paths, limit=8):
    """Format output path examples for concise report prose."""
    if not paths:
        return "none recorded"
    examples = paths[:limit]
    rendered = ", ".join(f"`{path}`" for path in examples)
    remaining = len(paths) - len(examples)
    if remaining > 0:
        rendered += f", and {pluralize(remaining, 'additional path')}"
    return rendered


def format_sivacor_environment(summary):
    """Format the computing environment block for a SIVACOR Part B file."""
    performances = summary["performances"]
    if not performances:
        return "- SIVACOR execution environment information was not found in the TRO."

    first = performances[0]
    lines = []
    if summary["jobid"]:
        lines.append(f"- SIVACOR Job ID: `{summary['jobid']}`")
    if first.get("Processor"):
        lines.append(f"- Processor: {first['Processor']}")
    if first.get("NCPU"):
        lines.append(f"- CPUs: {first['NCPU']}")
    if first.get("MemTotal"):
        lines.append(f"- Total memory: {first['MemTotal'] / (1024 ** 3):.1f} GB")
    if first.get("OperatingSystem"):
        os_text = first["OperatingSystem"]
        if first.get("OSVersion"):
            os_text += f" (Version {first['OSVersion']})"
        lines.append(f"- Operating system: {os_text}")
    if first.get("KernelVersion"):
        lines.append(f"- Kernel version: {first['KernelVersion']}")

    images = []
    for info in performances:
        tags = info.get("ImageRepoTags")
        if isinstance(tags, list) and tags:
            images.append(tags[0])
    images = list(dict.fromkeys(images))
    if images:
        lines.append("- Container image(s): " + ", ".join(f"`{image}`" for image in images))

    return "\n".join(lines)


def format_sivacor_steps(summary):
    """Format what SIVACOR actually ran for Replication steps."""
    performances = summary["performances"]
    if not performances:
        return "- The TRO did not contain workflow performance records."

    output = []
    for i, info in enumerate(performances, start=1):
        label = clean_step_label(info.get("_comment", ""))
        tags = info.get("ImageRepoTags")
        image = tags[0] if isinstance(tags, list) and tags else ""
        duration = format_duration_from_info(info)
        parts = [f"- Step {i}: SIVACOR ran {label}"]
        if image:
            parts.append(f"in container `{image}`")
        if duration:
            parts.append(f"for {duration}")
        output.append(" ".join(parts) + ".")
    return "\n".join(output)


def format_sivacor_findings(summary):
    """Format arrangement 0 vs final arrangement changes for Findings."""
    arrangements = sorted(summary["arrangements"], key=arrangement_sort_key)
    if len(arrangements) < 2:
        return "- The TRO did not contain enough arrangements to compare initial and final file states."

    initial = arrangements[0]
    final = arrangements[-1]
    diff = compare_arrangements(initial["paths"], final["paths"])

    output_paths = [path for path in diff["added"] if path.startswith("output/")]
    table_paths = [path for path in output_paths if path.startswith("output/Tables/")]
    figure_paths = [path for path in output_paths if path.startswith("output/Figures/")]
    log_paths = [path for path in diff["added"] if path.startswith("logs/") or path.endswith(".log")]
    data_paths = [path for path in diff["added"] if path.startswith("data/")]

    lines = []
    initial_label = initial["comment"] or initial["id"] or "arrangement 0"
    final_label = final["comment"] or final["id"] or "final arrangement"
    lines.append(f"- Compared `{initial_label}` with `{final_label}`, the highest arrangement available in the TRO.")
    lines.append(f"- Initial arrangement: {pluralize(len(initial['paths']), 'path')}. Final arrangement: {pluralize(len(final['paths']), 'path')}.")
    lines.append(f"- SIVACOR recorded {pluralize(len(diff['added']), 'new path')}, {pluralize(len(diff['removed']), 'removed path')}, and {pluralize(len(diff['changed']), 'modified path')} between the initial and final arrangements.")
    lines.append(f"- New paths were concentrated in {format_counter(top_level_counter(diff['added']))}.")
    lines.append(f"- Generated output paths included {pluralize(len(output_paths), 'path')}: {pluralize(len(table_paths), 'table path')}, {pluralize(len(figure_paths), 'figure path')}.")
    if data_paths:
        lines.append(f"- SIVACOR also recorded {pluralize(len(data_paths), 'new data/intermediate path')} and {pluralize(len(log_paths), 'new log path')}.")
    lines.append("- The full SIVACOR arrangement comparison is listed in the Appendix.")
    lines.append("- SIVACOR is used here to document execution and generated files. It is not designed to compare figures and tables against the manuscript; that comparison remains part of Findings/Part C review.")
    return "\n".join(lines)


def format_appendix_path_group(title, paths):
    """Format a full appendix path list."""
    lines = [f"#### {title}", ""]
    if not paths:
        lines.append("- None recorded.")
        return "\n".join(lines)
    for path in paths:
        lines.append(f"- `{path}`")
    return "\n".join(lines)


def format_sivacor_appendix(summary):
    """Format full SIVACOR arrangement comparison details for the appendix."""
    arrangements = sorted(summary["arrangements"], key=arrangement_sort_key)
    if len(arrangements) < 2:
        return "### SIVACOR arrangement comparison\n\nThe TRO did not contain enough arrangements to compare initial and final file states."

    initial = arrangements[0]
    final = arrangements[-1]
    diff = compare_arrangements(initial["paths"], final["paths"])

    output_paths = [path for path in diff["added"] if path.startswith("output/")]
    table_paths = [path for path in output_paths if path.startswith("output/Tables/")]
    figure_paths = [path for path in output_paths if path.startswith("output/Figures/")]
    other_output_paths = sorted(set(output_paths) - set(table_paths) - set(figure_paths))
    data_paths = [path for path in diff["added"] if path.startswith("data/")]
    log_paths = [path for path in diff["added"] if path.startswith("logs/") or path.endswith(".log")]
    renv_paths = [path for path in diff["added"] if path.startswith("renv/")]
    categorized = set(output_paths) | set(data_paths) | set(log_paths) | set(renv_paths)
    other_new_paths = [path for path in diff["added"] if path not in categorized]

    initial_label = initial["comment"] or initial["id"] or "arrangement 0"
    final_label = final["comment"] or final["id"] or "final arrangement"

    sections = []
    sections.append("### SIVACOR arrangement comparison")
    sections.append("")
    sections.append(f"SIVACOR arrangement comparison from `{initial_label}` to `{final_label}`.")
    sections.append("")
    sections.append(f"- Initial arrangement: {pluralize(len(initial['paths']), 'path')}.")
    sections.append(f"- Final arrangement: {pluralize(len(final['paths']), 'path')}.")
    sections.append(f"- New paths: {len(diff['added'])}.")
    sections.append(f"- Removed paths: {len(diff['removed'])}.")
    sections.append(f"- Modified paths: {len(diff['changed'])}.")
    sections.append("")
    sections.append(format_appendix_path_group("Generated table output paths", table_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Generated figure output paths", figure_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Other generated output paths", other_output_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Generated data/intermediate paths", data_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Generated log paths", log_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Generated R environment paths", renv_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Other new paths", other_new_paths))
    sections.append("")
    sections.append(format_appendix_path_group("Removed paths", diff["removed"]))
    sections.append("")
    sections.append(format_appendix_path_group("Modified paths", diff["changed"]))
    return "\n".join(sections)


def format_sivacor_replication_steps_insert(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Generate only the SIVACOR text to insert in Replication steps."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    output = []
    output.append("- [x] The reproducibility check was conducted by a trusted third-party; SIVACOR executed the submitted workflow and produced the TRO execution record.")
    output.append("")
    output.append("SIVACOR recorded the following workflow steps:")
    output.append("")
    output.append(format_sivacor_steps(summary))
    return "\n".join(output)


def format_sivacor_computing_environment_insert(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Generate only the SIVACOR text to insert in Computing Environment."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    output = []
    output.append("- [x] The reproducibility check was conducted by a trusted third-party; SIVACOR executed the submitted workflow and produced the TRO execution record.")
    output.append("")
    output.append("The AEA reviewer did not rerun the author code. The SIVACOR TRO records the following execution environment:")
    output.append("")
    output.append(format_sivacor_environment(summary))
    return "\n".join(output)


def format_sivacor_findings_insert(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Generate only the SIVACOR-generated files finding."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    output = []
    output.append("### SIVACOR-generated files")
    output.append("")
    output.append(format_sivacor_findings(summary))
    return "\n".join(output)


def format_sivacor_appendix_insert(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Generate the SIVACOR appendix section."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)
    return format_sivacor_appendix(summary)


def format_partb_sivacor(jsonld_data, jobid=None, jsonld_file=None, search_dir="."):
    """Generate a full SIVACOR-specific Part B Markdown file."""
    summary = extract_tro_summary(jsonld_data, jobid, jsonld_file=jsonld_file, search_dir=search_dir)

    output = []
    output.append("> INSTRUCTIONS: ==> Workflow stage: You are starting *PartB*. This Part B was generated for a SIVACOR-submitted repository.")
    output.append("")
    output.append("## All data files provided")
    output.append("")
    output.append("The submitted repository was generated by SIVACOR and includes a TRO directory documenting the SIVACOR execution record. Refer to the repository README and openICPSR deposit materials for package-level data documentation and any missing requirements.")
    output.append("")
    output.append("## Stated Requirements")
    output.append("")
    output.append("For SIVACOR-submitted repositories, stated software and computational requirements should be checked against the README and any author-provided documentation. SIVACOR records the execution environment used for the submitted run, but does not replace review of the authors' stated requirements.")
    output.append("")
    output.append("For missing requirements, see the list of required changes in the **[FINDINGS](#findings)** section.")
    output.append("")
    output.append("## Code description")
    output.append("")
    output.append("The package was submitted as a SIVACOR-generated repository. SIVACOR records which workflow steps were executed, but it is not designed to classify or compare manuscript figures and tables. Human review should use the README, source code, and generated outputs to map manuscript results to code and output files.")
    output.append("")
    output.append("## Computing Environment of the Replicator")
    output.append("")
    output.append("The code was run by SIVACOR. The AEA reviewer did not rerun the code.")
    output.append("")
    output.append(format_sivacor_environment(summary))
    output.append("")
    output.append("## Replication steps")
    output.append("")
    output.append("- [x] The reproducibility check was conducted by a trusted third-party; SIVACOR executed the submitted workflow and produced the TRO execution record.")
    output.append("")
    output.append("SIVACOR recorded the following workflow steps:")
    output.append("")
    output.append(format_sivacor_steps(summary))
    output.append("")
    output.append("## Findings")
    output.append("")
    output.append("### SIVACOR-generated files")
    output.append("")
    output.append(format_sivacor_findings(summary))
    output.append("")
    output.append("### Missing Requirements")
    output.append("")
    output.append("Refer to the README and author-provided package documentation for missing or incomplete software, package, operating-system, and computational requirements. SIVACOR records the environment used for its run, but does not by itself determine whether the README fully documented all requirements.")
    output.append("")
    output.append("### Figure, table, and code-behavior review")
    output.append("")
    output.append("SIVACOR is not designed to compare figures and tables against the manuscript. Human review should compare the generated outputs in the openICPSR deposit with the manuscript tables, figures, and in-text results, and should evaluate whether code behavior is substantively correct.")
    output.append("")
    output.append("## Classification")
    output.append("")
    output.append("Classification remains a human review task after comparing the SIVACOR-generated outputs with the manuscript and assessing any missing requirements.")

    return "\n".join(output)


def parse_jsonld(jsonld_file, keyword, jobid=None):
    """Parse JSONLD file and extract information based on keyword."""
    try:
        with open(jsonld_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{jsonld_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    if keyword == "computing":
        performances = extract_computing_info(data)
        if not performances:
            print("No computing information found in JSONLD file.", file=sys.stderr)
            sys.exit(1)
        return format_computing_info(performances, jobid)
    elif keyword == "time":
        performances = extract_computing_info(data)
        if not performances:
            print("No timing information found in JSONLD file.", file=sys.stderr)
            sys.exit(1)
        return format_time_info(performances, jobid)
    elif keyword == "partb":
        return format_partb_summary(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    elif keyword == "partb-sivacor":
        return format_partb_sivacor(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    elif keyword == "sivacor-computing-environment":
        return format_sivacor_computing_environment_insert(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    elif keyword == "sivacor-replication-steps":
        return format_sivacor_replication_steps_insert(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    elif keyword == "sivacor-findings":
        return format_sivacor_findings_insert(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    elif keyword == "sivacor-appendix":
        return format_sivacor_appendix_insert(data, jobid, jsonld_file=jsonld_file, search_dir=os.path.dirname(os.path.abspath(jsonld_file)) or ".")
    else:
        print(f"Error: Unknown keyword '{keyword}'. Supported keywords: {', '.join(SUPPORTED_KEYWORDS)}", file=sys.stderr)
        sys.exit(1)


def update_report_computing(report_file, sivacor_info, dry_run=False):
    """Update the report file with SIVACOR computing information."""
    try:
        with open(report_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Report file '{report_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Look for "Computing Environment of the Replicator" section
    pattern = r'(## Computing Environment of the Replicator\n\n)((?:- .*\n)*)'
    
    # Check if SIVACOR section already exists
    if re.search(r'\*\*SIVACOR\*\*', content):
        print("⚠️  WARNING: SIVACOR computing section already exists in report.", file=sys.stderr)
        print("\nExisting information in Markdown notation:\n", file=sys.stderr)
        print("**SIVACOR**\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return False
    
    # Build the SIVACOR section
    sivacor_section = f"\n**SIVACOR**\n\n{sivacor_info}\n\n"
    
    # Insert SIVACOR section after existing computing environment items
    def replace_func(match):
        return match.group(1) + match.group(2) + sivacor_section
    
    new_content = re.sub(pattern, replace_func, content)
    
    if new_content == content:
        print("Could not find 'Computing Environment of the Replicator' section in report.", file=sys.stderr)
        return False
    
    if dry_run:
        print("DRY RUN: Would add the following to the report:\n", file=sys.stderr)
        print("**SIVACOR**\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return True
    
    # Write the updated content
    with open(report_file, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully updated {report_file} with SIVACOR computing information.", file=sys.stderr)
    return True


def update_report_time(report_file, sivacor_info, dry_run=False):
    """Update the report file with SIVACOR timing information."""
    try:
        with open(report_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Report file '{report_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Look for "## Findings" section
    # Match ## Findings followed by any content until we find instructions or another section
    pattern = r'(## Findings\n\n)((?:> INSTRUCTIONS:.*\n)*(?:> INSTRUCTIONS:.*\n\n)*)'
    
    # Check if SIVACOR timing section already exists
    if re.search(r'\*\*SIVACOR Execution Time\*\*', content):
        print("⚠️  WARNING: SIVACOR timing section already exists in report.", file=sys.stderr)
        print("\nExisting information in Markdown notation:\n", file=sys.stderr)
        print("**SIVACOR Execution Time**\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return False
    
    # Build the SIVACOR timing section
    sivacor_section = f"**SIVACOR Execution Time**\n\n{sivacor_info}\n\n"
    
    # Insert SIVACOR section after the Findings heading and instructions
    def replace_func(match):
        return match.group(1) + match.group(2) + sivacor_section
    
    new_content = re.sub(pattern, replace_func, content)
    
    if new_content == content:
        print("Could not find 'Findings' section in report.", file=sys.stderr)
        return False
    
    if dry_run:
        print("DRY RUN: Would add the following to the report:\n", file=sys.stderr)
        print("**SIVACOR Execution Time**\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return True
    
    # Write the updated content
    with open(report_file, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully updated {report_file} with SIVACOR timing information.", file=sys.stderr)
    return True


def update_report_partb(report_file, sivacor_info, dry_run=False):
    """Update the report file with a SIVACOR Part B summary."""
    try:
        with open(report_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Report file '{report_file}' not found.", file=sys.stderr)
        sys.exit(1)

    if re.search(r'\*\*SIVACOR automated execution summary\*\*', content):
        print("WARNING: SIVACOR Part B summary already exists in report.", file=sys.stderr)
        print("\nExisting information in Markdown notation:\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return False

    pattern = r'(## Replication steps\n\n)((?:> INSTRUCTIONS:.*\n|> .*\n|\n)*)'
    new_section = f"{sivacor_info}\n\n"

    def replace_func(match):
        return match.group(1) + match.group(2) + new_section

    new_content = re.sub(pattern, replace_func, content, count=1)

    if new_content == content:
        print("Could not find 'Replication steps' section in report.", file=sys.stderr)
        return False

    if dry_run:
        print("DRY RUN: Would add the following to the report:\n", file=sys.stderr)
        print(sivacor_info, file=sys.stderr)
        return True

    with open(report_file, 'w') as f:
        f.write(new_content)

    print(f"Successfully updated {report_file} with SIVACOR Part B summary.", file=sys.stderr)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Parse SIVACOR JSONLD files for information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.jsonld computing
  %(prog)s --jsonld file.jsonld --key computing
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key computing
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key time
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key partb
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key partb-sivacor --output generated/REPLICATION-PartB-SIVACOR.md
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key computing --report REPLICATION-PartB.md
  %(prog)s --jobid 69cede1db3a6af67b1c01c3d --key time --report REPLICATION-PartB.md --dry-run
        """
    )
    
    parser.add_argument('jsonld_file', nargs='?', 
                        help='Path to JSONLD file (positional argument)')
    parser.add_argument('keyword', nargs='?',
                        help=f"Information keyword (positional argument): {', '.join(SUPPORTED_KEYWORDS)}")
    parser.add_argument('--jsonld', dest='jsonld_opt',
                        help='Path to JSONLD file (option)')
    parser.add_argument('--jobid', 
                        help='SIVACOR job ID (will search for tro-{jobid}.jsonld)')
    parser.add_argument('--key', dest='key_opt',
                        help=f"Information keyword (option): {', '.join(SUPPORTED_KEYWORDS)}")
    parser.add_argument('--report',
                        help='Report file to update with SIVACOR information')
    parser.add_argument('--output',
                        help='Write generated Markdown to this file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print output without modifying the report file')
    
    args = parser.parse_args()
    
    # Determine jsonld file
    jsonld = None
    jobid = None
    if args.jsonld_opt:
        jsonld = args.jsonld_opt
        match = re.search(r'tro-([a-f0-9]+)\.jsonld', jsonld)
        if match:
            jobid = match.group(1)
    elif args.jobid:
        jobid = args.jobid
        jsonld = find_jsonld_by_jobid(args.jobid)
        if not jsonld:
            print(f"Error: Could not find JSONLD file for job ID '{args.jobid}'", file=sys.stderr)
            sys.exit(1)
    elif args.jsonld_file:
        jsonld = args.jsonld_file
        # Try to extract job ID from filename
        match = re.search(r'tro-([a-f0-9]+)\.jsonld', jsonld)
        if match:
            jobid = match.group(1)
    else:
        parser.error("Must provide either positional jsonld_file, --jsonld, or --jobid")
    
    # Determine keyword
    keyword = None
    if args.key_opt:
        keyword = args.key_opt
    elif args.keyword:
        keyword = args.keyword
    else:
        parser.error("Must provide keyword either as positional argument or via --key")
    
    result = parse_jsonld(jsonld, keyword, jobid)
    
    if args.output:
        if args.dry_run:
            print("DRY RUN: Would write the following to " + args.output + ":\n", file=sys.stderr)
            print(result)
        else:
            with open(args.output, 'w') as f:
                f.write(result)
                f.write("\n")
            print(f"Successfully wrote {args.output}.", file=sys.stderr)
    elif args.report:
        if keyword == "computing":
            update_report_computing(args.report, result, args.dry_run)
        elif keyword == "time":
            update_report_time(args.report, result, args.dry_run)
        elif keyword == "partb":
            update_report_partb(args.report, result, args.dry_run)
        elif keyword == "partb-sivacor":
            if args.dry_run:
                print("DRY RUN: Would replace " + args.report + " with:\n", file=sys.stderr)
                print(result)
            else:
                with open(args.report, 'w') as f:
                    f.write(result)
                    f.write("\n")
                print(f"Successfully replaced {args.report} with SIVACOR Part B.", file=sys.stderr)
    else:
        # Just print to stdout
        print(result)


if __name__ == "__main__":
    main()
