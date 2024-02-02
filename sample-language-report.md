# Sample Language that may be used in the REPLICATION report

The following fragments may be used when reporting back on success or failure of a reproduction attempt. They usually identify lack of some key component. They should be added to the completed [REPLICATION.md](https://github.com/AEADataEditor/replication-template/blob/master/REPLICATION.md)

## Decisions

### the one you want to hear

**The replication package is accepted.**

### There might be some suggestions, but no requirements. Then the following section can be added.

If you wish to follow up on our suggestions, please follow [instructions on how to unlock/recall your replication package](https://aeadataeditor.github.io/aea-de-guidance/FAQ.html#you-can-recall-the-submission). Otherwise, no further action is required.

### the one almost as good during conditional acceptance

**Conditional on making the requested changes to the openICPSR deposit prior to publication, the replication package is accepted.**

(This means the author must still make a few changes to the openICPSR deposit, but the paper will be marked "accepted, forthcoming")


### the one is a bit more work at conditional acceptance

**Conditional on making the requested changes to the manuscript and the openICPSR deposit prior to publication, the replication package is accepted.**

(This means the author must still make a few changes to the openICPSR deposit, AND there are changes to the paper, but typically, these changes can be made to the paper during copy-editing, and the paper will be marked "accepted, forthcoming")

The following text is added to the "Manuscript" section:

> [REQUIRED] If making changes to the manuscript, please describe in a response letter to the Editor and Data Editor any deviations from the conditionally accepted version (as approved by the Editor) and their impact, especially of key estimates or outcomes. Email that response letter to the Data Editor at dataeditor@aeapubs.org, referencing the manuscript number.



### A warning which sometimes needs to be made explicit

There are quite a few items that still need resolution. However, we are confident that you will be able to address these issues in a timely fashion prior to publication of the manuscript. We note that the openICPSR deposit will not be in compliance with our policy until these items have been addressed.

### When we don't have time to run it.

> Even though we did not have time to run the code in this replication package before acceptance, we remind the authors that they remain responsible for the accuracy and consistency of the results produced by the code even after publication of the replication package. Our [Policy on Revisions of Data and Code Deposits in the AEA Data and Code Repository](https://www.aeaweb.org/journals/data/policy-revisions) applies to any corrections.

### When it just doesn't work: It remains in conditional accept

**We look forward to reviewing the final replication package after modifications.**

### For R&R that are mostly good to go:

**We look forward to reviewing the final replication package again after conditional acceptance.**

**The actions required to bring the package into conformance are simple enough, we do not need to see the package again until Conditional Acceptance.**

### For JEP and JEL that need to make changes

> In order to make changes, please "[recall the openICPSR deposit](https://aeadataeditor.github.io/aea-de-guidance/FAQ.html#you-can-recall-the-submission)", make changs, and re-submit. Do not create a new deposit.

### For external report

> The replication was attempted by a third-party trusted replicator.

## Info for summary

Pick and combine to create the summary:

> Thank you for your replication archive. 

> The article uses restricted-access data. Access to the data cannot be obtained in a timely fashion, a reproduction is not attempted. The report contains information on data description, and identifies whether all tables and figures can be identified in the code.

If we obtained data privately, and intend to re-run:

> The article uses restricted-access data, which the authors provided privately not-for-publication. 

If we obtained data privately, and are done (Accept, or Accept with changes):

> The article uses restricted-access data, which the authors provided privately not-for-publication. We will be in touch separately to confirm deletion of the data.

Other examples (adjust accordingly);

> Due to insufficient time available to the replicator, only a partial replication was completed. Thus, the report contains information on data description, identifies whether all tables and figures can be identified in the code, and notes the replication results of the partial replication.

> The replication package is accepted, pending one issue which can be addressed during copy-editing prior to publication. Since this only affects the README/code deposit/online appendix, this requires no further re-submission to Manuscript Central - a note will be added to the openICPSR repo, and publication is contingent on making the change.

> [NOTE] We are currently exploring expanded ways to highlight and facilitate reader-interaction with the computational code of an article. Your replication package seems to be compatible with our options. Please contact the AEA Data Editor if you are interested in this option (dataeditor@aeapubs.org).

Finish with


> In assessing compliance with our [Data and Code Availability Policy](https://www.aeaweb.org/journals/policies/data-code), we have identified the following issues, which we ask you to address:


## Temporary language

At the end of each summary, please include the following line:

> The openICPSR submission process has changed. If you have not already done so, please "Change Status -> Submit to AEA" from your deposit Workspace.

## README

> [SUGGESTED] A recommended README template for replication packages in economics can be found on the [Social Science Data Editor Github site](https://social-science-data-editors.github.io/guidance/template-README.html).

> [REQUIRED] Please ensure that a ASCII (txt), Markdown (md), or PDF version of the README are available in the data and code deposit.

## Data description

> [REQUIRED] Please provide this dataset

or if especially valuable

> [STRONGLY SUGGESTED] Please provide the cleaned  dataset as part of the archive, or a separate upload to an archive (Zenodo, Dataverse, ICPSR). In the latter case, cite it from there. See examples at [https://social-science-data-editors.github.io/guidance/Requested_information_hosting.html](https://social-science-data-editors.github.io/guidance/Requested_information_hosting.html), guidance at [https://social-science-data-editors.github.io/guidance/sample-depositing-data-for-greater-good.html](https://social-science-data-editors.github.io/guidance/sample-depositing-data-for-greater-good.html)

Note:
- openICPSR can handle files larger than 30GB, but you will need to request an increase in the quota from the Data Editor. Please specify total (uncompressed) data size and project number, and email dataeditor@aeapubs.org.

> [REQUIRED] Data are original (authors are data creators). Please cite the own data supplement, as per the [AEA Sample References](https://www.aeaweb.org/journals/policies/sample-references) and [additional guidance](https://aeadataeditor.github.io/aea-de-guidance/FAQ.html#how-do-i-cite-my-own-data-and-code-supplement).

> [REQUIRED] Please add data citations to the article. Guidance on how to cite data is provided in the [AEA Sample References](https://www.aeaweb.org/journals/policies/sample-references) and in [additional guidance](https://social-science-data-editors.github.io/guidance/addtl-data-citation-guidance.html).

> [REQUIRED] Please provide a clear description of access modality and source location for this dataset. Some examples are given [on this website](https://social-science-data-editors.github.io/guidance/Requested_information_dcas.html). 

Optionally:

- In particular, FRED provides a data citation at the bottom of each of its pages, e.g., for the CPI AUCNS, 

> U.S. Bureau of Labor Statistics, Consumer Price Index for All Urban Consumers: All Items in U.S. City Average [CPIAUCNS], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/CPIAUCNS, May 7, 2020. 


> [REQUIRED] Please provide a clear description of access modality and source location for this dataset. In particular, please provide evidence that you have the rights to redistribute the original and derived datasets.

> [REQUIRED] Please provide a clear description of access modality and source location for this dataset, including a description of which variables and options need to be selected from the URL provided.  

> [REQUIRED] Please provide a clear description of access modality and source location for this dataset. Please verify that your license allows you to redistribute Haver Analytics data.
For Haver Analytics, provide the "mnemonic" name. If a permission to redistribute these data has been obtained, store it within the openICPSR repository.

> [REQUIRED] Please provide a clear description of access modality and source location for this dataset. For Bloomberg data, provide the "ticker". If a permission to redistribute these data has been obtained, store it within the openICPSR repository.

### When data are private/ not provided 

The following may need to be added:


> [REQUIRED]  Please specify how long the data will be preserved in the restricted-access location.

> [REQUIRED] Please provide affirmation of support for replication checks.
  - As per the [AEA policy](https://www.aeaweb.org/journals/data/data-code-policy), "authors must commit to preserving data and code for a period of no less than five years following publication of the manuscript, and to providing reasonable assistance to requests for clarification and replication."

### If using World Development Indicators (WDI)

> [STRONGLY SUGGESTED] You use the WDI, but manually downloaded the data. We strongly suggest you use the API to formalize programmatically the download of the precise data series you used.
  - See https://datahelpdesk.worldbank.org/knowledgebase/articles/889464-wbopendata-stata-module-to-access-world-bank-data for more detail.

### If using NHGIS data:

> [NOTE] IPUMS has a new API system for creating (reproducible) extracts from NHGIS data. See [https://developer.ipums.org/docs/get-started/](https://developer.ipums.org/docs/get-started/). We strongly encourage you to Construct a valid JSON-formatted request, and provide that JSON file as part of the repository. Please feel free to reach out to IPUMS for assistance.

### If using general IPUMS data:

You may need these tags if the author did not provide their extract specification. Include the text right after the second tag as well.


> [REQUIRED] Please provide your IPUMS data extract.

> [REQUIRED] Please provide the IPUMS extract specification (the dofiles and DCT files provided with your extract).

Your replication package uses IPUMS data. Provision of extracts is required for sample (not full-count) files, and is compliant with [IPUMS Terms of Use](https://www.ipums.org/about/terms). 

For the extracts you generated, you should provide

- the dofile for read-in, e.g."usa_0028.do" and dct files
- for sample files, the actual extract (dat or dta files)

---

The pre-approver or the approver may decide to also add the following text:

IPUMS is trialling an API for extracts, which allows a user to export the extract specification, and for a replicator to re-use the extract specification programmatically. We encourage you to

- sign up for the beta (write to ipums+api@umn.edu and tell them you want to participate in the beta, and that the AEA Data Editor sent you)
- provide, as part of the repository, the JSON files you can download
- point to the IPUMS API pages as instructions for replicators to regenerate your extracts.

### If using Penn World Tables (PWT)

Typically, when authors use the PWT (there are multiple versions), they will include as citation

> Feenstra, Robert C., Robert Inklaar, and Marcel P. Timmer, “The Next Generation of the Penn World Table,” American Economic Review, 2015, 105 (10), 3150–3182.

However, that is not correct. The following text should be added to the report:

> [REQUIRED] Please add data citations to the article. Guidance on how to cite data is provided in the [AEA Sample References](https://www.aeaweb.org/journals/policies/sample-references) and in [additional guidance](https://social-science-data-editors.github.io/guidance/addtl-data-citation-guidance.html).
> - We understand that the above reference is the one requested by the data providers, however, it is wrong, and not compliant with AEA guidance and data citation principles. Please use the DOI on the page, with the correct year, to cite the data.
>
> Potential citation:
>
> > Feenstra, Robert C., Robert Inklaar and Marcel P. Timmer (2022), "Penn World Table version 10.0". Groningen Growth and Development Centre [distributor] https://doi.org/10.15141/S5Q94M, accessed on (DATE)


## General tags

> [REQUIRED] Please specify how long the data will be preserved in the restricted-access location.

> [SUGGESTED] The default AEA bibtex style file does not display URLs in the bibliography. A workaround might be to use the slightly modified [draft style file](https://github.com/AEADataEditor/aea-de-guidance/blob/master/citations/aea-mod.bst) or the `econ` style file referenced [here](https://www.aeaweb.org/journals/policies/random-author-order). 

> [REQUIRED] Please add a link to the full codebook to the README.

> [REQUIRED] Please ensure that all variables have labels, and that values are explained (have formats/codebook/etc.)

(used when dataset is primary, and raw data are not provided with the replication archive)

> [SUGGESTED] Please link to codebooks for these two datasets in the README.

(used when datasets are of secondary importance)

If data are provided in Numbers of Mathematica files: 

> [REQUIRED] Please provide this dataset in a preferred archive-ready format (CSV, TXT). If the data files also contain code (e.g. data & figure in a Numbers file), extract the data, save it separately as a CSV file, and add this to the repository (in addition to the original file).  

### PSID not allowed


> [REQUIRED] Per the [PSID website](https://psidonline.isr.umich.edu/Guide/FAQ.aspx?Type=8), you are not allowed to post extracts of their data to our archive. Please see details at [our FAQ](https://www.aeaweb.org/journals/data/faq#psid)

> [REQUIRED] Per the [PSID website](https://psidonline.isr.umich.edu/Guide/FAQ.aspx?Type=8), please include the following acknowledgement: 

    The collection of data used in this study was partly supported by the National Institutes of Health under grant number R01 HD069609 and R01 AG040213, and the National Science Foundation under award numbers SES 1157698 and 1623684.

### BLS confidential data used


> [REQUIRED] Per your BLS Data Use Agreement, you are required to include the following disclaimer in the title footnote: 

>  “This research was conducted with restricted access to Bureau of Labor Statistics (BLS) data. The views expressed here are those of the author and do not reflect the views of the BLS.” 

### Census Bureau confidential data

(add language for Census disclaimre)
> [REQUIRED] Per your Census Bureau Agreement, you are required to include the following disclaimer in the title footnote: 
 
> Any opinions and conclusions expressed herein are those of the authors and do not necessarily represent the views of the US Census Bureau.

> [REQUIRED] Please provide your Census Bureau DRB number authorizing the release of results and statistics from the Census Bureau or the FSRDC.


## PII suspected

> [REQUIRED] We have identified possible PII. Please verify, and if necessary, remove from deposit. If not removing, please explicitly confirm in your response letter that the identified variables are OK to publish without restrictions.

## Code

> [STRONGLY SUGGESTED] We strongly suggest to (a) create named releases on Github.com (using [semantic versioning](https://semver.org/)) (b) archive such releases, for instance through the [Github-Zenodo linkage](https://guides.github.com/activities/citable-code/) (c) cite the specific version corresponding to this article (for instance, using the Zenodo DOI)

> [REQUIRED] Please provide complete code, including for construction of the analysis data from raw data, and for appendix tables and figures, and identify source for inline numbers.

> [REQUIRED] Please provide a mapping of programs to figures/tables, or add comments to the code that identify where each figure/table is produced.

> [REQUIRED] Please add a setup program that installs all Stata packages. Please specify all necessary commands. An example of a setup file can be found at [https://gist.github.com/c3dddbcf73e7534a22e3583b3422d7c5](https://gist.github.com/c3dddbcf73e7534a22e3583b3422d7c5)

> [REQUIRED] Please add a setup program that installs all R packages. Please specify all necessary commands. An example of a setup file can be found at [https://github.com/labordynamicsinstitute/paper-template/blob/master/programs/global-libraries.R](https://github.com/labordynamicsinstitute/paper-template/blob/master/programs/global-libraries.R)

> [REQUIRED] Please provide a `requirements.txt` or `environment.yml` file  to   install all Python dependencies. Please specify all necessary commands (a link to the [`pip freeze`](https://pip.pypa.io/en/stable/cli/pip_freeze/) + [`pip install -r requirements.txt](https://pip.pypa.io/en/stable/cli/pip_install/) or [`conda env export`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#sharing-an-environment) reference may suffice).

> [REQUIRED] Please provide a `Manifest.toml` file to specify all dependencies for Julia. Some guidance is provided at the [QuantEcon](https://julia.quantecon.org/more_julia/tools_editors.html#Package-Environments) website. Alternatively, add a setup program that installs all Julia package, specifying all necessary commands. An example of a setup file can be found at [https://github.com/labordynamicsinstitute/paper-template/blob/master/programs/packages.jl](https://github.com/labordynamicsinstitute/paper-template/blob/master/programs/packages.jl)


> [REQUIRED] Please provide debugged code, addressing the issues identified in this report.

> [SUGGESTED] Please specify hardware requirements, and duration (execution time) for the last run, to allow replicators to assess the computational requirements.

> [REQUIRED] Please use packages or commands that automatically write out tables and figures.
  - NOTE: if importing data output from Stata into Excel to create figures, provide the Excel "shell" that is used. All programming languages can write output directly into Excel sheets.

> [REQUIRED] Please use programmatic data load statement instead of manual instructions to load data.

> [REQUIRED] Please set a random seed to allow for pseudo-random results to be exactly reproduced.

> [REQUIRED] Please provide code that creates all figures and tables without manual editing of parameters, for instance by using function calls, loops, or other mechanisms. The README should still provide instructions to replicators on how to further modify such parameters.

> [REQUIRED] Please provide instructions for figures generated via ArcGIS - in particular, the input data, and the manipulations made in order to generate the figure. Consider using ArcGIS ModelBuilder, ArcPy, or ArcGIS Pro Notebooks.

> [REQUIRED] Please provide code to produce the maps, or instructions on how to generate the maps. At a minimum, the source data should be identified, the source of the shape files recorded, and the processing steps described. 

When running the scanner, please review and provide suggested packages:

> [SUGGESTED] While running a [static code scanner for Stata](https://github.com/lydreiner/Statapackagesearch/), we identified  possible Stata packages used in your code. Please verify, and adjust requirements accordingly.

(copy and paste the top list)

## Results

> [REQUIRED] Please adjust your tables to account for the noted numerical discrepancies, or explain (in the README) discrepancies that a replicator should expect. 

> [REQUIRED] Please adjust your figures to account for the noted discrepancies, or explain (in the README) discrepancies that a replicator should expect. 


## RCT

> [REQUIRED] This is a RCT. The AEA requires that RCTs be registered, the registration number be **cited** in the title page footnote. For more details, see [AEA RCT policy](https://www.aeaweb.org/journals/policies/rct-registry) and the example citation provided in the [AEA Sample References](https://www.aeaweb.org/journals/policies/sample-references).


This is a RCT. The registration number is already identified in the title page footnote, but is not cited.

> [REQUIRED] Please cite the RCT wherever referenced (including title footnote). For more details, see the example citation provided in the [AEA Sample References](https://www.aeaweb.org/journals/policies/sample-references).

## IRB

> [REQUIRED] The data collection reported in this article seems to have required IRB approval. Please provide IRB approval information in the titlepage footnote, including protocol number and home institution of the IRB.

> [REQUIRED] The data collection reported in this article had IRB approval. Please provide full IRB approval information, including protocol number and home institution of the IRB, in the titlepage footnote.

> [REQUIRED] The data collection reported in this article had IRB approval. Please provide full IRB approval information, including protocol number, in the titlepage footnote.

## Experiment conducted


## Experimental instructions

The deposit does not seem to contain the required software/scripts to implement the experiment, though the appendix provides a complete verbose description thereof. As per the AEA's [Policy for Papers Conducting Experiments and Collecting Primary Data](https://www.aeaweb.org/journals/data/policy-experimental), please

> [REQUIRED] Provide any computer programs, configuration files, or scripts used to run the experiment or develop the survey instrument, e.g., z-Tree code, Qualtrics, SurveyCTO, and LimeSurvey.


## If no ICPSR deposit

> [REQUIRED] We note that you provided data during the R&R phase through Dropbox. When the paper is conditionally accepted, your code will need to be uploaded to openICPSR. Please preserve the same directory structure as we observed in this round. Import all ZIP files, unless discussed/authorized otherwise by the Data Editor. Please follow [our guidance](https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html#checklist).

## When there is no ICPSR deposit because there is a CodeOcean capsule

> [REQUIRED] Suggested language (for title footnote): "Data and code for this article can be found at AUTHORS (2022a), and a compute capsule is available at AUTHORS (2022b)." where AUTHORS (2022a) points to the openICPSR deposit DOI, and AUTHORS (2022b) points to the CodeOcean capsule.

(note also that presently, the content of the CodeOcean capsule should be mirrored to openICPSR)

## Relative to the openICPSR deposit

> [REQUIRED] Several required metadata elements are missing from the openICPSR deposit. Please consult our [additional deposit guidance](https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html)

> [SUGGESTED] Several suggested metadata elements are missing from the openICPSR deposit. Please consult our [additional deposit guidance](https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea-guidance.html)

> [REQUIRED]  ZIP files should be uploaded to openICPSR via "Import from ZIP" instead of "Upload Files" (there should be no ZIP files visible, except in rare approved circumstances). Please delete the ZIP files, and re-upload using the "Import from ZIP" function.

> [STRONGLY SUGGESTED] Please add the Github repository, or its archived equivalent, as a "Related Publication"

> [REQUIRED]  Please delete the `__MACOS` directory
    
> [REQUIRED]   Please delete empty directories
    
> [REQUIRED]   Please delete any redundant (obsolete) files

> [SUGGESTED] Please ensure that the README is in the root directory, and that unnecessary directory levels are pruned from the repository.

When authors are redistributing data or code from other authors that is not published and was obtained via personal correspondence. 

> [REQUIRED] Please create a "LICENSE" file in the repository, collecting the various permissions and licenses. A simple concatenation is fine. Paraphrasing is fine. Providing copies of the email correspondence in addition to the LICENSE file is fine. 

An example of a license file might start as follows:

```
Permission to redistribute data from Bateman and Munro (2005) was granted by Ian Bateman on May 26, 2019.

```

When there is evidence of a differing license in the deposit, there must be a "LICENSE.txt" file present.

> [REQUIRED] Please create a separate file called "LICENSE.txt" and add the text from the bottom of the README. This is necessary to let openICPSR recognize that the deposit is not subject to the standard CC-BY license.

## If the deposit is on OSF

> [REQUIRED] Please create an openICPSR deposit, as OSF is not a "trusted archive" (deposits are not fully preserved).

Instructions for creating a deposit can be found at https://aeadataeditor.github.io/aea-de-guidance/data-deposit-aea.html

## If the deposit has Git structure

> [REQUIRED] Please remove the Git-related directories from the openICPSR deposit. You can link the Github repo, if you wish, via the “related publications” link in the openICPSR deposit interface.

