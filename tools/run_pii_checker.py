#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

"""
Run pii-checker (https://github.com/AEADataEditor/pii-checker) on a deposit
and sort its results into what may be committed and what may not.

pii-checker writes two workbooks into the package directory (with
--strip-details):
  pii_checker_results.xlsx            includes the values shown to the model
  pii_checker_results-nodetails.xlsx  the same without those values
The first is moved to --full-dir (an artifact of the pipeline run, never committed), the
second to --output-dir. A one-paragraph summary of the counts goes to
--summary-file, for the Jira comment.

Ollama is reached at --endpoint, else $OLLAMA_ENDPOINTS, else port 11434 of
the default gateway: in a container started by a Bitbucket Docker runner, the
gateway is the host that also serves Ollama. The model is loaded before
pii-checker starts, because pii-checker's own test call gives up after 30
seconds, which loading a large model from disk can exceed.

Ollama decides once, when it loads the model, how much of it goes on the GPU,
from the GPU memory free at that moment (for instance, while another model is
loaded). A model that ends up mostly on the CPU still works, but runs for
hours. So after loading, a short fixed prompt measures the generation speed.
Below --min-tokens-per-sec, the model is unloaded and loaded again every
--retry-minutes, until it is fast enough or --wait-minutes have passed; then
the script gives up (exit 3) with a message saying why, which also goes to
--summary-file for the Jira comment.

Usage:
    python3 tools/run_pii_checker.py DIRECTORY --checker-dir PATH [--model NAME]
        [--endpoint URL] [--full-dir DIR] [--output-dir DIR] [--summary-file FILE]
        [--min-tokens-per-sec N] [--wait-minutes N] [--retry-minutes N]

Run it with a Python that has pii-checker's requirements installed (it runs
pii-checker with the same interpreter); automations/34_run_pii_checker.sh
sets that up.
"""

import argparse
import datetime
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

RESULTS = 'pii_checker_results.xlsx'
NODETAILS = 'pii_checker_results-nodetails.xlsx'
OLLAMA_PORT = 11434
LOAD_TIMEOUT = 900  # seconds; a 25B model loads from a cold disk in a few minutes
BENCH_TIMEOUT = 600  # seconds; 64 tokens, even on the CPU
BENCH_PROMPT = 'List the first twenty prime numbers, separated by commas.'
BENCH_TOKENS = 64
SLOW = 3  # exit status when the model stays too slow
MIN_RATE = 40.0  # tokens/s; gemma4:26b makes about 100 on two RTX 3060s

# Overview sheet labels of pii-checker's results workbook
COUNTS = [
    ('Columns checked', 'columns checked'),
    ('Flagged: direct PII', 'direct PII'),
    ('Flagged: possible indirect PII', 'possible indirect PII'),
    ('Flagged: internal ID', 'internal IDs'),
]


def default_gateway(route_file='/proc/net/route'):
    """IPv4 address of the default gateway, or None."""
    try:
        with open(route_file) as f:
            next(f)  # header
            for line in f:
                fields = line.split()
                if len(fields) > 2 and fields[1] == '00000000':
                    return socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))
    except (OSError, ValueError, StopIteration):
        pass
    return None


def resolve_endpoint(endpoint=None, environ=os.environ, route_file='/proc/net/route'):
    if endpoint:
        return endpoint
    if environ.get('OLLAMA_ENDPOINTS'):
        return environ['OLLAMA_ENDPOINTS'].split(',')[0].strip()
    gateway = default_gateway(route_file)
    return f"http://{gateway or 'localhost'}:{OLLAMA_PORT}"


def ollama(endpoint, path, payload=None, timeout=60):
    """JSON response of an Ollama API call (POST if there is a payload)."""
    request = urllib.request.Request(
        endpoint.rstrip('/') + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read() or b'{}')


def load_model(endpoint, model, timeout=LOAD_TIMEOUT):
    """Asks Ollama to load the model (a generate call without a prompt)."""
    ollama(endpoint, '/api/generate', {'model': model, 'keep_alive': '15m'}, timeout)


def unload_model(endpoint, model):
    ollama(endpoint, '/api/generate', {'model': model, 'keep_alive': 0})


