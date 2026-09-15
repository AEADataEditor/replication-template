#!/usr/bin/env python3
"""
Wrapper for zenodo_get that suppresses progress bar in CI environments.

This script wraps the zenodo_get module to provide a CI-friendly interface
that suppresses the animated progress bar while preserving all informational
messages. It detects CI environments via the CI environment variable.

Usage:
    python3 tools/zenodo_get_ci.py [ZENODO_GET_OPTIONS]

Examples:
    # Download all files from a Zenodo record
    python3 tools/zenodo_get_ci.py --output-dir=zenodo-123456 123456
    
    # Use sandbox
    python3 tools/zenodo_get_ci.py --sandbox --output-dir=zenodo-123456 123456

Environment Variables:
    CI - When set, suppresses the progress bar by redirecting stdout to /dev/null
    
Behavior:
    - In CI environments (CI env var set): Progress bar is suppressed
    - In interactive environments: Progress bar is shown normally
    - All informational messages are preserved (they go to stderr)

Note:
    The zenodo_get module writes informational messages to stderr via eprint(),
    while the progress bar from the wget library writes to stdout. This allows
    us to suppress only the progress bar by redirecting stdout.
"""

import os
import sys

# Import zenodo_get first
from zenodo_get import zget

if __name__ == '__main__':
    # Suppress progress bar in CI by redirecting stdout to /dev/null
    if os.getenv("CI"):
        # Save original stdout
        original_stdout = sys.stdout
        # Redirect stdout to /dev/null to suppress progress bar
        sys.stdout = open(os.devnull, 'w')
        
        try:
            zget.cli()
        finally:
            # Restore stdout
            sys.stdout.close()
            sys.stdout = original_stdout
    else:
        # Normal mode - show progress bar
        zget.cli()
