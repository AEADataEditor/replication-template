{smcl}
{* revised 17may2019}{...}
{cmd:help filelist}
{hline}

{title:Title}

{phang}
{bf:filelist} {hline 2} Recursively search directories for files


{title:Syntax}

{p 4 16 2}
{cmd:filelist} 
	{cmd:,}
	[
	{opt d:irectory(dirpath)} 
	{opt p:attern(search_pattern)} 
	{opt s:ave(stata_dataset)} 
	{opt replace}
	{opt l:ist} 
	{opt nor:ecursive}
	{opt max:deep(#)}
	]
	

{marker Description}{...}
{title:Description}

{pstd}
{cmd:filelist} searches {it:dirpath} for files that match
{it:search_pattern} and continues searching recursively in all
its subdirectories. If {opt d:irectory(dirpath)} is omitted,
the search starts from the current directory 
(see {help pwd} and {help cd}). 

{pstd}
By default, {cmd:filelist} will pick up all files, including
system files that are usually hidden. To target a specific
type of file using a pattern in the file name, use the 
{opt p:attern(search_pattern)} option.
The {it:search_pattern} string must conform to the rules of the {help strmatch()}
function. For example, with {opt pattern("*.csv")}, {cmd:filelist} will return only
file names that end with ".csv".

{pstd}
{cmd:filelist} creates a dataset with 3 variables and as
many observations as there are matching files.
The {cmd:dirname} variable stores the file path to the file,
starting from the initial {it:dirpath}. The {cmd:filename} variable 
stores the file name and {cmd:fsize} stores the file size in bytes.

{pstd}
You can use the {opt s:ave(stata_dataset)} option to save the
results to disk instead of replacing the data in memory. Use
the {opt replace} option if {it:stata_dataset} already exists
and you want to overwrite it.

{pstd}
The {opt l:ist} option is used to print the matched files
in Stata's Results window.

{pstd}
The {opt max:deep(#)} can be used to control how many levels
deep {cmd:filelist} will search for files. {opt max:deep(1)}
is equivalent to using the {opt nor:ecursive} option and will
limit the search to the initial directory specified by {it:dirpath}.
The default is to search all subdirectories recursively.


{marker Limitations}{...}
{title:Limitations}

{pstd}
{cmd:filelist} can recursively scan a directory and return an unlimited 
number of files (it will happily scan a whole hard disk if you ask for it).
Note however that {cmd:filelist} is written in Mata and unfortunately the
{cmd:dir()} function can only return 10,000 filenames from a single directory.
As of May 17, 2019, this hard coded limit is still present in the all versions
of Stata. 

{pstd}
If the directory structure is deep enough,
the file path may exceed the maximum string length for variables of 244
characters in Stata version 9 to 12. When used with Stata 13
or higher, {cmd:filelist} can handle any length.

{pstd}
The Stata routines used by {cmd:filelist} 
to discover the file size work with files
up to 2,147,483,647 bytes (2GB). For files
larger than 2GB, you need a 64-bit version
of Stata 13.1 (revision 03 Jun 2015) or higher.
Otherwise, {cmd:fsize} will
contain a missing value for that observation.


{marker Examples}{...}
{title:Examples}

{pstd}
To find all files in the current directory and its subdirectories

        {cmd:.} {stata filelist}

{pstd}
If there is a "main" directory within the current directory, you can
search for all Stata datasets in "main" using

        {cmd:.} {stata filelist, dir("main") pat("*.dta")}
        
{pstd}
To search for all comma-separated data files in the "main" directory 
within the current directory and save the results to disk
        
        {cmd:.} {stata filelist, dir("main") pat("*.csv") save("csv_datasets.dta")}
        
{pstd}
You can run the following code if you want to use the saved search 
results to append all csv data files

        {cmd:} use "csv_datasets.dta", clear
        {cmd:} local obs = _N
        {cmd:} forvalues i=1/`obs' {
        {cmd:}   use "csv_datasets.dta" in `i', clear
        {cmd:}   local f = dirname + "/" + filename
        {cmd:}   insheet using "`f'", clear
        {cmd:}   gen source = "`f'"
        {cmd:}   tempfile save`i'
        {cmd:}   save "`save`i''"
        {cmd:} }

        {cmd:} use "`save1'", clear
        {cmd:} forvalues i=2/`obs' {
        {cmd:}   append using "`save`i''"
        {cmd:} }


{marker Acknowledgments}{...}
{title:Acknowledgments}

{pstd}A question on Statalist from {browse "http://www.stata.com/statalist/archive/2013-10/msg01014.html":Tim Evans} was the stimulus for
writing this program. 


{marker Author}{...}
{title:Author}

{pstd}Robert Picard{p_end}
{pstd}picard@netbox.com{p_end}


{marker also}{...}
{title:Also see}

{psee}
Stata:  {help pwd}, {help cd:[D] cd}, {help dir:[D] dir}, {help extended_fcn:[P] macro -- Extended macro functions}, {help mf_dir: [M-5] dir()}
{p_end}

{psee}
SSC:  {stata "ssc desc dirlist":dirlist}, {stata "ssc desc dirtools":dirtools}, {stata "ssc desc fs":fs}
{p_end}
