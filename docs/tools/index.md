(helpful-scripts)=
# Various helpful scripts

*Last updated: April 2, 2026*

All of the following scripts are either made available in `bash` when you run the [bash setup](setup-bash) in the `$HOME/bin` directory, or are available in the `tools/` folder in each repository. 

:::{note}

If you do not see a script referenced here, or the script does not behave as intended, 

1. `git commit` all changes, and `git push` them
2. Run the `Refresh repository` script in Bitbucket.

:::


## Data Download and Synchronization Tools

### download_box_private.py
Python script for downloading files from private Box folders using JWT authentication.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_box_private.py) | [Help](download/96-90-download_box_private.md)

### download_dv.py
Python script for downloading complete datasets from Dataverse repositories as ZIP archives using DOI.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_dv.py) | [Help](download/96-90-download_dv.md)

### download_openicpsr-private.py
Python script for downloading files from private (unpublished) openICPSR deposits with authentication.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_openicpsr-private.py) | [Help](download/96-90-download_openicpsr-private.md)

### download_openicpsr-public.py
Python script for downloading files from public (published) openICPSR deposits.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_openicpsr-public.py) | [Help](download/96-90-download_openicpsr-public.md)

### download_osf.sh
Bash script for downloading all files and directories from Open Science Framework (OSF) projects.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_osf.sh) | [Help](download/96-90-download_osf.md)

### download_sivacor.py
Python script for downloading SIVACOR submission artifacts, handles ZIP extraction, and commits results to git branch.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_sivacor.py) | [Help](download/96-90-download_sivacor.md)

### get_sivacor_info.py
Python script for extracting computing environment, timing information, and SIVACOR-specific Part B Markdown from TRO JSONLD files. Can output to stdout, write generated Markdown, or update reports.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/get_sivacor_info.py) | [Help](repository/96-90-get_sivacor_info.md)

### generate_sivacor_partb.sh
Bash wrapper for generating `generated/REPLICATION-PartB-SIVACOR.md` from a submitted SIVACOR TRO file without rerunning author code. The generated file extracts Part B from the single `REPLICATION.md` template and inserts only objective SIVACOR-derived material: computing environment facts, workflow steps, and SIVACOR-generated-file findings. It also writes `generated/sivacor-partb-appendix.md` for inclusion by the normal generated appendix template.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/generate_sivacor_partb.sh) | [Help](repository/96-90-get_sivacor_info.md)

### download_zenodo_draft.py
Python script for downloading files from Zenodo draft deposits that require authentication.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_zenodo_draft.py) | [Help](download/96-90-download_zenodo_draft.md)

### download_zenodo_public.sh
Bash script for downloading files from public Zenodo repositories using zenodo_get tool.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/download_zenodo_public.sh) | [Help](download/96-90-download_zenodo_public.md)

### list_box_files.py
Lists files from a private Box folder using JWT authentication and outputs results to a text file.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/list_box_files.py) | [Help](repository/96-90-list_box_files.md)

### sync-codeocean.sh
Synchronizes CodeOcean capsules with local repositories, maintaining both live Git clones and static copies.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/sync-codeocean.sh) | [Help](repository/96-90-sync-codeocean.md)

### zenodo_get_ci.py
CI-friendly wrapper for zenodo_get that suppresses animated progress bar in automated pipelines.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/zenodo_get_ci.py) | [Help](repository/96-90-zenodo_get_ci.md)

## File Format Conversion Tools

### convert_eps.sh
Bash script that recursively converts EPS (Encapsulated PostScript) files to PNG format using ImageMagick. 

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/convert_eps.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/convert_eps.sh)

### convert_graphs.do
Stata script that converts GPH graph files to PDF and PNG formats.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/convert_graphs.do) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/convert_graphs.do)

### csv2md.py
Python tool for converting arbitrary CSV files to Markdown format.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/csv2md.py) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/csv2md.py)

### matlab_convert_fig.m
MATLAB script that converts .fig files to PNG format, processing all figure files in the current directory.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/matlab_convert_fig.m) | [Help](conversion/96-90-matlab_convert_fig.md)

### matlab_convert_mat2csv.m
MATLAB script that converts .mat files to CSV format, extracting all variables as separate CSV files.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/matlab_convert_mat2csv.m) | [Help](conversion/96-90-matlab_convert_mat2csv.md)

### mk_tex_table.sh
Converts standalone LaTeX table files to complete PDF documents with comprehensive formatting packages.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/mk_tex_table.sh) | [Help](conversion/96-90-mk_tex_table.md)

## Tools to check for various things

These are usually not used directly, but run by the Pipelines.

