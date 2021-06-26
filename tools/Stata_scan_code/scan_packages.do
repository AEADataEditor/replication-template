** Master file for text-mining based package search

***************************
* Step 1: Preliminaries   *
***************************
clear all

// Point to location of folder with .do files to scan for potential packages:
// Probably the only thing you need to change:

global codedir "U:/Documents/AEA_Workspace/aearep-1787/130804"
// Point to location of "scanning_framework" folder which contains scanning 
// code, package list, and stopwords & subwords files
// Might need to create an absolute path, but normally not necessary

local pwd : pwd
global rootdir "`pwd'"

// Set globals below
// Configure a few features. Probably not necessary unless you know what 
// you are doing.

global savefiles = 1 // Set to 1 if you want to save the list of files that was parsed. Useful
global createlog = 0 // If you wish to create a log file of the parsing/matching process,
global saveexcel = 1 // Set to 1 if you want to save the Excel report into the original directory (codedir)
global savehot   = 0 // Set to 1 if you want to save the "whatshot" report. Usually not needed.


//################## NO NEED TO CHANGE ANYTHING BELOW THIS ###############################
// DO NOT CHANGE Points to location of subwords and stopwords 
global auxdir "$rootdir/ado/auxiliary"

// Install packages, provide system info

global reportexcel "candidatepackages.xlsx"
if ( $saveexcel == 1 ) { 
	global reportfile "$codedir/$reportexcel"
}
else {
	global reportfile "$rootdir/$reportexcel"
}

/* It will provide some info about how and when the program was run */
/* See https://www.stata.com/manuals13/pcreturn.pdf#pcreturn */
local variant = cond(c(MP),"MP",cond(c(SE),"SE",c(flavor)) )  
// alternatively, you could use 
// local variant = cond(c(stata_version)>13,c(real_flavor),"NA")  

di "=== SYSTEM DIAGNOSTICS ==="
di "Stata version: `c(stata_version)'"
di "Updated as of: `c(born_date)'"
di "Variant:       `variant'"
di "Processors:    `c(processors)'"
di "OS:            `c(os)' `c(osdtl)'"
di "Machine type:  `c(machine_type)'"
di "=========================="


/* install any packages locally */
capture mkdir "$rootdir/ado"
sysdir set PERSONAL "$rootdir/ado/personal"
sysdir set PLUS     "$rootdir/ado/plus"
sysdir set SITE     "$rootdir/ado/site"
sysdir

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

********************************************************
* Step 2: Collect list of all packages hosted at SSC   *
********************************************************
// Collect top hits at SSC for the past month 
tempfile whatshot
tempfile packagelist

cap log close
log using "`whatshot'", replace text
* if the # of available packages ever exceeds 10000, adjust the line below
ssc whatshot, n(10000)
log close

// Data cleaning (import log file, export cleaned .dta file)

*May need to adjust the starting value for rowrange- target the first line where the first package is mentioned
import delimited whitespace rank hits packagename authors using "`whatshot'", rowrange(14:) delimiters("       ", collapse) clear

gen byte notnumeric = real(hits)==.
drop if notnumeric==1
drop authors-notnumeric
drop whitespace

destring rank, replace
destring hits, replace

label var rank "Package popularity (rank out of total # of packages)"

// Develop ranking system to help determine likelihood of false positives
sum hits, detail

* include prob of false positive if # of monthly hits for the package is below 90th percentile
gen probFalsePos = rank/_N if _n>`r(p90)' 
replace probFalsePos = 0 if _n<=`r(p90)'
label var probFalsePos "likelihood of false positive based on package popularity"
if ( $savehot == 1 ) {
	save "$rootdir/package_list" , replace
}

gen word = packagename 
sort word
save "`packagelist'"

// If you wish to create a log file of the parsing/matching process, set global "createlog" at top

if ( $createlog == 1 ) {
global logdir "${rootdir}/logs"
cap mkdir "$logdir"

local c_date = c(current_date)
local cdate = subinstr("`c_date'", " ", "_", .)
local c_time = c(current_time)
local ctime = subinstr("`c_time'", ":", "_", .)

log using "$logdir/logfile_`cdate'-`ctime'.log", replace text
}



***************************
* Step 3: Parsing	      *
***************************

*Parse each .do file in a directory, then append the parsed files

* Scan files in subdirectories
	tempfile file_list 
	filelist, directory("$codedir") pattern("*.do")
	gen temp="/"
	egen file_path = concat(dirname temp filename)
	save `file_list'
	keep file_path
	
qui count
	local total_files = `r(N)'
	forvalues i=1/`total_files' {
		local file_`i' = file_path[`i']
	}

