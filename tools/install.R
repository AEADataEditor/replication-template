# install.R


pkgTest <- function(x,y="")
{
	if (!require(x,character.only = TRUE))
	{
		if ( y == "" ) 
			{
		        install.packages(x,dep=TRUE)
			} else {
			remotes::install_version(x, y)
			}
		if(!require(x,character.only = TRUE)) stop("Package not found")
	}
	return("OK")
}

global.libraries <- c("here","renv")

results <- sapply(as.list(global.libraries), pkgTest)