### Stata_scan_code/
Directory containing Stata code scanning tools and packages for analyzing Stata scripts and dependencies.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/tree/master/tools/Stata_scan_code) | [Help](https://github.com/aeaDataEditor/replication-template/tree/master/tools/Stata_scan_code)

### check_ipynb_order.py
Python script that verifies Jupyter notebook code cells were executed in sequential order for reproducibility.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/check_ipynb_order.py) | [Help](analysis/96-90-check_ipynb_order.md)

### check_r_deps.R
R script that finds and outputs all R package dependencies as CSV from a project directory.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/check_r_deps.R) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/check_r_deps.R)

### check_rds_files.R
R script for checking RDS (R data files), designed to run automatically without manual changes.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/check_rds_files.R) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/check_rds_files.R)

### doi_validator.py
Python module to validate DOI links and convert between formats for Harvard Dataverse DOIs.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/doi_validator.py) | [Help](analysis/96-90-doi_validator.md)

### find_cran_date.py
Python tool that determines minimum CRAN snapshot date for pinned R packages and reports matching Docker images.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/find_cran_date.py) | [Help](analysis/96-90-find_cran_date.md)

### install.R
R package installation utility with version control; provides `pkgTest()` function to install and require packages.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/install.R) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/install.R)

### scan_pkg.jl
Julia package scanner that identifies and lists packages used in Julia files via `using` and `import` statements.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/scan_pkg.jl) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/scan_pkg.jl)

### summarize_data.py
Python script that summarizes data metadata by directory levels, aggregating file sizes from CSV.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/summarize_data.py) | [Help](analysis/96-90-summarize_data.md)

## Ad-hoc Data Analysis and Comparison Tools

### compare_manifests.py
Python script that compares two SHA256 manifest files to identify overlaps in filenames, checksums, and complete records.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/compare_manifests.py) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/compare_manifests.py)

### generate_png_diff.sh
Generates visual diffs for modified PNG images by comparing them against their git repository versions.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/generate_png_diff.sh) | [Help](conversion/96-90-generate_png_diff.md)


### summarize_diff_stats.py
Parses and summarizes statistical differences from files, extracting numerical values and filenames.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/summarize_diff_stats.py) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/summarize_diff_stats.py)


## Pipeline and Workflow Tools


### pipeline-steps1-4.sh
Combined pipeline script that handles multiple steps of the openICPSR download process.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/pipeline-steps1-4.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/pipeline-steps1-4.sh)

### run_scanner.sh
Runs Stata code scanner on ICPSR directory, reads configuration and executes scanning operations.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/run_scanner.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/run_scanner.sh)

### sbatch-shell.sh
SLURM batch job script template for running Stata jobs on HPC clusters with resource specifications.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/sbatch-shell.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/sbatch-shell.sh)

## JIRA Integration Tools

These tools integrate with the AEA Data Editor Jira system for task tracking and metadata extraction.

### jira_add_comment.py
Posts comments to Jira issues using the Jira API with support for wiki markup formatting.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/jira_add_comment.py) | [Help](jira/96-90-jira_add_comment.md)

### jira_find_task_by_icpsr.py
Finds the highest-numbered Jira Task issue for a given openICPSR project ID.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/jira_find_task_by_icpsr.py) | [Help](jira/96-90-jira_find_task_by_icpsr.md)

### jira_get_info.py
Retrieves various information fields from Jira issues including DOIs, openICPSR URLs, and SIVACOR IDs.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/jira_get_info.py) | [Help](jira/96-90-jira_get_info.md)

### jira_download_attachments.py
Downloads all attachments from Jira issues with their original filenames, with support for filtering and list-only mode.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/jira_download_attachments.py) | [Help](jira/96-90-jira_download_attachments.md)

### jira_sync_fields.py
Copies fields from a source Jira issue to a target issue, filling only empty fields on the target. Useful for carrying over metadata from an original issue to a revision issue.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/jira_sync_fields.py) | [Help](jira/96-90-jira_sync_fields.md)

## Configuration and Setup Tools


### linux-system-info.sh
System information collector that displays OS details, processor info, and memory availability.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/linux-system-info.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/linux-system-info.sh)


### update_tools.sh
Tool updater that downloads latest replication template files from GitHub and copies them to template directory.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/update_tools.sh) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/update_tools.sh)

## Document Processing Tools

### prepare-revision.py (inactive)

Processes Markdown files by replacing code block content in Appendix sections while maintaining headers.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/prepare-revision.py) | [Help](https://github.com/aeaDataEditor/replication-template/blob/master/tools/prepare-revision.py)


## Configuration Files

### requirements-scanner.txt
Python requirements file for scanner tools.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/requirements-scanner.txt)

### requirements.txt
Python requirements file for general tools.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/requirements.txt)

### template.tex
LaTeX template file for document generation.

**Links:** [Source](https://github.com/aeaDataEditor/replication-template/blob/master/tools/template.tex)
