#!/usr/bin/env python3
"""Update the Contributors list in README.md from the GitHub contributors API."""

import os
import re
import sys

import requests

README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")
MARKER_START = "<!-- CONTRIBUTORS:START -->"
MARKER_END = "<!-- CONTRIBUTORS:END -->"

EXCLUDED_LOGINS = {"copilot", "claude", "claude[bot]"}


def api_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_contributors(repo, headers):
    contributors = []
    url = f"https://api.github.com/repos/{repo}/contributors"
    params = {"per_page": 100, "anon": "false"}
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        contributors.extend(response.json())
        url = response.links.get("next", {}).get("url")
        params = None
    return contributors


def get_display_name(login, headers):
    response = requests.get(f"https://api.github.com/users/{login}", headers=headers)
    response.raise_for_status()
    return response.json().get("name") or login


def build_contributor_list(repo, token):
    headers = api_headers(token)
    contributors = get_contributors(repo, headers)

    entries = []
    for contributor in contributors:
        login = contributor["login"]
        if login.lower() in EXCLUDED_LOGINS:
            continue
        name = get_display_name(login, headers)
        entries.append((name, login))

    entries.sort(key=lambda entry: entry[0].lower())
    return entries


def render_list(entries):
    lines = [f"- {name}, [@{login}](https://github.com/{login})" for name, login in entries]
    return "\n".join(lines)


def update_readme(entries):
    with open(README_PATH, "r") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.DOTALL
    )
    if not pattern.search(content):
        sys.exit(
            f"Could not find {MARKER_START} / {MARKER_END} markers in README.md"
        )

    replacement = f"{MARKER_START}\n{render_list(entries)}\n{MARKER_END}"
    content = pattern.sub(replacement, content)

    with open(README_PATH, "w") as f:
        f.write(content)


def main():
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]

    entries = build_contributor_list(repo, token)
    update_readme(entries)


if __name__ == "__main__":
    main()
