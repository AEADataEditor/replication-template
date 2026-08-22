# [MC number] [Manuscript Title] Validation and Replication results

> INSTRUCTIONS: This report can be used by Third Party Replicators. It is NOT a complete report, as the AEA staff will add additional information regarding data sources.

> INSTRUCTIONS: For more information on what it means to be a Third Party Replicator, please see the AEA policy at [https://www.aeaweb.org/journals/data/policy-third-party](https://www.aeaweb.org/journals/data/policy-third-party).

> INSTRUCTIONS: Once you've read these instructions, DELETE THESE AND SIMILAR LINES. Also delete lines that include "{{  SOME-TEXT }}".

> INSTRUCTIONS: In the above title, replace [Manuscript Title] with the actual title of the paper, and [MC number] with the Manuscript Central number (e.g., AEJPol-2017-0097)

> INSTRUCTIONS: Go through the steps to download and attempt a replication. Document your steps here, the errors generated, and the steps you took to alleviate those errors. This includes apparently minor steps, such as adjusting directories, or installing packages, any deviations from the README. If the README did not specify a certain step or action, describe why you chose that action, and whether it should be detailed in the README. All figures and tables should be evident once you are done, i.e., saved to disk. If this is not done in code, please add code to do so.

> INSTRUCTIONS: You should NOT communicate with the authors of the manuscript on anything other than how to obtain access to the data. If some communication is absolutely necessary, do so by email, and copy the Data Editor at dataeditor@aeapubs.org. Also note such communication in this report. 

> INSTRUCTIONS: To compare images and tables, annotated screenshots from the manuscript can be helpful for comparison, highlighting where differences were found. However, comply with all disclosure avoidance/ results release rules.

> INSTRUCTIONS: Once completed, send this file, any allowed log files and output, back to the requesting editor.

> INSTRUCTIONS: Fill out the following section:

## Affirmations

- [ ] I have identified any deviations from the PUBLIC README, noted any bugs (even minor) that needed to be fixed.
- [ ] I have not had any communications with the authors of this manuscript on this package ever, other than to coordinate access to data; OR
- [ ] I have had communications with the authors of this manuscript, and I copied the AEA Data Editor on all such communication; OR
- [ ] I have had communications with the authors of this manuscript, without involving the AEA Data Editor.


## Data description
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
## Replication steps


> INSTRUCTIONS: If there is an external reproducibility report (e.g., World Bank, cascad), please include it in the repository, and mention it here, and delete the other lines.

- [ ] The reproducibility check was conducted by a trusted third-party, see their appended report for details.

> INSTRUCTIONS: provide details about your process of accessing the code and data.
> 
> - Do NOT detail things like "I save them on my Desktop".
> - DO describe actions that you did as per instructions ("I added a config.do")
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

```
error: command distinct unknown
```

- Had to add undocumented package `distinct` to the install portion of the config file. Ran again.
- Code failed because of a typo in the name of the file "`superdata.dta`" (was: `superdta.dta`). Fixed. Ran again.
- Code ran to completion. 

{{ sivacor-partb-replication-steps.md }}


## Findings

> INSTRUCTIONS: Describe your findings both positive and negative in some detail, for each **Data Preparation Code, Figure, Table, and any in-text numbers**. You can re-use the Excel file created under *Code Description*. When errors happen, be as precise as possible. For differences in figures, provide both a screenshot of what the manuscript contains, as well as the figure produced by the code you ran. For differences in numbers, provide both the number as reported in the manuscript, as well as the number replicated. If too many numbers, contact your supervisor.

> INSTRUCTIONS: Even when there is an external reproducibility report, summarize the findings here. 

{{ sivacor-partb-findings.md }}

### Missing computational requirements

> INSTRUCTIONS: If the replication package contains Stata programs run `tools/Stata_scan_code/scan_packages.do`, ensuring that you update the global `codedir` first. If the data is accessible, add any packages not mentioned in the README to the `config.do` and paste the excel output as a table below. If the data is restricted-access and not obtainable in a reasonable amount of time, paste the excel output as a table below.

> INSTRUCTIONS: If it turns out that some requirements were not stated/ are incomplete (software, packages, operating system), check the *missing* item(s) in the checklist below; delete lines that are not missing/not relevant. This checklist must stay in the report — checked or unchecked as appropriate — whenever ANY computational requirement is missing; do not replace it with free-text prose instead. If the stated requirements are complete, delete this entire section (checklist and tags alike), and replace with "None".

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

> INSTRUCTIONS: For a missing setup program (e.g. a Stata/R/Python/Julia package not installed by any provided setup code), do NOT write a custom paraphrase of the request. Use the matching `[REQUIRED]` setup-program tag verbatim from the "Code" section of `sample-language-report.md` (one tag per language actually missing a setup program). You may append a short, untagged explanation directly below the tag limited to what's actually missing (e.g. the specific package name and which program required it) — do not restate what the README already covers.

> [REQUIRED] Please amend README to contain complete computational requirements.

This tag must ALWAYS be included, in addition to any setup-program tag(s) above, whenever any computational requirement is missing — it is not a substitute for the setup-program tag(s), nor are they a substitute for it.

You can copy the section above, amended if necessary.


### Data Preparation Code

Examples:

- Program `1-create-data.do` ran without error, output expected data
- Program `2-create-appendix-data.do` failed to produce any output.

### Tables and Figures

> INSTRUCTIONS: Insert the filled-out `code-check.xlsx` here (complete the column `Reproduced?`), using the VS Code Plugins [Excel to Markdown table](https://marketplace.visualstudio.com/items?itemName=csholmq.excel-to-markdown-table). Then describe in more detail the issues that may have arisen.

Examples:

- Table 1: Looks the same
- Table 2: (contains no data)
- Table 3: Minor differences in row 5, column 3, 0.003 instead of 0.3

> INSTRUCTIONS: For tables, simple comparisons can be listed out as above. More complex differences can be described by using screenshots of the original table and the reproduced table, highlighting the differences.
 
> INSTRUCTIONS: Please provide a comparison with the paper when describing that figures look different. Use a screenshot for the paper, and the graph generated by the programs for the comparison. Reference the graph generated by the programs as a local file within the repository.

Example:

- Figure 1: Looks the same
- Figure 2: no program provided
- Figure 3: Paper version looks different from the one generated by programs:

Paper version:
![Paper version](template/dog.jpg)

Figure 3 generated by programs:

![Replicated version](template/odie.jpg)
