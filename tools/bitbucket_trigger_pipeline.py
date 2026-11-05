#!/usr/bin/env python3
"""
Start a custom pipeline of this Bitbucket repository on the current branch.

Usage:
    bitbucket_trigger_pipeline.py <pipeline> [--var NAME=VALUE ...]
    bitbucket_trigger_pipeline.py -h|--help

Arguments:
    pipeline         Name of the custom pipeline (e.g., m-parse-manuscript)

Options:
    --var NAME=VALUE Pipeline variable to pass (repeatable). Variables with an
                     empty value are not sent.

Environment (all set by Bitbucket Pipelines, except the two credentials):
    BITBUCKET_WORKSPACE, BITBUCKET_REPO_SLUG, BITBUCKET_BRANCH
    JIRA_USERNAME    Atlassian account email, used for the API login
    P_BITBUCKET_PAT  Bitbucket API token (scope: write:pipeline:bitbucket)

Prints the URL of the new pipeline run. Exit code 0 if it was started, 1 if not;
the reason goes to stderr.
"""

import argparse
import os
import sys

import requests

API = "https://api.bitbucket.org/2.0/repositories"
WEB = "https://bitbucket.org"


def build_request(pipeline, variables, environ):
    """Return (url, payload) for the pipelines API, from the Bitbucket environment."""
    missing = [k for k in ("BITBUCKET_WORKSPACE", "BITBUCKET_REPO_SLUG", "BITBUCKET_BRANCH") if not environ.get(k)]
    if missing:
        raise ValueError(f"not running in Bitbucket Pipelines: {', '.join(missing)} not set")
    url = f"{API}/{environ['BITBUCKET_WORKSPACE']}/{environ['BITBUCKET_REPO_SLUG']}/pipelines/"
    payload = {
        "target": {
            "type": "pipeline_ref_target",
            "ref_type": "branch",
            "ref_name": environ["BITBUCKET_BRANCH"],
            "selector": {"type": "custom", "pattern": pipeline},
        },
    }
    sent = [{"key": k, "value": v} for k, v in variables.items() if v]
    if sent:
        payload["variables"] = sent
    return url, payload


def parse_vars(items):
    variables = {}
    for item in items or []:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise ValueError(f"--var needs NAME=VALUE, got {item!r}")
        variables[name] = value
    return variables


def trigger(pipeline, variables, environ, post=requests.post):
    """Start the pipeline. Returns the URL of the run; raises RuntimeError on failure."""
    user, token = environ.get("JIRA_USERNAME"), environ.get("P_BITBUCKET_PAT")
    if not user or not token:
        raise RuntimeError("JIRA_USERNAME and P_BITBUCKET_PAT must be set")
    try:
        url, payload = build_request(pipeline, variables, environ)
    except ValueError as e:
        raise RuntimeError(str(e))
    response = post(url, json=payload, auth=(user, token), timeout=60)
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Bitbucket answered {response.status_code}: {response.text[:300]}")
    run = response.json()
    return (f"{WEB}/{environ['BITBUCKET_WORKSPACE']}/{environ['BITBUCKET_REPO_SLUG']}"
            f"/pipelines/results/{run.get('build_number', '')}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pipeline")
    p.add_argument("--var", action="append", metavar="NAME=VALUE")
    args = p.parse_args(argv)
    try:
        print(trigger(args.pipeline, parse_vars(args.var), os.environ))
    except (RuntimeError, ValueError, requests.RequestException) as e:
        print(f"Error: could not start {args.pipeline}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
