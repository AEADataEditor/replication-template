# Author: Lars Vilhuber
# (C) 2023
# Licensed under BSD-3 license
#
# Finds all dependencies and outputs them as a CSV.
# Uses the first command line argument as root path
# if using R CMD BATCH, use
#   R CMD BATCH '--args (PATH)'

# Import necessary packages, install if necessary

outfile="r-deps"

if (!require("renv",character.only = TRUE))	{ 
    if ( file.exists("install.R")) {
       source("install.R")
    } else {
      if ( file.exists("tools/install.R") ) {
        source("tools/install.R")
      }
    }
  }

##First read in the arguments listed at the command line
args=(commandArgs(TRUE))

##args is now a list of character vectors
## First check to see if arguments are passed.
## Then cycle through each element of the list and evaluate the expressions.
if(length(args)==0){
    print("No arguments supplied.")
    ##supply default values
    basepath = "."
} else {
    basepath = args[[1]] 
    }

print(paste0("Basepath: ",basepath))
  
deps <- renv::dependencies(path=basepath)


if ( nrow(deps) > 0 ) {
    # remove absolute paths
    abspath=here::here()
    deps$Source <- gsub(abspath,"",deps$Source)

    # create summary 
    summary <- as.data.frame(table(deps$Package))
    names(summary) <- c("Package","Occurences")

   write.csv(deps,   paste0(outfile,".csv"),        row.names=FALSE)
   write.csv(summary,paste0(outfile,"-summary.csv"),row.names=FALSE)
} else {
    message("No R dependencies found.")
}
