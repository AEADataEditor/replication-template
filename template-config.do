/* Template config.do */
/* Copy this file to your replication directory if using Stata, e.g.,
    cp template-config.do 12345/codes/config.do

   or similar, and then add

   include "config.do"

   in the author's main Stata program

   */

/* Structure of the code, two scenarios:
   - Code looks like this (simplified, Scenario A)
         directory/
              code/
                 main.do
                 01_dosomething.do
              data/
                 data.dta
                 otherdata.dta
   - Code looks like this (simplified, Scenario B)
         directory/
               main.do
               scripts/
                   01_dosomething.do
                data/
                   data.dta
                   otherdata.dta
 - Code looks like this (simplified, Scenario C - like A, but with an additional level of directories)
         directory/
	   step1/
               scripts/
                   main.do
                   01_dosomething.do
           step2/
	       scripts/
	           othermain.do
		   01_analysis.do
           data/
               data.dta
               otherdata.dta
    For the variable "scenario" below, choose "A" or "B" (or seldomly "C"). It defaults to "A".

    NOTE: you should always put "config.do" in the same directory as "main.do"
*/

local scenario "A" 
* *** Add required packages from SSC to this list ***
local ssc_packages ""
    // Example:
    // local ssc_packages "estout boottest"
    // If you need to "net install" packages, go to the very end of this program, and add them there.

/* Authors may provide us with adofiles. The path should be added here, relative to the root 
   of the replication package.
   For instance, if (after LDI-specific setup) 
   the replication package is "aearep-1234/123456/Replication package"
   and the authors provide ado files in "aearep-1234/123456/Replication package/Ado-files"
   then you would enter "Ado-files" in the local definition below.
*/

local author_adopath ""


/* This works on all OS when running in batch mode, but may not work in interactive mode */
local pwd : pwd                     // This always captures the current directory

if "`scenario'" == "A" {             // If in Scenario A, we need to change directory first
    cd ..
}
if "`scenario'" == "C" {             // If in Scenario C, we need to go up twice
    cd ../..
}
global rootdir : pwd                // Now capture the directory to use as rootdir
display in red "Rootdir has been set to: $rootdir"


/*================================================================================================================*/
/*                            You normally need to make no further changes below this                             */
/*                             unless you need to "net install" packages                                          */

set more off
cd "`pwd'"                            // Return to where we were before and never again use cd
global logdir "${rootdir}/logs"
cap mkdir "$logdir"

/* check if the author creates a log file. If not, adjust the following code fragment */

local c_date = c(current_date)
local cdate = subinstr("`c_date'", " ", "_", .)
local c_time = c(current_time)
local ctime = subinstr("`c_time'", ":", "_", .)
local ldilog = "$logdir/logfile_`cdate'-`ctime'-`c(username)'.log"
local systeminfo = "$logdir/system_`cdate'-`ctime'-`c(username)'.log"

/* global logfile */
log using "`ldilog'", name(ldi) replace text

/* used only for system info */
log using "`systeminfo'", name(system) replace text

/* It will provide some info about how and when the program was run */

/* install any packages locally */
di "=== Redirecting where Stata searches for ado files ==="
capture mkdir "$rootdir/ado"
adopath - PERSONAL
adopath - OLDPLACE
adopath - SITE
sysdir set PLUS     "$rootdir/ado/plus"
sysdir set PERSONAL "$rootdir/ado"       // may be needed for some packages
sysdir

/*==============================================================================================*/
/* If present, add the authors' replication-package specific ado file path                      */
/* This is defined above                                                                        */
/*==============================================================================================*/

if "`author_adopath'" != "" {             // The author adopath variable is filled out
    adopath ++ "$rootdir/`author_adopath'"
}

/* now let's check what's there */

di "=== Verifying pre-existing ado files - normally, this should be EMPTY upon first run"
adopath
ado
di "=========================="


/* this is long, so we pause the main log file */
log off ldi

di "=== SYSTEM DIAGNOSTICS ==="
creturn list
query
di "=========================="

/* we're done collecting system info */
log close system
log on ldi


/* add packages to the macro */

    
    if !missing("`ssc_packages'") {
        foreach pkg in `ssc_packages' {
            capture which `pkg'
            if _rc == 111 {                 
               dis "Installing `pkg'"
                ssc install `pkg', replace
            }
            which `pkg'
        }
    }

/*==============================================================================================*/
/* If you need to "net install" packages, add lines to this section                             */
    * Install packages using net
    * net install grc1leg, from("http://www.stata.com/users/vwiggins/")
    
/*==============================================================================================*/
/* other commands, rarely used, uncomment as needed */
/* Some packages do not contain a command with the same name as the package, and thus cannot be verified by "which" */
/*==============================================================================================*/

/* if needing egenmore, uncomment next line. egenmore cannot be verified by "which" . There are some other packages like that*/

// ssc install egenmore
// ssc install blindschemes

/*==============================================================================================*/
/* yet other programs have no install capability, and may need to be copied */
/*==============================================================================================*/

// e.g.
//  copy (URL) (name_of_file.ado)
// example:
// copy http://www.sacarny.com/wp-content/uploads/2015/08/ebayes.ado ebayes.ado


/*==============================================================================================*/
/* This toolbox allows us to run code that still contains interactive commands (which it should not) */
/*==============================================================================================*/

net install cli-compat, all replace from("https://raw.githubusercontent.com/aeadataeditor/cli-compat-stata/master")

/*-------------- Sometimes, you may get the dreaded esttab error about paths -------------------*/
/* in that case, uncomment the following line, and overwrite the estout package with the newer one */

// net install estout, replace from(https://raw.githubusercontent.com/benjann/estout/master/)

/*==============================================================================================*/
/* after installing all packages, it may be necessary to issue the mata mlib index command */
/* This should always be the LAST command after installing all packages                    */
/*==============================================================================================*/

	mata: mata mlib index

/*==============================================================================================*/
/* This is specific to AEA replication environment. May not be needed if no confidential data   */
/* are used in the reproducibility check.                                                       */
/* Replicator should check the JIRA field "Working location of restricted data" for right path  */
/*==============================================================================================*/

global sdrive ""


/*==============================================================================================*/
/* After all the setup work, let's check again what's installed in the ado directories          */
/*==============================================================================================*/


di "=== Verifying ado files after all install steps"
adopath
ado
di "=========================="



di "========================================= END SETUP + DIAGNOSTICS ===================================="
