# [MC number] [Manuscript Title] Validation and Replication results


> Some useful links:
> - [Official Data and Code Availability Policy](https://www.aeaweb.org/journals/policies/data-code)
> - [Step by step guidance](https://aeadataeditor.github.io/aea-de-guidance/) 
> - [Template README](https://social-science-data-editors.github.io/template_README/)

## SUMMARY

Thank you for submitting the replication package. At this time, the deposit is not compliant, and we have not made an assessment. We provide guidance on how to make a compliant deposit, in line with the [Official Data and Code Availability Policy](https://www.aeaweb.org/journals/policies/data-code), the required  [Template README](https://social-science-data-editors.github.io/template_README/). We provide extensive [Step by step guidance](https://aeadataeditor.github.io/aea-de-guidance/), which we suggest you consult.


> If your openICPSR deposit appears to be "locked", please follow [these instructions](https://aeadataeditor.github.io/aea-de-guidance/FAQ.html#you-can-recall-the-submission).

> The openICPSR submission process has changed. If you have not already done so, please "Change Status -> Submit to AEA" from your deposit Workspace.


## General


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
  - Please treat the above as a checklist.

> We found no README in the deposit. The README should have all the above elements in order to be compliant.


### Requirements 

- [ ] README is in TXT, MD, PDF format
- [ ] Deposit has no ZIP files
- [ ] Title conforms to guidance (starts with "Data and Code for:" or "Code for:", is properly capitalized)
- [ ] Authors (with affiliations) are listed in the same order as on the paper

> Detailed guidance is at [https://aeadataeditor.github.io/aea-de-guidance/](https://aeadataeditor.github.io/aea-de-guidance/), for non-ICPSR deposits, check out [this guidance](https://aeadataeditor.github.io/aea-de-guidance/guidelines-other-repositories).

### Deposit Metadata


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

- [NOTE] openICPSR metadata is sufficient.

> [SUGGESTED] We suggest you update the openICPSR metadata fields marked as (highly recommended), in order to improve findability of your data and code supplement. 
> [SUGGESTED] We suggest you update the openICPSR metadata fields marked as (suggested), in order to improve findability of your data and code supplement. 


For additional guidance, see [https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html](https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html).


## Code description

- [ ] The replication package contains a "main" or "master" file(s) which calls all other auxiliary programs.

> [SUGGESTED] We strongly advise the use of a single (or a small number of) main control file(s) to automatically reproduce all figures and tables in the paper, without manual interaction.


## Missing Requirements

- [ ] Software Requirements 
  - [ ] Matlab
    - [ ] Version
- [ ] Computational Requirements specified as follows:
  - Cluster size, disk size, memory size, etc.
- [ ] Time Requirements 
  - Length of necessary computation (hours, weeks, etc.)

> [REQUIRED] Please amend README to contain complete requirements. 


## Classification

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
- [x] not able to reproduce most or all of the results (reasons see above)

### Reason for incomplete reproducibility


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


