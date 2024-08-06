# [MC number] [Manuscript Title] Validation and Replication results

> INSTRUCTIONS: Once you've read these instructions, DELETE THESE AND SIMILAR LINES. Also delete lines that include "{{  SOME-TEXT }}".

> INSTRUCTIONS: In the above title, replace [Manuscript Title] with the actual title of the paper, and [MC number] with the Manuscript Central number (e.g., AEJPol-2017-0097)

> INSTRUCTIONS: Go through the steps to download and attempt a replication. Document your steps here, the errors generated, and the steps you took to alleviate those errors. This includes apparently minor steps, such as adjusting directories, or installing packages, any deviations from the README. If the README did not specify a certain step or action, describe why you chose that action, and whether it should be detailed in the README. All figures and tables should be evident once you are done, i.e., saved to disk. If this is not done in code, please add code to do so.

> INSTRUCTIONS: To compare images and tables, annotated screenshots from the manuscript can be helpful for comparison, highlighting where differences were found.

> INSTRUCTIONS: Leave these lines here:

> Some useful links:
> - [Official Data and Code Availability Policy](https://www.aeaweb.org/journals/policies/data-code)
> - [Step by step guidance](https://aeadataeditor.github.io/aea-de-guidance/) 
> - [Template README](https://social-science-data-editors.github.io/template_README/)

## SUMMARY

> INSTRUCTION: The Data Editor will fill this part out. It will be based on any [REQUIRED] and [SUGGESTED] action items that the report makes a note of.

> INSTRUCTION: The next line CLOSES the summary.

In assessing compliance with our [Data and Code Availability Policy](https://www.aeaweb.org/journals/policies/data-code), we have identified the following issues, which we ask you to address:


### Action Items (manuscript)

> INSTRUCTION: Add all manuscript related items here.

> INSTRUCTION: If any changes are needed, leave the following text in; otherwise, remove it:

> [REQUIRED] If making changes to the manuscript (other than citations or bibliography), please describe in a response letter to the Editor and Data Editor any deviations from the conditionally accepted version (as approved by the Editor) and their impact, especially of key estimates or outcomes. Email that response letter to the Data Editor at dataeditor@aeapubs.org, referencing the manuscript number.


### Action Items (openICPSR)

> INSTRUCTION: leave the next few lines in, do not delete them.

-----action items go here------

> - If your openICPSR deposit appears to be "locked", please follow [these instructions](https://aeadataeditor.github.io/aea-de-guidance/FAQ.html#you-can-recall-the-submission).
> - Do NOT create a new deposit! You should modify the existing deposit, deleting any files that need be replaced. We encourage you to use the "Import from ZIP" function to upload multiple files, rather than the "Upload Files" function.
> - Under no circumstances should your primary deposit contain confidential or restricted-use data. If a component of your replication package cannot be openly published, please contact us immediately.
> - Please provide a brief but detailed response to the requested changes. You can do this in the Communication Log in your deposit Workspace, or by email to dataeditor@aeapubs.org, mentioning the manuscript number in the subject line.
>
> Once you are done making changes, please "Change Status -> Submit to AEA" from your deposit Workspace.

> [NOTE] We may publish replication packages as soon as all requested changes to the deposit have been made. Please process any requested changes as soon as possible.

> INSTRUCTION: ALWAYS do "Data description", "Code description". If data is present, ALWAYS do "Data checks". If time is sufficient (initial assessment!), do "Replication steps", if not, explain why not.

## General


> INSTRUCTIONS: Check off the following sections/elements that you find in either the README provided by the authors, or in the authors' online appendix (rare).
> INSTRUCTIONS: ==>  Workflow stage: You are now going from *In Progress* to *Code*

- [ ] Data Availability and Provenance Statements
  - [ ] Statement about Rights - Part 1: Right to use the data
  - [ ] Statement about Rights - Part 2: Right to publish the data
  - [ ] License for Data (optional, but recommended)
  - [ ] Details on each Data Source
- [ ] Dataset list
- [ ] Computational requirements
  - [ ] Software Requirements
  - [ ] Controlled Randomness (as necessary)
  - [ ] Memory, Runtime, and Storage Requirements
- [ ] Description of programs/code
  - [ ] License for Code (Optional, but recommended) 
- [ ] Instructions to Replicators
  - [ ] Details (as necessary)
- [ ] List of tables and programs
- [ ] References (Optional, but recommended) 


> INSTRUCTIONS: Leave this in, when any of the sections is lacking. Remove the entire section only if the README has all the pieces necessary (up to minor imprecisions).

> [REQUIRED] As specified in the [Policy](https://www.aeaweb.org/journals/data/data-code-policy) and the [DCAF](https://www.aeaweb.org/journals/forms/data-code-availability), the README should follow the schema provided by the [Social Science Data Editors' template README](https://social-science-data-editors.github.io/guidance/template-README.html).
  - All elements are required, unless a modifier is used in the above list.

## Data description

### Data Sources

> INSTRUCTIONS: Identify all INPUT data sources. Create a list (and commit the list together with this report) (not needed if filling out the "Data Citation and Information report"). For each data source, list in THIS document presence or absence of source, codebook/information on the data, and summary statistics. Summary statistics and codebook may not be necessary if they are available for public use data. In all cases, if the author of the article points to an online location for such information, that is OK. IN THIS DOCUMENT, point out only a summary of shortcomings.

> INSTRUCTIONS: For all data sources, check for a data citation. Oftentimes authors will cite the **paper** in which a dataset is originally used, but this is not a *data* citation. If you have found what you think to be a data citation, quote it in the report as shown below for the "Example data". 

#### Template

> INSTRUCTIONS: Use this template for each of the actual data sources. Check off the boxes that are TRUE, leave empty those that are not.

- [ ] Dataset is  provided in public deposit
- [ ] Dataset is PRIVATELY provided (not for publication)
- [ ] Access conditions are described:
  - INSTRUCTIONS: summarize the access conditions here.
- [ ] DOI or URL is provided, and works: (PROVIDE URL OR DOI HERE)
- [ ] Data are not cited, but a working paper, article, or other document is cited (not a data citation)
- [ ] Data are cited
  - [ ] in the manuscript
  - [ ] in the README

> INSTRUCTIONS: copy the citation here, whether data or the document citation.

> INSTRUCTIONS: If the relevant items above are NOT checked, leave the related [REQUIRED] element here. Otherwise, delete the line.

> [REQUIRED] Please add data citations to the article. Guidance on how to cite data is provided in the [AEA Sample References](https://www.aeaweb.org/journals/data/references) and in [additional guidance](https://social-science-data-editors.github.io/guidance/addtl-data-citation-guidance.html).

> [REQUIRED] Please provide a clear description of access modality and source location for this dataset. Some examples are given [on this website](https://social-science-data-editors.github.io/guidance/Requested_information_dcas.html).

> INSTRUCTIONS: Here is an example (delete it once you've read through it!)

#### Example data: Bureau of Labor Statistics

> INSTRUCTIONS: In this example, data are not provided, a link is provided in the README, and that's about it. Here's how you would fill that out:

- [ ] Dataset is  provided.
- [x] Access conditions are described:
  - No information on access conditions.
- [x] DOI or URL is provided, and works: http://data.bls.gov/cgi-bin/surveymost?sm+08
- [ ] Data are not cited, but a working paper, article, or other document is cited (not a data citation)
- [x] Data are cited
  - [x] in the manuscript
  - [x] in the README:

> Bureau of Labor Statistics. 2000–2010. “Current Employment Statistics: Colorado, Total Nonfarm, Seasonally adjusted - SMS08000000000000001.” United States Department of Labor. http://data.bls.gov/cgi-bin/surveymost?sm+08 (accessed February 9, 2011).

### Analysis Data Files

> INSTRUCTIONS: Separately, identify any analysis data file provided. Analysis data files are produced by code in the deposit from data sources. Not every deposit will have these. Analysis data files do not need to be cited, because they are a key part of the replication package.

- [ ] No analysis data file mentioned
- [ ] Analysis data files mentioned, not provided (explain reasons below)
- [ ] Analysis data files mentioned, provided. File names listed below.
- [ ] Analysis data files not mentioned, but provided.

Example:

```
./Output_Empirical/data/regression_main.dta
```

## Data deposit

> INSTRUCTIONS: Most deposits will be at openICPSR, but all need to be checked for complete metadata. Detailed guidance is at [https://aeadataeditor.github.io/aea-de-guidance/](https://aeadataeditor.github.io/aea-de-guidance/). 

### Requirements 

> INSTRUCTIONS: Check that these requirements are met. All of these should be met for openICPSR deposits, for other deposits, check out [this page](https://aeadataeditor.github.io/aea-de-guidance/guidelines-other-repositories).

- [ ] README is in TXT, MD, PDF format
- [ ] Deposit has no ZIP files
- [ ] Title conforms to guidance (starts with "Data and Code for:" or "Code for:", is properly capitalized)
- [ ] Authors (with affiliations) are listed in the same order as on the paper

> INSTRUCTIONS: If any of the above are NOT checked, leave the related [REQUIRED] element here. Otherwise, delete the line.

> [REQUIRED] Please ensure that a ASCII (txt), Markdown (md), or PDF version of the README are available in the data and code deposit.

> [REQUIRED] Deposit should not have ZIP files visible. 
  - on openICPSR: ZIP files should be uploaded to openICPSR via "Import from ZIP" instead of "Upload Files". Please delete the ZIP files, and re-upload using the "Import from ZIP" function.
  - on other platforms: Please consult with your repository helpdesk how to "import from ZIP".

> [REQUIRED] Please review the title of the deposit as per our guidelines (below).

> [REQUIRED] Please review authors and affiliations on the deposit. In general, they are the same, and in the same order, as for the manuscript; however, authors can deviate from that order.

> INSTRUCTIONS: Leave the following line in the report if any of the above are checked:

> Detailed guidance is at [https://aeadataeditor.github.io/aea-de-guidance/](https://aeadataeditor.github.io/aea-de-guidance/), for non-ICPSR deposits, check out [this guidance](https://aeadataeditor.github.io/aea-de-guidance/guidelines-other-repositories).

### Deposit Metadata

> INSTRUCTIONS: Some of these are specific to openICPSR (JEL, Manuscript Number). Others may or may not be present at other trusted repositories (Dataverse, Zenodo, etc.). Verify all items for openICPSR, check with supervisor for other deposits.

- [ ] JEL Classification (required)
- [ ] Manuscript Number (required)
- [ ] Subject Terms (highly recommended)
- [ ] Geographic coverage (highly recommended)
- [ ] Time period(s) (highly recommended)
- [ ] Collection date(s) (suggested)
- [ ] Universe (suggested)
- [ ] Data Type(s) (suggested)
- [ ] Data Source (suggested)
- [ ] Units of Observation (suggested)

> INSTRUCTIONS: Go through the checklist above, and then choose ONE of the following results:

> [NOTE] openICPSR metadata is sufficient.

or

> [REQUIRED] Please update the openICPSR metadata fields marked as (required), in order to improve findability of your data and code supplement. 

and/or

> [SUGGESTED] We suggest you update the openICPSR metadata fields marked as (highly recommended), in order to improve findability of your data and code supplement. 
> [SUGGESTED] We suggest you update the openICPSR metadata fields marked as (suggested), in order to improve findability of your data and code supplement. 


For additional guidance, see [https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html](https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html).


> INSTRUCTIONS: ==>  Workflow stage: You have now completed *PartA*. Please update Jira and prepare to discuss with lead RA or supervisor!

> INSTRUCTIONS: ==>  Workflow stage: You are starting *PartB*.

## Stated Requirements

> INSTRUCTIONS: The authors may have specified specific requirements in terms of software, computer hardware, etc. Please list them here. This is **different** from the Computing Environment of the Replicator. You have the option to amend these with unstated requirements later. If all requirements are listed, check the box "Requirements are complete".

- [ ] No requirements specified
- [ ] Software Requirements specified as follows:
  - Software 1
  - Software 2
- [ ] Computational Requirements specified as follows:
  - Cluster size, etc.
- [ ] Time Requirements specified as follows:
  - Length of necessary computation (hours, weeks, etc.)

- [ ] Requirements are complete.

> INSTRUCTIONS: If the requirements are NOT complete, please leave this line in. If unsure, leave this line in:

For missing requirements, see the list of required changes in the **FINDINGS** section.

> INSTRUCTIONS: If easier, simply copy-and-paste the authors' stated requirements here:

---

## Code description

> INSTRUCTIONS: Review the code (but do not run it yet). Identify programs that create "analysis files" ("data preparation code"). Identify programs that create tables and figures. Not every deposit will have separate programs for this.

> INSTRUCTIONS: Identify all **Figure, Table, and any in-text numbers**. Create a list, mapping each of them to a particular program and line number within the program (use [this template](code-check.xlsx)). Commit that list. You will come back to the list in your findings. IN THIS SECTION, point out only a summary description, including of shortcomings. E.g.

> INSTRUCTIONS: For example, you could write "There are four provided Stata do files, three Matlab .m files, including a "master.do"."
> INSTRUCTIONS: And you could list the issues you encounter:
> INSTRUCTIONS: - Table 5: could not identify code that produces Table 5
> INSTRUCTIONS: - Neither the program codes, nor the README, identify which tables are produced by what program.

{{ programs-summary.txt }}

The full list of programs provided can be found in the Appendix.

> INSTRUCTIONS: Verify the appendix, the repository. If the list is missing, generate it by hand (instructions in the appendix).

- [ ] The replication package contains a "main" or "master" file(s) which calls all other auxiliary programs.

> INSTRUCTIONS: If the above checkbox for "main" file is NOT checked, leave the following SUGGESTION in the report!

> [SUGGESTED] We strongly advise the use of a single (or a small number of) main control file(s) to automatically reproduce all figures and tables in the paper, without manual interaction.

> NOTE: In-text numbers that reference numbers in tables do not need to be listed. Only in-text numbers that correspond to no table or figure need to be listed.

## All data files provided

The full list of data files is listed in the Appendix.

> INSTRUCTIONS: Please verify that the list in the appendix was created and is complete. If not, create the list by hand (instructions in the appendix)

## Computing Environment of the Replicator


> INSTRUCTIONS: This might be automated, for now, please fill in manually. Remove examples that are not relevant, adjust examples to fit special circumstances. Some of this is available from the standard log output in Stata or R. Some frequently used details are below. Some of these details can be found as follows:
>
> - (Windows) by right-clicking on "This PC"
> - (Mac) Apple-menu > "About this Mac"
> - (Linux) see code in `tools/linux-system-info.sh`
>
> Some options are listed below. Choose the one that applies.

- Mac Laptop M2 MacBook Pro, MacOS 10.14.6, 8 GB of memory, (M2 Processor, 8 cores)
- RedCloud Servers: Intel Xeon Processor (Skylake)   3.09 GHz  (18 processors), Installed Ram 176 GB, 64-bit operating system, x64-based processor
- CCSS Cloud: Windows Server AMD EPYC 7763 64-Core Processor 2.44 GHz, 128GB
- BioHPC Linux server, Rocky Linux 9.0, AMD Opteron Processor 6380 / 16 cores/ 125 GB memory (adjust as necessary from output of linux-system-info.sh)
- WholeTale (describe the environment chosen)
- CodeOcean (describe the type of capsule chosen) Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 cores), 128 GB Memory
- Bitbucket Pipelines, "Ubuntu 20.04.2 LTS", Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz, 8 cores, 9GB memory
- Codespaces, "Ubuntu 20.04.2 LTS", Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz, 2 core, 4GB/ 4-core, 8GB/ 8-core, 16 GB/ 16-core, 64GB (choose appropriately)


> INSTRUCTIONS: Please also list the software you used (specific versions). List only the ones you used, add any not listed in the examples:

- Stata/MP 18.0
- Matlab R2022a
- Intel Compiler 3.14152 (note: there is no such thing, so please verify the version!)

## Replication steps

> INSTRUCTIONS: provide details about your process of accessing the code and data.
> 
> - Do NOT detail things like "I save them on my Desktop".
> - DO describe actions that you did  as per instructions ("I added a config.do")
> - DO describe any other actions you needed to do ("I had to make changes in multiple programs"), without going into TOO much detail. (Link to the log file in the JIRA comments of this case!)
> 
> BUT:
> 
> - DO provide ENOUGH detail so that an author, without access to the logs, can understand what needed to be fixed, including a copy-paste of the error message.
> - DO commit to git before EACH new run with corrected code.
> - DO (after all debugging is completed) a full run through the data, top-to-bottom, once all bugs are fixed, using the approriate method (command line or right-click).

Example:

- Downloaded code and data from openICPSR provided.
- Added the config.do generating system information.
- Ran code as per README, but the third step did not work. (describe the problem HERE, but link to the logfile in the JIRA comments) (commit)
- Had to add undocumented package `distinct` to the install portion of the config file.  Ran again.
- Code failed because of a typo in the name of the file "`superdata.dta`" (was: `superdta.dta`). Fixed. Ran again.
- Code ran fine. 

> INSTRUCTIONS: ==>  Workflow stage: You are now going  to *Writing Report*. Verify that both PartA and PartB have been completed.

## Findings

> INSTRUCTIONS: Describe your findings both positive and negative in some detail, for each **Data Preparation Code, Figure, Table, and any in-text numbers**. You can re-use the Excel file created under *Code Description*. When errors happen, be as precise as possible. For differences in figures, provide both a screenshot of what the manuscript contains, as well as the figure produced by the code you ran. For differences in numbers, provide both the number as reported in the manuscript, as well as the number replicated. If too many numbers, contact your supervisor.


### Missing Requirements

> INSTRUCTIONS: If the replication package contains Stata programs run `tools/Stata_scan_code/scan_packages.do`, ensuring that you update the global `codedir` first. If the data is accessible, add any packages not mentioned in the README to the `config.do` and paste the excel output as a table below. If the data is restricted-access and not obtainable in a reasonable amount of time, paste the excel output as a table below.

> INSTRUCTIONS: If it turns out that some requirements were not stated/ are incomplete (software, packages, operating system), please list the *missing* list of requirements here. Remove lines that are not necessary. If the stated requirements are complete, delete this entire section, including the [REQUIRED] tag at the end.

- [ ] Software Requirements 
  - [ ] Stata
    - [ ] Version
    - Packages go here
  - [ ] Matlab
    - [ ] Version
  - [ ] R
    - [ ] Version
    - R packages go here
  - [ ] Python
    - [ ] Version
    - Python package go here
  - [ ] REPLACE ME WITH OTHER
- [ ] Computational Requirements specified as follows:
  - Cluster size, disk size, memory size, etc.
- [ ] Time Requirements 
  - Length of necessary computation (hours, weeks, etc.)

> [REQUIRED] Please amend README to contain complete requirements. 

You can copy the section above, amended if necessary.



### Data Preparation Code

Examples:

- Program `1-create-data.do` ran without error, output expected data
- Program `2-create-appendix-data.do` failed to produce any output.

### Tables

Examples:

- Table 1: Looks the same
- Table 2: (contains no data)
- Table 3: Minor differences in row 5, column 3, 0.003 instead of 0.3

### Figures

> INSTRUCTIONS: Please provide a comparison with the paper when describing that figures look different. Use a screenshot for the paper, and the graph generated by the programs for the comparison. Reference the graph generated by the programs as a local file within the repository.

Example:

- Figure 1: Looks the same
- Figure 2: no program provided
- Figure 3: Paper version looks different from the one generated by programs:

Paper version:
![Paper version](template/dog.jpg)

Figure 3 generated by programs:

![Replicated version](template/odie.jpg)

### In-Text Numbers

> INSTRUCTIONS: list page and line number of in-text numbers. If ambiguous, cite the surrounding text, i.e., "the rate fell to 52% of all jobs: verified".

[ ] In-text numbers not verified.

[ ] There are no in-text numbers, or all in-text numbers stem from tables and figures.

[ ] There are in-text numbers, but they are not identified in the code

- Page 21, line 5: Same


## Classification

> INSTRUCTIONS: Make an assessment here.
>
> Full reproduction can include a small number of apparently insignificant changes in the numbers in the table. Full reproduction also applies when changes to the programs needed to be made, but were successfully implemented.
>
> Partial reproduction means that a significant number (>25%) of programs and/or numbers are different.
>
> Note that if some data is confidential and not available, then a partial reproduction applies. This should be noted in the Reasons.
>
> Note that when all data is confidential, it is unlikely that this exercise should have been attempted.
>
> Failure to reproduce: only a small number of programs ran successfully, or only a small number of numbers were successfully generated (<25%). This also applies when all data is restricted-access and none of the **main** tables/figures are run.

- [ ] full reproduction
- [ ] full reproduction with minor issues
- [ ] partial reproduction (see above)
- [ ] not able to reproduce most or all of the results (reasons see above)

### Reason for incomplete reproducibility

> INSTRUCTIONS: mark the reasons here why full reproduciblity was not achieved, and enter this information in JIRA. When results are fully reproduced, leave this section here, and mark "None".

- [ ] None.
- [ ] `Discrepancy in output` (either figures or numbers in tables or text differ)
- [ ] `Bugs in code`  that  were fixable by the replicator (but should be fixed in the final deposit)
- [ ] `Code missing`, in particular if it  prevented the replicator from completing the reproducibility check
  - [ ] `Data preparation code missing` should be checked if the code missing seems to be data preparation code
- [ ] `Code not functional` is more severe than a simple bug: it  prevented the replicator from completing the reproducibility check
- [ ] `Software not available to replicator`  may happen for a variety of reasons, but in particular (a) when the software is commercial, and the replicator does not have access to a licensed copy, or (b) the software is open-source, but a specific version required to conduct the reproducibility check is not available.
- [ ] `Insufficient time available to replicator` is applicable when (a) running the code would take weeks or more (b) running the code might take less time if sufficient compute resources were to be brought to bear, but no such resources can be accessed in a timely fashion (c) the replication package is very complex, and following all (manual and scripted) steps would take too long.
- [ ] `Data missing` is marked when data *should* be available, but was erroneously not provided, or is not accessible via the procedures described in the replication package
- [ ] `Data not available` is marked when data requires additional access steps, for instance purchase or application procedure. 
- [ ] `Missing README` is marked if there is no README to guide the replicator, or the README is not in compliance with AEA requirements



> INSTRUCTIONS: ==>  Workflow stage: You are now going from  *Writing Report* to *Submitting Report*!

---

> INSTRUCTIONS: These appendixes will usually get filled automatically.

## Appendix: Candidate Stata packages (if any, based on scan)

{{ candidatepackages.md }}

## Appendix: Candidate R packages (if any, based on scan)

{{ r-deps-summary.md }}

## Appendix: Candidate Python packages (if any, based on scan)

{{ python-deps.md }}

## Appendix: Possible PII (if any, based on scan)

{{ pii_stata_output.md }}


## Appendix: Programs provided


> INSTRUCTIONS: Please verify that the following list is complete, if pre-filled.
> INSTRUCTIONS: You can generate a similar list manually, or add manually to this list.
> INSTRUCTIONS: For large deposits, this can be done using the "Git Bash" program:
> INSTRUCTIONS: > find . -name \*.R
> INSTRUCTIONS:  will list all R programs. Replace `R` with `.do` or any other extension to find other programs.

```
{{ programs-list.txt }}
```

## Appendix: Data files provided

> INSTRUCTIONS: Please verify that the following list is complete, if pre-filled.
> INSTRUCTIONS: You can generate a similar list manually, or add manually to this list.
> INSTRUCTIONS: For large deposits, this can be done using the "Git Bash" program:
> INSTRUCTIONS: > find . -name \*.dta
> INSTRUCTIONS:  will list all Stata datasets. Replace `dta` with `.Rdata` or any other extension to find other datafiles.

```
{{ data-list.txt }}
```
