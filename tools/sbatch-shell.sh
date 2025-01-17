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
## Command(s) to run (example):
/usr/local/stata16/stata-mp -b main.do
## Matlab - will run "main.m", output to "main.log"
# matlab -nodisplay -r "addpath(genpath('.')); main" -logfile main.log
