# Project Guidelines for WSL Environment

## Environment Context

This workspace operates in a **Windows Subsystem for Linux (WSL)** environment accessed through VS Code.

## Critical Path Handling Rules

### Always Use Unix-Style Paths
- **Correct**: `/home/vilhuber/Workspace/aearep-8513/tools/script.py`
- **Incorrect**: `\home\vilhuber\Workspace\aearep-8513\tools\script.py`
- **Incorrect**: `C:\home\vilhuber\Workspace\aearep-8513\tools\script.py`

### Terminal Commands
- All terminal commands must use forward slashes `/`
- Working directory is within WSL filesystem: `/home/vilhuber/Workspace/aearep-8513`
- Never prepend Windows drive letters (C:, D:, etc.) to WSL paths

### File Operations
- When using file tools (read_file, create_file, replace_string_in_file), always use forward slashes
- Workspace root: `/home/vilhuber/Workspace/aearep-8513`
- If VS Code presents a path with backslashes, convert to forward slashes before using in tools

## Repository Structure

This is an academic replication package review repository with:
- **Python** data analysis scripts in `tools/`
- **MATLAB** configuration files (template-config.m)
- **Stata** scanner and analysis (PII_stata_scan.do, ado/)
- **R** configuration (template-config.R)
- **Shell scripts** for automation in `automations/`

## Common Commands

```bash
# Navigate to workspace root
cd /home/vilhuber/Workspace/aearep-8513

# Run automation scripts
bash automations/00_preliminaries.sh

# Python tools
python tools/advanced_pdf_extractor.py
```

## Code Review Workflow

When asked to "run code review", refer to instructions in [CLAUDE.md](CLAUDE.md) for standard review prompts and report generation.
