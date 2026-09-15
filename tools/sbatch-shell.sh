#!/bin/bash
# Job name:
#SBATCH --job-name=RunStata
#
# Memory
#SBATCH --mem=32G
#
# Request one node:
#SBATCH --nodes=1
#
# Specify number of tasks for use case (example):
#SBATCH --ntasks-per-node=1
#
# Processors per task: here, 8 bc we have Stata-MP/8
#SBATCH --cpus-per-task=8
#
# Wall clock limit: adjust accordingly. Format is HH:MM:SS or DD-HH:MM:SS where DD are days.
#SBATCH --time=00:00:30
#
# Email?
# Probably do not need "--mail-user=youremail@cornell.edu"
# Just add your email to the file "$HOME/.forward"
# 
#SBATCH --mail-type=ALL
#
#############################################################################
## Jira notifications - see docs/tools/repository/96-90-sbatch-shell.md
#############################################################################
#
JIRATICKET=auto
TOOLS_DIR="${SLURM_SUBMIT_DIR:-$PWD}/tools"
PYTHON_CMD=$(command -v python3 || command -v python || true)
#
jira_notify() {
    [ -n "$PYTHON_CMD" ] || return 0
    [ -f "$TOOLS_DIR/jira_add_comment.py" ] || return 0
    "$PYTHON_CMD" "$TOOLS_DIR/jira_add_comment.py" --partb --slurm \
        "$@" -- "$JIRATICKET" || true
}
#
# The stop notification runs from a trap, so it also fires when the job fails
# or is killed at the wall clock limit (SIGTERM, reported as exit code 143).
jira_notify_end() {
    rc=$?
    [ -z "$1" ] || rc=$1
    trap - EXIT TERM
    jira_notify --status completed --exit-code "$rc"
    exit "$rc"
}
trap 'jira_notify_end' EXIT
trap 'jira_notify_end 143' TERM
#
# Start notification.
jira_notify --status started
#
#############################################################################
## Command(s) to run (example):
#############################################################################
#
# Stata example
#
/usr/local/stata16/stata-mp -b main.do
#
## Matlab - will run "main.m", output to "main.log"
## Assumes you have done the setup at https://labordynamicsinstitute.github.io/ecco-notes/docs/biohpc/slurm-quick-start.html#one-time-setup
# module load matlab/2023a
# matlab -nodisplay -r "addpath(genpath('.')); main" -logfile main.$(date +%F_%H-%M-%S).log
#
# R example - caution with version and parallel processing
module load R/4.4.2
R CMD BATCH main.R main.$(date +%F_%H-%M-%S).log
#
# Exit with the status of the last command above, so that the stop
# notification reports "completed" or "failed" correctly.
exit $?
