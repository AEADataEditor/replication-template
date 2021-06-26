/* Template config.do */
/* Copy this file to your replication directory if using Stata, e.g.,
    cp template-config.do 12345/codes/config.do

   or similar, and then add

   include "config.do"

   in the author's main Stata program

   */

/* adjust this as necessary. This works on all OS when running in batch mode, but may not work in interactive mode */

local pwd : pwd
global rootdir "`pwd'"
global logdir "${rootdir}/logs"
cap mkdir "$logdir"

/* check if the author creates a log file. If not, adjust the following code fragment */

local c_date = c(current_date)
local cdate = subinstr("`c_date'", " ", "_", .)
local c_time = c(current_time)
local ctime = subinstr("`c_time'", ":", "_", .)

log using "$logdir/logfile_`cdate'-`ctime'-`c(username)'.log", name(ldi) replace text

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

/* add packages to the macro */

* *** Add required packages from SSC to this list ***
    local ssc_packages ""
    // local ssc_packages "estout boottest"
    
    if !missing("`ssc_packages'") {
        foreach pkg in `ssc_packages' {
            dis "Installing `pkg'"
            ssc install `pkg', replace
        }
    }

    * Install packages using net
    *  net install yaml, from("https://raw.githubusercontent.com/gslab-econ/stata-misc/master/")
    
/* other commands */

/* after installing all packages, it may be necessary to issue the mata mlib index command */
	mata: mata mlib index


set more off


