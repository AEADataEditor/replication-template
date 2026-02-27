# Author: Andres Aradillas Fernandez
# (C) 2022
# Licensed under BSD-3 license
#
# Running instructions: Run all the code at once, no manual changes needed.
# Run with the WD set in this directory.
# Example: cd tools; R CMD BATCH (THIS FILE)

# Import necessary packages, install if necessary

if (!require("here",character.only = TRUE))
	{ 
    message("Installing packages.")
    message("If this fails, run 'source(\"tools/install.R\",echo=TRUE)' interactively.")
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

# create basename
basename <- "r-data-checks"

# Finds current directory
root <- here(basepath)

# Create list of all RDS files in directory
datafiles_list <- list.files(root, pattern = "\\.rds", full.names = TRUE, recursive = TRUE, ignore.case = TRUE, include.dirs = FALSE)

# Create list denoting successes/failures
read_success <- list()

# Loop to read all RDS files, recording successes as "yes"
if ( length(datafiles_list) == 0 ) {
  message("No RDS files found, exiting")
} else {
  for(k in 1:length(datafiles_list)){
    filename <- datafiles_list[[k]]
    short.filename <- gsub(paste0(root,"/"),"",filename)
    message(paste0("Processing: ",short.filename))
    t <- try(readRDS(filename), silent = TRUE)
    if ("try-error" %in% class(t)){
      read_success[[k]] <- "No"
    } else{
      read_success[[k]] <- "Yes"
    }
  }

  # Convert list into data frame
  df <- data.frame(matrix(unlist(datafiles_list), nrow=length(datafiles_list),  byrow=TRUE))
  df$col2 <- read_success

  # Add column names to new data frame
  colnames(df) <- c("File name", "Successfully read")
  df <- as.matrix(df)

  # remove root from absolute pathnames
  df[,1] <- gsub(paste0(root,"/"),"",df[,1])


  # Export as text file - always

  csvfile = here(paste0(basename,".csv"))
  xlsxfile= here(paste0(basename,".xlsx"))

  message(paste0("Writing out results: ",gsub(paste0(root,"/"),"",csvfile)))
  write.table(df, file = csvfile, 
                sep = ",", 
                quote = FALSE, 
                row.names = FALSE)


  # Export results as Excel if xlsx package installed
  t <- try(library(xlsx), silent = TRUE)
  if ("try-error" %in% class(t)) {
    message("No xlsx library, skipping write-out of XLSX file.")

  } else{
    message(paste0("Writing out results: ",gsub(paste0(root,"/"),"",xlsxfile)))
    write.xlsx(df, file = xlsxfile, 
                sheetName = "Output", 
                append = FALSE)
  }
}