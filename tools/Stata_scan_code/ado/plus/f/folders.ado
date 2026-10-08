*! NJC 1.0.0 20 November 2006 
* fs NJC 1.0.4 26 April 2004 
program folders, rclass   
	version 8

	if `"`0'"' == "" local 0 "." 

	local pwd    "`c(pwd)'" 
	local pwd2 : subinstr local pwd "\" "/", all 

	foreach f of local 0 {

		// all folders in pwd 
		if "`f'" == "." | inlist("`f'", "`pwd'", "`pwd2'") { 
			local folders : dir . dirs "*" 
		} 	
		else {
			// folder specification 
			if index("`f'", "/") | ///
			index("`f'", "\")    | ///
			index("`f'", ":")    | ///
			inlist(substr("`f'", 1, 1), ".", "~") { 
				ParseSpec `f'

				//  wildcard 
				if index("`f'", "*") | index("`f'", "?") { 
					local folders : dir "`d'" dirs "`f'"
				}
				// not a wildcard 
				else local folders : dir "`d'`f'" dirs "*" 
			} 	
			// no folder specification 
			else { 
				// wildcard 
				if index("`f'", "*") | index("`f'", "?") { 
					local folders : dir . dirs "`f'" 
				}
				// not a wildcard 
				else local folders : dir "`f'" dirs "*" 
			} 	
		}
		local Folders "`Folders'`folders' "
	} 

	DisplayInCols res 0 2 0 `Folders' 
	if trim(`"`Folders'"') != "" {
		return local folders `"`Folders'"' 
	}	
end 	

program ParseSpec
	args f 

	// first we need to strip off directory or folder information 

	// if "/" or "\" occurs we want to know where the 
	// last occurrence is -- which will be the first in 
	// the reversed string 
	local f : subinstr local f "\" "/", all 
	local where = index(reverse("`f'"), "/")

	// map to position in original string and 
	// extract the directory or folder 
	local where = min(length("`f'"), 1 + length("`f'") - `where') 
	local d = substr("`f'", 1, `where') 

	// absolute references start with "/" or "\" or "." or "~" 
	// or contain ":"  
	local abs = inlist(substr("`f'", 1, 1), "/", ".", "~") 
	local abs = `abs' | index("`f'", ":")
	
	// prefix relative references 
	if !`abs' local d "./`d'" 
	
	// fix references to root 
	else if "`d'" == "/" | "`d'" == "\" { 
		local pwd "`c(pwd)'" 
		local pwd : subinstr local pwd "\" "/", all 
		local d = substr("`pwd'", 1, index("`pwd'","/"))
	} 
	
	// absent foldername list 
	if "`f'" == "`d'" local f "*" 
	else              local f = substr("`f'", `= `where' + 1', .)

	//  return to caller
	c_local f "`f'"
	c_local d "`d'" 
end 

program DisplayInCols /* sty #indent #pad #wid <list>*/
	gettoken sty    0 : 0
	gettoken indent 0 : 0
	gettoken pad    0 : 0
	gettoken wid	0 : 0

	local indent = cond(`indent'==. | `indent'<0, 0, `indent')
	local pad    = cond(`pad'==. | `pad'<1, 2, `pad')
	local wid    = cond(`wid'==. | `wid'<0, 0, `wid')
	
	local n : list sizeof 0
	if `n'==0 { 
		exit
	}

	foreach x of local 0 {
		local wid = max(`wid', length(`"`x'"'))
	}

	local wid = `wid' + `pad'
	local cols = int((`c(linesize)'+1-`indent')/`wid')

	if `cols' < 2 { 
		if `indent' {
			local col "column(`=`indent'+1)"
		}
		foreach x of local 0 {
			di as `sty' `col' `"`x'"'
		}
		exit
	}
	local lines = `n'/`cols'
	local lines = int(cond(`lines'>int(`lines'), `lines'+1, `lines'))

	/* 
	     1        lines+1      2*lines+1     ...  cols*lines+1
             2        lines+2      2*lines+2     ...  cols*lines+2
             3        lines+3      2*lines+3     ...  cols*lines+3
             ...      ...          ...           ...               ...
             lines    lines+lines  2*lines+lines ...  cols*lines+lines

             1        wid
	*/


	* di "n=`n' cols=`cols' lines=`lines'"
	forvalues i=1(1)`lines' {
		local top = min((`cols')*`lines'+`i', `n')
		local col = `indent' + 1 
		* di "`i'(`lines')`top'"
		forvalues j=`i'(`lines')`top' {
			local x : word `j' of `0'
			di as `sty' _column(`col') "`x'" _c
			local col = `col' + `wid'
		}
		di as `sty'
	}
end