* Read in each do file in the folder and split by line
forvalues i=1/`total_files' {
	di "file_`i'=`file_`i''"
	local v = "`file_`i''"
	
	infix str300 txtstring 1-300 using "`v'", clear

	* indexes each line
	gen line = _n
	* drop blank lines
	drop if txtstring == ""


	*drop commented lines (drop if //, *, /* or \* appears at the start of the line)
	drop if regexm(txtstring,"^//")==1
	drop if regexm(txtstring,"^/\*")==1
	drop if regexm(txtstring,"^\*")==1

	/* clean - this is handled by the stopword file as well */

	* split on common delimiters- txttool can't handle long strings
	replace txtstring = subinstr(txtstring,"\", " ",.)
	replace txtstring = subinstr(txtstring,"{", " ",.)
	replace txtstring = subinstr(txtstring,"}", " ",.)
	replace txtstring = subinstr(txtstring,"="," ",.)
	replace txtstring = subinstr(txtstring, "$"," ",.)
	replace txtstring = subinstr(txtstring, "/"," ",.)
	replace txtstring = subinstr(txtstring, "_"," ",.)
	replace txtstring = subinstr(txtstring, "*"," ",.)
	replace txtstring = subinstr(txtstring, "-"," ",.)
	replace txtstring = subinstr(txtstring, ","," ",.)
	replace txtstring = subinstr(txtstring, "+"," ",.)
	replace txtstring = subinstr(txtstring, "("," ",.)
	replace txtstring = subinstr(txtstring, ")"," ",.)
	replace txtstring = subinstr(txtstring, "#"," ",.)
	replace txtstring = subinstr(txtstring, "~"," ",.)
	replace txtstring = subinstr(txtstring, "."," ",.)
	replace txtstring = subinstr(txtstring, "<"," ",.)
	replace txtstring = subinstr(txtstring, ">"," ",.)
	
	
	* perform the txttool analysis- removes stopwords and duplicates
	txttool txtstring, sub("$auxdir/signalcommands.txt") stop("$auxdir/stopwords.txt") gen(bagged_words)  bagwords prefix(w_)

	* saves the results as .dta file (one for each .do file in the folder)
	save "$rootdir/parsed_data_`i'.dta", replace
 }

**********************
* Step 4: Matching 	 *
**********************

** Inputs: parsed .dta files from parsing code and list of freshly obtained ssc packages

** Outputs: list of missing packages


 *List all generated .dta files and append them to prepare for the match
 fs "parsed_data*.dta"
 append using `r(files)'
 
 
*Collapses unique words into 1 observation
collapse (sum) w_* 

* create a new var and count to capture frequency
gen word = ""
gen count = 0

*expand dataset again
global counter 0
foreach var of varlist w_* {
	/* add a row for the next variable */
	global counter = $counter +1
	set obs $counter
	/* capture word and its count */
    
	*capture the name of the variable and its frequency and do this for every variable, then drop all variables (collapses the unique variables)
	replace word = "`var'" if _n == $counter
	replace count = `var'  if _n == $counter
}
replace word = subinstr(word,"w_","",.)
drop w_*

sort word

// Cleanup
local datafiles : dir "$rootdir" files "parsed_data_*.dta"

foreach v in `datafiles' {
erase "`v'"
}


// Merge/match
sort word
merge 1:1 word using `packagelist' 
list if _merge==3

// More cleanup
cap erase "scanned_dofile.dta"

**************************************************************************
* Step 5: Export output & install found missing packages (if desired) 	 *
**************************************************************************

// Set up output export
gen matchedpackage = word if _merge==3
label var matchedpackage "(Potential) missing package found"
keep if matchedpackage !=""
gen confirmed_is_used = .

// Sort by rank (incorporates false positive probability) from packagelist file
gsort rank matchedpackage

// Export missing package list to Excel
export excel matchedpackage rank probFalsePos confirmed_is_used using "$reportfile", firstrow(varlabels) keepcellfmt replace sheet("Missing packages")

   * export file list to report
    if ( $savefiles == 1 ) {
	use `file_list', clear
	export excel dirname filename  using "$reportfile", firstrow(varlabels) keepcellfmt sheet("Programs parsed", modify)
	}

// Uncomment the section below to install all packages found by the match
** Warning: Will install all packages found, including false positives!

/*
levelsof matchedpackage, clean local(foundpackages)
    if !missing("foundpackages") {
        foreach pkg in `foundpackages' {
            dis "Installing `pkg'"
            ssc install `pkg', replace
        }
    }
*/

