/*********************************************************************************************************************************************
Description: This file will scan all .dta files within a directory and all of its subdirectories for potential PII. Potential PII includes 
variables with names or labels containing any of the strings in global search_string. The program decodes all encoded numeric variables (i.e. 
those with value labels or those created using the command "encode") to create string variables, which are searched along with all original 
string variables for variables with string lengths greater than 3 (or user-defined length). Flagged variables are saved to pii_stata_output.csv. 

Inputs: Path to top directory.
Outputs: pii_stata_output.csv (saved to current working directory)
Date Last Modified: May 24, 2018
Minor modifications: April 2, 2020 (lars.vilhuber@cornell.edu)
Last Modified By: Marisa Carlos (mcarlos@povertyactionlab.org)
**********************************************************************************************************************************************/

*version 15.1
clear all
set more off 
set maxvar 12000


 // CHANGE PATH TO WHERE YOU WANT TO SAVE pii_stata_output.csv

global directory_to_scan "." // SET THIS DIRECTORY TO THE ONE YOU WANT TO SCAN (change options at botton of do-file)
global rootdir : pwd

if "`1'" != "" global directory_to_scan "`1'"
if "`2'" != "" global rootdir "`2'"

cap mkdir "${rootdir}/ado"
sysdir set PERSONAL "$rootdir/ado/personal"
sysdir set PLUS "$rootdir/ado/plus"


cd "$directory_to_scan"

***Command "filelist" required:
capture ssc install filelist


****************************** ADD OR REMOVE SEARCH STRINGS AS NEEDED: ******************************
#delimit ;
global search_strings
	address
	bday
	beneficiary
	birth 
	block
	cell
	census
	child
	city
	community
	compound
	coord
	country
	district
	daughter
	email
	father
	fax
	gender
	gps
	house
	husband
	landline
	latitude
	location
	longitude
	mother
	municipality
	name
	network
	panchayat
	parish
	phone 
	precinct
	school
	sex
	social
	spouse 
	street
	subcountry
	territory
	village
	wife
	zip
;

global strict_search_strings
	url
	son
	dob
	loc
;
#delimit cr;
*****************************************************************************************************

