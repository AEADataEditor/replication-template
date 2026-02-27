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
#* Let's do everything verbosely.

options(verbose=TRUE)


#*================================================
#* lets capture the current wd, so we can return to it later
temphome <- getwd()

#*================================================
#* This lists the libraries that are to be installed.
#* Adjust this by adding on additional ones identified by the authors as necessary

global.libraries <- c("devtools","rprojroot")
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
# Only check for weekday if posit.date is a Date object, not a string
if (!is.character(posit.date) && weekdays(posit.date) %in% c("Saturday","Sunday")) {
  posit.date <- posit.date - 2
}

# Check if running on Linux
if (Sys.info()['sysname'] == "Linux") {
  # Try to determine the Linux distribution and version using /etc/os-release
  if (file.exists("/etc/os-release")) {
    os_release <- system("grep -E '^(ID|VERSION_ID|VERSION_CODENAME|ID_LIKE)=' /etc/os-release", intern = TRUE)
    
    # Extract distribution ID (like ubuntu, debian, rocky)
    distro_id <- gsub("ID=", "", grep("^ID=", os_release, value = TRUE))
    distro_id <- gsub("[\"']", "", distro_id) # Remove quotes if present
    
    # Extract version ID (like 9.4 for Rocky Linux)
    version_id <- gsub("VERSION_ID=", "", grep("^VERSION_ID=", os_release, value = TRUE))
    version_id <- gsub("[\"']", "", version_id) # Remove quotes if present
    
    # Extract codename (like focal, jammy, bullseye)
    codename <- gsub("VERSION_CODENAME=", "", grep("^VERSION_CODENAME=", os_release, value = TRUE))
    
    # Extract ID_LIKE (like rhel, centos, fedora)
    id_like <- gsub("ID_LIKE=", "", grep("^ID_LIKE=", os_release, value = TRUE))
    id_like <- gsub("[\"']", "", id_like) # Remove quotes if present
    
    # If we found Ubuntu or Debian
    if (length(distro_id) > 0 && grepl("^(ubuntu|debian)$", distro_id)) {
      # Set CRAN to binary PPM for Ubuntu/Debian
      options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/__linux__/", codename, "/", posit.date)))
      message(paste0("Using binary PPM for Linux distribution: ", distro_id, " (", codename, ")"))
    } else if (length(distro_id) > 0 && distro_id == "rocky" && grepl("^9", version_id)) {
      # Set CRAN to binary PPM for Rocky Linux 9
      options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/__linux__/rhel9/", posit.date)))
      message(paste0("Using binary PPM for Linux distribution: ", distro_id, " (version ", version_id, ")"))
    } else if (length(distro_id) > 0 && distro_id == "opensuse-leap" && version_id == "15.6") {
      # Set CRAN to binary PPM for opensuse-leap 15.6
      options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/__linux__/opensuse156/",posit.date)))
      message(paste0("Using binary PPM for Linux distribution: ", distro_id, " (version ", version_id, ")"))
    } else {
      # Use standard PPM with date-based snapshot for other Linux
      options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/", posit.date)))
    }
  } else {
    # Use standard PPM with date-based snapshot if os-release not available
    options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/", posit.date)))
  }
} else {
  # Use standard PPM with date-based snapshot for non-Linux systems
  options(repos = c(CRAN = paste0("https://packagemanager.posit.co/cran/", posit.date)))
}

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

# lets get back to where we started

setwd(temphome)

# keep these lines in the config file
message("======================================================================================================")
message(paste0(" Current working directory: ",getwd()))
print(sessionInfo())
message("Current libPaths:")
message(.libPaths())
message(print(list.files(.libPaths()[1])))

message("Done with configuration.")


