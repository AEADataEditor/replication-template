#Template config.R

# INSTRUCTIONS:
# 
# Step 1: Add or modify code to install libraries
#
# If the author provides a setup or config file that installs packages, use it.
# Then proceed to Step 2.
# If not, then copy this code to "config.R", modify the lines after this comment block,
# and add "source("config.R", echo = TRUE)" to the main file.
#
# If the author does not have a main file, you can instead copy this code to "main.R",
# and add "source("authorcode.R", echo = TRUE)" to the end of this file, for each R file
# provided by the author.
#
# Step 2: Run the code generating a log file
# 
# The following command works on Linux, MacOS, and on Windows
# from the "Terminal" within Rstudio:
#     R CMD BATCH program.R 
# For alternative ways to do that, see 
# https://github.com/labordynamicsinstitute/replicability-training/wiki/R-Tips



#*================================================
#* This lists the libraries that are to be installed.
#* Adjust this by adding on additional ones identified by the authors as necessary

global.libraries <- c("foreign","devtools","rprojroot","skimr")
# For example, you can add on two additional ones:
# global.libraries <- c("foreign","devtools","rprojroot","ggplot2","nonsenseR")

#*==============================================================================================*/
#* This is specific to AEA replication environment. May not be needed if no confidential data   */
#* are used in the reproducibility check.                                                       */
#* Replicator should check the JIRA field "Working location of restricted data" for right path  */

sdrive <- ""

#*================================================
#* This lists any paths, relative to the root directory, that are to be created.

create.paths <- c("logs","libraries")
# for instance, the following paths might be necessary
#create.paths <- c("data/raw","data/interwrk","data/generated","results")

################################################
# Setup for automatic basepath detection       #
################################################

# Preferred:
# in bash, go to the root directory and type
# "touch .here". Then the following code will work cleanly.

# Alternative:
# There is already a "name_of_project.Rproj" file in the root directory.
# No further action needed

# If for some reason that does not work (and it always should)
# manually override:

# rootdir <- "path/to/root/directory"
rootdir <- ""

####################################
# global libraries used everywhere #
####################################

posit.date <- Sys.Date() - 31
# posit.date <- "2020-01-01" # uncomment and set manually if the above does not work

# PPM only snapshots on weekdays (not sure why...)
if ( weekdays(posit.date) %in% c("Saturday","Sunday") ) posit.date <- posit.date - 2
options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/",posit.date)))



################################################
# No additional changes needed below this line #
################################################

# print option repos 
message(paste0("Setting Posit Package Manager snapshot to ",posit.date))
message("If this does not work, set the date manually in line 22")
getOption("repos")




####################################
# Set path to root directory       #
#                                  #
####################################

install.packages("here")
if ( rootdir == "" ) rootdir <- here::here()
setwd(rootdir)


# Main directories

for ( dir in create.paths){
	if (file.exists(file.path(rootdir,dir))){
	} else {
	dir.create(file.path(rootdir,dir))
	}
}


# Setting project-specific library

.libPaths(file.path(rootdir,"libraries"))

# Get information on the system we are running on
Sys.info()
R.version

# Function to install libraries
# inject here back into these libraries

global.libraries <- c(global.libraries,"here")

pkgTest <- function(x)
{
	if (!require(x,character.only = TRUE))
	{
		install.packages(x,dep=TRUE)
		if(!require(x,character.only = TRUE)) stop("Package not found")
	}
	return("OK")
}

## Add any libraries to this line, and uncomment it.


results <- sapply(as.list(global.libraries), pkgTest)


# keep this line in the config file
print(sessionInfo())
.libPaths()
list.files(.libPaths()[1])

message("Done with configuration.")


