** Master file for text-mining based package search

***************************
* Step 1: Preliminaries   *
***************************
clear all

// Point to location of folder with .do files to scan for potential packages:
// Probably the only thing you need to change:

global codedir "XXXCODEDIRXXX"

if "`1'" != "" global codedir "`1'"
// Point to location of "scanning_framework" folder which contains scanning 
// code, package list, and stopwords & subwords files
// Might need to create an absolute path, but normally not necessary


di "=== SYSTEM DIAGNOSTICS ==="
di "Stata version: `c(stata_version)'"
di "Updated as of: `c(born_date)'"
di "Variant:       `variant'"
di "Processors:    `c(processors)'"
di "OS:            `c(os)' `c(osdtl)'"
di "Machine type:  `c(machine_type)'"
di "=========================="


adopath - PERSONAL     
adopath - SITE    
adopath

net install packagesearch, from("https://aeadataeditor.github.io/Statapackagesearch/")
// If you have issues, create a branch to fix the problem, and install from there:
//net install packagesearch, from("https://raw.githubusercontent.com/AEADataEditor/Statapackagesearch/issue-x/")

/* add necessary packages to perform the scan & analysis to the macro */

* *** Add required packages from SSC to this list ***
    local ssc_packages "fs filelist txttool"
    
    if !missing("`ssc_packages'") {
        foreach pkg in `ssc_packages' {
            dis "Installing `pkg'"
            ssc install `pkg', replace
        }
    }

/* after installing all packages, it may be necessary to issue the mata mlib index command */
	mata: mata mlib index


set more off
set maxvar 120000

packagesearch, codedir("$codedir") excelsave csvsave filesave
