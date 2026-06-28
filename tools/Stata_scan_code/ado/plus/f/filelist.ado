*! version 2.0.7  08jun2015 Robert Picard, picard@netbox.com
program define filelist

	version 9.2
	
	syntax , ///
		[ ///
		Directory(string) ///
		List ///
		Pattern(string) ///
		noRecursive ///
		MAXdeep(string) ///
		replace ///
		Save(string) ///
		]

	// default to all files pattern if not specified
	if "`pattern'" == "" local pattern "*"
	
	// default to current directory if not spefified
	if "`directory'" == "" local directory "."
	
	// default is to search all subdirectories recursively
	if "`maxdeep'" == "" local maxdeep .
	
	if "`recursive'" == "norecursive" local maxdeep 1
	
	cap assert `maxdeep' > 0
	if _rc {
		dis as err "maxdeep must be > 0"
		exit _rc
	}
	
	// if we are saving results to disk, preserve data in memory
	if "`save'" != "" preserve
	
	
	drop _all
	gen dirname = ""
	gen filename = ""
	gen double fsize = .
		
	
	mata: filelist_recur("`directory'", "`pattern'", `maxdeep')
	
	
	qui compress
	qui leftalign
	format %15.0fc fsize
	sort dirname filename
	
	
	dis as txt "Number of files found = " as res _N


	if "`list'" != "" {
		gen filepath = dirname + "/" + filename
		qui leftalign filepath
		list filepath fsize, noobs sepby(dirname)
		drop filepath
	}
	
	
	if "`save'" != "" save "`save'", `replace'
	
end


// local copy of -leftalign-; version on SSC as of 20140921
// *! version 2.0.3, 09sep2014, Robert Picard, picard@netbox.com      
program define leftalign

	version 9.2
	
	syntax [varlist] , [Label All]
	
	foreach v of varlist `varlist' {
	
		if "`all'" != "" local doit 1
		else local doit 0
		
		
		if "`label'" != "" {
			if "`: value label `v''" != "" local doit 1		
		}
	
		// do all string variables
		local f : format `v'
		if regexm("`f'", "^%.+s$") local doit 1
		
		if `doit' {
		
			// strip the "%", "%-", or "%~" prefix
			local ff = regexr("`f'", "^%~?\-?","")
		
			// ignore error if the left-aligned format is not legal		
			cap format %-`ff' `v'
		
			// check for change vs. original format
			if "`: format `v''" != "`f'" local vlist `vlist' `v'
			
		}
		
	}
	
	if "`vlist'" != "" des `vlist'
		
end


version 9.2
mata:
mata set matastrict on

void filelist_recur(

	string scalar currentdir,
	string scalar pattern,
	real scalar level
	
)
{

	string colvector filelist, dirlist
	real scalar i, obs, wdir, wfiles, first, last, nfiles
	real colvector filesize
	
	
	filelist = dir(currentdir, "files", pattern)
	nfiles = rows(filelist)
	
	if (nfiles) {
	
		wdir = strlen(currentdir)
		wfiles = colmax(strlen(filelist))
		
		first = st_nobs() + 1
		st_addobs(nfiles)
		last = st_nobs()
		
		strlen_check("dirname",wdir)
		strlen_check("filename",wfiles)
		
		st_sstore((first,last), (1,2), (J(nfiles, 1, currentdir), filelist))
		
		filesize = J(nfiles, 1, .)
		for (i=1; i<=nfiles; i++) {
			
			filesize[i] = get_file_size(currentdir + "/" + filelist[i])
			
		}
		
		st_store((first,last), 3, filesize)
		
	}
	
	
	if (level > 1) {
	
		dirlist  = dir(currentdir, "dirs", "*")
	
		for (i=1; i<=rows(dirlist); i++) {
		
			level--
	
			filelist_recur(currentdir + "/" + dirlist[i], pattern, level)
			
			level++
			
		}
		
	}
	
}


void strlen_check(

	string scalar varname,
	real scalar wneed
	
)
{

	real scalar wnow, maxslen


	// as of Stata 13, strL can accomodate 2,000,000,000 characters
	if (st_vartype(varname) != "strL") {
	
		// as of Stata 13, this is 2045; prior version was 244
		maxslen = st_numscalar("c(maxstrvarlen)")
		
		// recast to strL if available
		if (wneed > maxslen) {
		
			if (maxslen == 244) {
				printf("{err}directory path is too long, ")
				printf("requires %f characters while max is %f{txt}\n",wneed,maxslen)
				exit(109)
			}
			
			stata(sprintf("qui recast strL %s", varname))

		}
		
		// note that strL will come out as . (missing)
		wnow = strtoreal(substr(st_vartype(varname), 4, .))
		
		if (wneed > wnow) {
			stata(sprintf("qui recast str%f %s", wneed, varname))
		}
		
	}
}


real scalar get_file_size(

	string scalar fname
	
)
{
	
	real scalar fh, fsize, filepos
	
	fh = fopen(fname, "r")
	
	// go to the end of the file; returns negative error codes
	filepos = _fseek(fh, 0, 1)
	
	if (filepos >= 0) fsize = ftell(fh)
	
	fclose(fh)
	
	return(fsize)

}


end