capture program drop pii_scan
program pii_scan
	syntax anything(name=search_directory id="path of directory to search")[, remove_search_list(string) add_search_list(string) ignore_varname(string) string_length(integer 3) samples(integer 5) time]
	/*
	EXPLANATION OF INPUTS:
		search_directory = path of directory to search 
		remove_search_list = list of strings to remove from the search list (e.g. if you don't want to search for string with "zip" or "wife" in the name or label, use 
							 option remove_search_list(zip wife)
		add_search_list = list of strings to add to the search list (e.g. if you also want to search for "person" in name/label, use option add_search_list(person)
		ignore_varname = A list of strings such that if there are any variables flagged with any of these strings in the VARIABLE NAME, they will NOT be output to the CSV file 
				(e.g. if you don't want any variables with the word "materials" to be output to pii_stata_output.xlsx, use option "ignore(materials)"). 
				NOTE: This does not ignore the word if it is only found in the variable label.
		string_length = the cutoff length for the strings you want to be flagged. The default is 3 (i.e. strings with lengths greater than 3 will be output to CSV file)
		samples = number of samples to output to CSV, default is 5
		time = display time takes to run do-file (start time and end time)
	*/
	if !missing("`time'") {
		local start_time = c(current_time)
	}
	
	*make list of user defined search strings to ignore lowercase:
	local ignore_strings
	foreach search_string of local remove_search_list {
		local string_lower = lower("`search_string'")
		local ignore_strings "`ignore_strings' `string_lower'"
	}
	*make list of user defined search strings to add lowercase:
	local add_strings
	foreach search_string of local add_search_list {
		local string_lower = lower("`search_string'")
		local add_strings "`add_strings' `string_lower'"
	}
	
	*Remove strings user defined from search list:
	global final_search_list : list global(search_strings) - ignore_strings
	
	*Add strings user defined to search list:
	global final_search_list : list global(final_search_list) | add_strings
	*Make sure list only contains unique values: 
	global final_search_list : list uniq global(final_search_list)
	
	tempfile file_list 
	filelist, directory(`search_directory') pattern("*.dta")
	gen temp="/"
	egen file_path = concat(dirname temp filename)
	keep file_path
	save `file_list'

	qui count
	local total_files = `r(N)'
	forvalues i=1/`r(N)' {
		local file_`i' = file_path[`i']
	}

	capture file close output_file
	file open output_file using pii_stata_output.csv, write replace text
	
	foreach header in "file" "var" "varlabel" "most freq value" "unique values" "total obs" {
		file write output_file _char(34) `"`header'"' _char(34) ","
	}
	forvalues i=1/`samples' {
		file write output_file _char(34) `"samp`i'"' _char(34) ","
	}
	file write output_file _n
	
	local total_variables = 0 // used to count/display total number of variables at end
	local total_variables_flagged = 0 // used to count/display number of FLAGGED variables at the end

	local backtick `"`"'
	qui count
	forvalues i=1/`r(N)' {
		use "`file_`i''", clear
		qui count 
		local N = r(N) // USED WHEN OUTPUTING TO CSV
		***Initialize locals:
		local decoded_vars_original
		local decoded_vars_renamed
		local vars_output_csv
		local strings_to_output
		local string_vars
		local numeric_vars 
		local all_vars
		local flagged_vars
		
		*Drop any variables with strings in the user defined "ignore" list:
		foreach ignore_string of local ignore_varname {
			foreach var of varlist * {
				local var_name = lower("`var'")
				local lower_ignore_string = lower("`ignore_string'")
				local ignore_name_pos = strpos("`var_name'","`lower_ignore_string'")
				if `ignore_name_pos'!=0 {
					drop `var'
				}
			}
		}
		
		foreach var of varlist * {
			local ++total_variables
			local all_vars "`all_vars' `var'"
		}

		*** Decode all of the string variables that are encoded (this creates a string variable that takes on the values of the value labels) 
		foreach var of varlist * {
			*** If the variable name is longer than 31 character, need to substring to get the first 31 letters so can add on DCD
			if length("`var'")>31 {
				local var_prefix = substr("`var'",1,31)
			}
			else {
				local var_prefix "`var'"
			}
			capture decode `var', gen(`var_prefix'DCD)
			if _rc==0 { // if the variable is successfully decoded (i.e. it has a value label):
				*** Make sure that the decoded variable is not missing for all obs 
				*   - if it is missing then there is a value label associated with this variable but none of the numeric values the variable takes correspond to 
				*   the strings in the value label:
				qui count
				local n1=r(N)
				qui count if mi(`var_prefix'DCD)
				local n2=r(N)
				
				*If the decoded variable is NOT missing for all observations, add it to list of decoded variables: 
				if `n1'!=`n2' {
					local decoded_vars_original "`decoded_vars_original' `var'"
					local decoded_vars_renamed "`decoded_vars_renamed' `var_prefix'DCD"
				}
				else {
					drop `var_prefix'DCD
				}
			}
		}
		if "`decoded_vars_original'"!="" {
			local j=0
			foreach orig_var of local decoded_vars_original {
				local ++j
				local k=0
				foreach new_var of local decoded_vars_renamed {
					local ++k
					if `j'==`k' {
						drop `orig_var'
						rename `new_var' `orig_var'
					}
				}
			}
		}
		
		***Get list of all string variables (this will include original string variables and the decoded variables) 
		foreach var of varlist * {
			capture confirm string var `var'
			if _rc==0 {
				local string_vars "`string_vars' `var'"
			}
			else {
				local numeric_vars "`numeric_vars' `var'"
			}
		}
		
		
		*** Search through ALL the variables to see if there is a PAIR of variables for lat/lon:
		*First see if there are two variables "lat" and "lon" anywhere in the datafile:
		local lat = 0
		local lon = 0
		foreach var of local all_vars {
			if lower("`var'")=="lat" {
				local lat = 1
				local lat_var "`var'"
			}
			if lower("`var'")=="lon" {
				local lon = 1
				local lon_var "`var'"
			}
		}
		if `lat'==1 & `lon'==1 {
			local flagged_vars "`lat_var' `lon_var'"
		}
		
		local total_vars = 0
		foreach var of local all_vars {
			local ++total_vars
			local lab: variable label `var'
			local var_label = lower("`lab'")
			local var_name = lower("`var'")
			
			local var`total_vars' "`var_name'"
			local var_orig_case`total_vars' "`var'"
			local var_label`total_vars' "`var_label'"
		}
		local var_num = 0
		foreach var of local all_vars {
			local ++var_num
			local prev_var_num = `var_num' - 1
			local next_var_num = `var_num' + 1
			
			if `var_num'!= 1 {
				local prev_var "`var`prev_var_num''"
				local prev_var_orig_case "`var_orig_case`prev_var_num''"
				local prev_var_label "`var_label`prev_var_num''"
			}
			else {
				local prev_var
				local prev_var_orig_case
				local prev_var_label
			}
			if `var_num' != `total_vars' {
				local next_var "`var`next_var_num''"
				local next_var_orig_case "`var_orig_case`next_var_num''"
				local next_var_label "`var_label`next_var_num''"
			}
			else {
				local next_var
				local next_var_orig_case
				local next_var_label
			}
				
			local lab: variable label `var'
			local var_label = lower("`lab'")
			local var_name = lower("`var'")
			
			*If "lat" is in the variable name or label, see if "lon" is in the next or previous variables name or label:
			if strmatch("`var_name'","*lat*")==1 | strmatch("`var_label'","*lat*")==1 {
				*if it's in the PREV variable name or label:
				if strmatch("`prev_var'","*lon*")==1 |  strmatch("`prev_var_label'","*lon*")==1 {
					display "lat/lon variable found: `var' (label = `var_label')"
					*ADD CURRENT VARIABLE AND PREVOUS VARIABLE TO FLAGGED:
					local flagged_vars "`flagged_vars' `var' `prev_var_orig_case'"
				}
				*if it's in the NEXT variable name or label:
				if strmatch("`next_var'","*lon*")==1 | strmatch("`next_var_label'","*lon*")==1 {
					display "lat/lon variable found: `var' (label = `var_label')"
					* ADD CURRENT VARIABLE AND NEXT VARIABLE TO FLAGGED:
					local flagged_vars "`flagged_vars' `var' `next_var_orig_case'"
				}
			}
		}
		
		*Remove duplicates in list of flagged vars:
		local flagged_vars : list uniq flagged_vars
		
		*Search through the remaining variables to see if there are variables for degree minute second. Only output the variables if all three are present, otherwise they are not likely to be PII:
		*initialize locals:
		foreach gps_string in degree minute second {
			local `gps_string' = 0
			local `gps_string'_vars
		}
		local gps_var_search : list all_vars - flagged_vars
		foreach var of local gps_var_search {
			local var_name = lower("`var'")
			local lab: variable label `var'
			local var_label = lower("`lab'")
			foreach gps_string in degree minute second {
				if strmatch("`var_name'","*`gps_string'*")==1 | strmatch("`var_label'","*`gps_string'*")==1 { 
					local `gps_string' = 1
					local `gps_string'_vars "``gps_string'_vars' `var'"
				}
			}
		}
		if `degree'==1 & `minute'==1 & `second' == 1 {
			local flagged_vars "`flagged_vars' `degree_vars' `minute_vars' `second_vars'"
		}
		
		*Remove duplicates in list of flagged vars:
		local flagged_vars : list uniq flagged_vars
			
	
		***Search through the variables and see if there are any of the PII search words in the variable names or labels:
		***Only look through variables that havent been assigned to be output to CSV sheet already
		local search_list : list all_vars - flagged_vars 
		*local flagged_vars "`strings_to_output'"
		foreach var of local search_list {
			local lab: variable label `var'
			local var_label = lower("`lab'")
			local var_name = lower("`var'")
			local keep_searching = 1
			foreach search_string of global final_search_list {
				if `keep_searching' == 1 {
					local search_string = lower(`"`search_string'"')
					***Look for string in variable name:
					local name_pos = strpos("`var_name'","`search_string'")
					***Look for string in variable label: 
					local label_pos = strpos("`var_label'","`search_string'")
					if `name_pos'!=0 | `label_pos' !=0 {
						display "search term `search_string' found in `var' (label = `var_label')"
						local flagged_vars "`flagged_vars' `var'"
						local keep_searching = 0
					}
				}
			}
			
			* If the variable hasnt been flagged yet look through the strict search terms list:
			if `keep_searching' == 1 {
				foreach str of global strict_search_strings {
					if `keep_searching' == 1 {
						*Search the variable name for the exact match or a match at the beginning or end of the variable name or in the middle separated by "_":
						if "`var_name'"=="`str'" | strmatch("`var_name'","*`str'")==1 | strmatch("`var_name'","`str'*")==1 | strmatch("`var_name'","*_`str'_*")==1 {
							display "Strict search term `str' found in `var' (label = `var_label')"
							local flagged_vars "`flagged_vars' `var'"
							local keep_searching = 0
						}
						
						*labels: - search for the full word in the label:
						if "`var_label'"=="`str'" | strmatch("`var_label'","* `str' *")==1 | strmatch("`var_label'","* `str'")==1 | strmatch("`var_label'","`str' *")==1 {
							display "Strict search term `str' found in `var' (label = `var_label')"
							local flagged_vars "`flagged_vars' `var'"
							local keep_searching = 0
						}
					}
				}	
			}	
		}
		
		
		*** Search through the STRING variables that havent been flagged by the name/label search to find variables with lengths greater than 3:
		local string_vars_to_search : list string_vars - flagged_vars
		foreach var of local string_vars_to_search {
			tempvar temp1
			qui gen `temp1' = length(`var') // string length 
			qui sum `temp1'
			if `r(max)'>`string_length' {
				local var_name = lower("`var'")
				local lab: variable label `var'
				display "`var' (label = `lab') has length > `string_length'"
				local flagged_vars "`flagged_vars' `var'"
			}
			drop `temp1'
		}

		
		***Make sure list of flagged variables does not contain repeated variables:
		local flagged_vars : list uniq flagged_vars
		
		***Dont output variable to list if all observations are missing:
		local flagged_vars_copy `flagged_vars'
		qui count 
		local total_obs = r(N)
		foreach var of local flagged_vars_copy {
			qui count if missing(`var')
			if r(N)==`total_obs' {
				display "`var' is missing for all observations - don't output to CSV"
				local flagged_vars : list flagged_vars - var
			}
		}
		
		*Drop the non-flagged variables:
		capture keep `flagged_vars'
		qui duplicates drop
		
		***Output the flagged variables to csv file: 
		foreach var of local flagged_vars {
			local ++total_variables_flagged
			tempvar obsnm_temp temp2 temp3 temp4 temp5
			qui egen `temp2' = group(`var') // group var
			qui egen `temp3' = mode(`temp2'), maxmode // mode of GROUP
			qui egen `temp4' = tag(`temp2')
			qui gen `temp5' = `temp4'*`temp2' // tag*group = 1 for first obs in group 1, 0 for second obs in group 1, 2 for first obs in group 2, etc

			***First column=path
			file write output_file _char(34) `"`file_`i''"' _char(34) ","
			***Second column=variable nam
			file write output_file _char(34) `"`var'"' _char(34) ","
			***Third column=label
			local lab: variable label `var'
			local lab : subinstr local lab "`backtick'" "" // remove backtick 
			***Remove double quotation marks from label which messes up writing to single cells of CSV file:
			local lab = subinstr(`"`lab'"',`"""',"",.)
			file write output_file _char(34) `"`lab'"' _char(34) ","
			***Fourth column=most frequent value  -- mode = `temp3' - value where tag*group (`temp5') = mode
			qui gen `obsnm_temp'=_n
			qui sum `obsnm_temp' if `temp3'==`temp5'
			
			local most_freq_value = `var'[`r(mean)']
			local most_freq_value : subinstr local most_freq_value "`backtick'" "" // remove backtick 
			*Remove double quotation marks which mess up writing to single cells of CSV file:
			local most_freq_value = subinstr(`"`most_freq_value'"',`"""',"",.)
			file write output_file _char(34) `"`most_freq_value'"' _char(34) ","
			***Fifth column = ratio of num diff values/num obs
			***Fifth column = # of unique values
			qui sum `temp2'
			file write output_file _char(34) `"`r(max)'"' _char(34) ","
			local num_unique_values = `r(max)' // save this to use for writing samples below
			***Sixth column = total observations
			***NOTE: `N' comes from "qui count" when file is first opened
			file write output_file _char(34) `"`N'"' _char(34) ","
			***Seventh column = samp1 (nonmissing) --> N+7th column = sampN (nonmissing):
			***First sort by tag*group:
			*** Only do the sorting if samples>0:
			if `samples'>0 {
				gsort - `temp5'
				forvalues m=1/`samples' {
					local samp`m' = `var'[`m']
				}
				local num_samples_output = min(`samples',`num_unique_values') // If there are only 2 unique values, only write 2 samples (samp1 samp2) 
				forvalues sampnum=1/`num_samples_output' {
					*Remove double quotation marks which mess up writing to single cells of CSV file:
					local samp`sampnum' : subinstr local samp`sampnum' "`backtick'" "" // remove backtick 
					local samp`sampnum' = subinstr(`"`samp`sampnum''"',`"""',"",.)
					file write output_file _char(34) `"`samp`sampnum''"' _char(34) ","
				}
			}
			drop `obsnm_temp' `temp2' `temp3' `temp4' `temp5'
			drop `var'
			file write output_file _n
		}
	}

	file close output_file

	display ""
	display "------------------------------------------------------------"
	if !missing("`time'") {
		display ""
		display "START TIME = `start_time'"
		display "END TIME = " c(current_time)
	}

	display ""
	display "FILES SCANNED = `total_files'"
	display "VARIABLES SCANNED = `total_variables'"
	display "VARIABLES WITH POTENTIAL PII = `total_variables_flagged'"
	display ""
	display "------------------------------------------------------------"

end


pii_scan ${directory_to_scan}