def measure_speed(endpoint, model, timeout=BENCH_TIMEOUT):
    """Tokens per second generated for a short fixed prompt. Sends no options
    that would make Ollama reload the model (such as num_ctx)."""
    result = ollama(endpoint, '/api/generate',
                    {'model': model, 'prompt': BENCH_PROMPT, 'stream': False, 'keep_alive': '15m',
                     'options': {'num_predict': BENCH_TOKENS, 'temperature': 0}}, timeout)
    count, duration = result.get('eval_count', 0), result.get('eval_duration', 0)  # duration in ns
    return count / duration * 1e9 if count and duration else 0.0


def other_models(endpoint, model):
    """Names of the other models Ollama has loaded, which hold GPU memory."""
    try:
        loaded = ollama(endpoint, '/api/ps').get('models', [])
    except (OSError, ValueError):
        return []
    return [m.get('name') for m in loaded if m.get('name') and m.get('name') != model]


def wait_for_speed(endpoint, model, min_rate, wait_minutes, retry_minutes,
                   clock=time.monotonic, sleep=time.sleep, log=None):
    """Measures the speed of the loaded model; while it is below min_rate,
    unloads it, waits retry_minutes, loads it again and measures again, for
    up to wait_minutes. Returns (ok, message)."""
    log = log or (lambda text: print(f"run_pii_checker: {text}", file=sys.stderr))
    deadline = clock() + wait_minutes * 60
    best = 0.0
    while True:
        rate = measure_speed(endpoint, model)
        best = max(best, rate)
        if rate >= min_rate:
            return True, f"{model} generates {rate:.1f} tokens/s (minimum {min_rate:g})"
        others = other_models(endpoint, model)
        loaded = f"; also loaded: {', '.join(others)}" if others else ''
        if clock() + retry_minutes * 60 > deadline:
            return False, (
                f"pii-checker did not run: {model} generated at most {best:.1f} tokens/s, "
                f"below the minimum of {min_rate:g} (PiiMinTokensPerSec), for {wait_minutes:g} minutes "
                f"(PiiWaitMinutes){loaded}. Ollama most likely placed the model largely on the CPU, "
                f"because the GPU memory was in use when it loaded the model. "
                f"Run the pipeline again once the GPU is free, or choose a smaller PiiModel.")
        log(f"{model} generates {rate:.1f} tokens/s, below {min_rate:g}{loaded}; "
            f"unloading it and trying again in {retry_minutes:g} minutes")
        unload_model(endpoint, model)
        sleep(retry_minutes * 60)
        load_model(endpoint, model)


def read_overview(path):
    """{Metric: Value} from the Overview sheet of a results workbook."""
    from openpyxl import load_workbook
    workbook = load_workbook(path, read_only=True)
    try:
        if 'Overview' not in workbook.sheetnames:
            return {}
        rows = workbook['Overview'].iter_rows(min_row=2, values_only=True)
        return {row[0]: row[1] for row in rows if row and row[0] is not None}
    finally:
        workbook.close()


ARTIFACT_DAYS = 14  # how long Bitbucket keeps the artifacts of a pipeline run


def pipeline_run(environ=os.environ):
    """Jira link to this pipeline run's step page, whose Artifacts tab offers
    the full results (Bitbucket has no link to the tab itself), or plain text
    outside Bitbucket Pipelines."""
    number = environ.get('BITBUCKET_BUILD_NUMBER')
    origin = environ.get('BITBUCKET_GIT_HTTP_ORIGIN')
    if not origin and environ.get('BITBUCKET_WORKSPACE') and environ.get('BITBUCKET_REPO_SLUG'):
        origin = f"https://bitbucket.org/{environ['BITBUCKET_WORKSPACE']}/{environ['BITBUCKET_REPO_SLUG']}"
    if not number:
        return 'the pipeline run'
    if not origin:
        return f'pipeline run #{number}'
    url = f"{origin.rstrip('/')}/pipelines/results/{number}"
    if environ.get('BITBUCKET_STEP_UUID'):
        url += '/steps/' + urllib.parse.quote(environ['BITBUCKET_STEP_UUID'], safe='')
    return f'pipeline run [#{number}|{url}]'


