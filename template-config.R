#Template config.R

# INSTRUCTIONS:
# 
# In order to generate log files with R, use one of two methods:
# 1. If running on Linux or macOS, do not use this program, 
#    and run the author's program from the terminal:
#     R --vanilla < program.R > program.log
# 2. Alternatively, or if the setup is more complex, use this template.
#    Either integrate pieces of it into the author's main program
#    or call the author's R programs from this program, using 
#    this program as the "main" program:
#    - copy this program to main.R
#    - call all required R scripts through the source() function:
#      source("DataPrep.R", echo = TRUE)

####################################
# global libraries used everywhere #
####################################

mran.date <- "2021-01-01"
options(repos=paste0("https://cran.microsoft.com/snapshot/",mran.date,"/"))


# Set up the logging package

install.packages('TeachingDemos')   
library(TeachingDemos)

####################################
# Set path to root directory       #
#                                  #
#  --->>   MODIFY THIS  <<---      #
####################################
basepath <- "path/to/root/directory"
setwd(basepath)

# Start the markdown log file
mdtxtStart("Log", file = paste0('logfile-',Sys.Date(),'.md'), commands = TRUE, results = TRUE, visible.only = TRUE)
Sys.info()
R.version



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

global.libraries <- c("foreign","devtools","rprojroot")

results <- sapply(as.list(global.libraries), pkgTest)


# keep this line in the config file
print(sessionInfo())
print(paste0("MRAN date was set to: ",mran.date))

####################################
# Call provided R scripts using    #
#  'source(".", echo = TRUE)'      #
#                                  #
#  --->>   MODIFY THIS  <<---      #
####################################

# source("path/to/program1.R", echo = TRUE)
# source("path/to/program2.R", echo = TRUE)

# Close log file
mdtxtStop()
