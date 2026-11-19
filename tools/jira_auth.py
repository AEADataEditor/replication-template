#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

"""
Connection and authentication check shared by the Jira tools.

Every Jira REST call goes through the Atlassian API gateway (GATEWAY_URL),
which accepts scoped API tokens as well as unscoped (classic) ones. The site
URL (SITE_URL) accepts only unscoped tokens, so it is used for browse links
only.

Importing this module needs only the standard library; the `jira` package is
imported by connect() alone, so that jira_add_comment.py keeps working where
`jira` is not installed.
"""

TOKEN_URL = "https://id.atlassian.com/manage-profile/security/api-tokens"

# The Jira site, used for browse links.
SITE_URL = "https://aeadataeditors.atlassian.net"

# The same site through the Atlassian API gateway, where every REST call goes.
CLOUD_ID = "c342e627-3ea3-47e3-b3dd-58b188a34a9e"
GATEWAY_URL = "https://api.atlassian.com/ex/jira/" + CLOUD_ID

# Statuses with which Jira refuses the credentials themselves.
REJECTED = (401, 403)


class JiraAuthError(Exception):
    """Jira did not accept JIRA_USERNAME / JIRA_API_KEY."""


def verify_auth(client):
    """Confirm Jira accepts the client's credentials and return the user record.

    `client` is anything with a myself() method whose HTTP errors carry a
    `status_code` attribute (a jira.JIRA client, or jira_add_comment's
    clients). Jira Cloud serves a request with a rejected API token as an
    anonymous user instead of failing it, so without this check a bad token
    shows up later as a missing custom field or a nonexistent issue.
    Errors other than a rejection pass through unchanged.
    """
    try:
        return client.myself()
    except Exception as exc:
        status = getattr(exc, 'status_code', None)
        if status in REJECTED:
            raise JiraAuthError(
                "Jira rejected JIRA_USERNAME/JIRA_API_KEY (HTTP {0}). "
                "The API token may be expired, revoked, or missing a scope; "
                "create a new one at {1}".format(status, TOKEN_URL)
            ) from exc
        raise


def connect(username, api_key):
    """Authenticated jira.JIRA client (through the gateway), and the user record.

    Raises JiraAuthError if the credentials are rejected; connection errors
    pass through.
    """
    from jira import JIRA

    jira = JIRA(server=GATEWAY_URL, basic_auth=(username, api_key),
                options={'verify': True})
    return jira, verify_auth(jira)
