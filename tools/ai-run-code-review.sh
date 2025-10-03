#!/bin/bash

# AI Code Review Script
# Usage: ./run-code-review.sh [directory_name]

DIRECTORY=${1:-"src"}

echo "Starting AI code review for directory: $DIRECTORY"
echo "================================================"

# Launch Claude Code with the review prompt
claude-code "You are a code reviewer. Find any bugs in the code in this repository in the $DIRECTORY directory."