def summarize(overview, model, nodetails_path, full_path, environ=os.environ, today=None):
    counts = ', '.join(f"{overview.get(label, '?')} {text}" for label, text in COUNTS)
    until = (today or datetime.date.today()) + datetime.timedelta(days=ARTIFACT_DAYS)
    return (f"pii-checker (model {model}): {counts}. "
            f"Results without the values observed in the data: {{{{{nodetails_path}}}}}. "
            f"The full results, with the values shown to the model, are not committed: "
            f"download {{{{{full_path}}}}} from the Artifacts tab of {pipeline_run(environ)} "
            f"until {until:%B %-d, %Y}.")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('directory', help='deposit directory to check')
    parser.add_argument('--checker-dir', required=True, help='pii-checker checkout')
    parser.add_argument('--model', default='gemma4:26b', help='Ollama model (default: %(default)s)')
    parser.add_argument('--endpoint', help='Ollama URL (default: $OLLAMA_ENDPOINTS, else the default gateway)')
    parser.add_argument('--full-dir', default='pii-checker-full',
                        help='where the full results go; must not be committed (default: %(default)s)')
    parser.add_argument('--output-dir', default='generated',
                        help='where the results without values go (default: %(default)s)')
    parser.add_argument('--summary-file',
                        help='write the summary (or why the check did not run) here as well as to stdout')
    parser.add_argument('--min-tokens-per-sec', type=float, default=MIN_RATE,
                        help='slowest acceptable generation speed; 0 skips the check (default: %(default)s)')
    parser.add_argument('--wait-minutes', type=float, default=30,
                        help='how long to keep trying for that speed (default: %(default)s)')
    parser.add_argument('--retry-minutes', type=float, default=5,
                        help='pause between attempts (default: %(default)s)')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not os.path.isdir(args.directory):
        print(f"run_pii_checker: not a directory: {args.directory}", file=sys.stderr)
        return 2

    endpoint = resolve_endpoint(args.endpoint)
    print(f"run_pii_checker: loading {args.model} on {endpoint}", file=sys.stderr)
    try:
        load_model(endpoint, args.model)
    except OSError as e:
        print(f"run_pii_checker: could not load {args.model} on {endpoint}: {e}", file=sys.stderr)
        return 1
    if args.min_tokens_per_sec > 0:
        try:
            ok, message = wait_for_speed(endpoint, args.model, args.min_tokens_per_sec,
                                         args.wait_minutes, args.retry_minutes)
        except OSError as e:
            print(f"run_pii_checker: could not measure the speed of {args.model}: {e}", file=sys.stderr)
            return 1
        print(f"run_pii_checker: {message}", file=sys.stderr)
        if not ok:
            unload_model_quietly(endpoint, args.model)
            write_summary(args.summary_file, message)
            return SLOW

    env = dict(os.environ, LLM_PROVIDER='ollama', OLLAMA_ENDPOINTS=endpoint)
    run = subprocess.run(
        [sys.executable, os.path.join(args.checker_dir, 'interface.py'),
         os.path.abspath(args.directory), '--strip-details', '--model', args.model],
        cwd=args.checker_dir, env=env)
    if run.returncode != 0:
        print(f"run_pii_checker: pii-checker exited with {run.returncode}", file=sys.stderr)
        return run.returncode

    # pii-checker logs a failed package and exits 0: the workbooks tell
    produced = {name: os.path.join(args.directory, name) for name in (RESULTS, NODETAILS)}
    missing = [name for name, path in produced.items() if not os.path.isfile(path)]
    if missing:
        print(f"run_pii_checker: pii-checker did not write {', '.join(missing)}", file=sys.stderr)
        return 1

    os.makedirs(args.full_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    full_path = os.path.join(args.full_dir, RESULTS)
    nodetails_path = os.path.join(args.output_dir, NODETAILS)
    shutil.move(produced[RESULTS], full_path)
    shutil.move(produced[NODETAILS], nodetails_path)

    summary = summarize(read_overview(nodetails_path), args.model, nodetails_path, full_path)
    print(summary)
    write_summary(args.summary_file, summary)
    return 0


def write_summary(path, text):
    if path:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w') as f:
            f.write(text + '\n')


def unload_model_quietly(endpoint, model):
    try:
        unload_model(endpoint, model)
    except OSError:
        pass


if __name__ == '__main__':
    sys.exit(main())
