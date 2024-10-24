#!/bin/bash
# This simply combines Parts A and B of the report

# read functions arguments and define defaults

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi


# If argument is "-h" print help and exit
print_help() {
  echo "Usage: $0 [no arguments]"
  echo "This script converts EPS and PDF to PNG."
  echo " -p[roject/path] Usually the project path, can be a full path"
  echo " -e[ps]   yes/no whether to process EPS files"
  echo " -[p]d[f] yes/no whether to process PDF files"
  echo "Possible optional arguments:"
    echo "  -h  print this help message"
  exit 0
}

# parse arguments

while getopts "p:e:d:h:" opt; do
    case $opt in
        p) path="$OPTARG" ;;  # Store the argument for -p
        e) eps="$OPTARG" ;; # Store the argument for -e
        d) pdf="$OPTARG" ;; # Store the argument for -d
        h) print_help; exit 0 ;; 
        \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
        :)  echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
    esac
done

# Shift processed options away
shift $((OPTIND - 1))

echo "Parsing path: $path"
echo "       - EPS: $eps"
echo "       - PDF: $pdf"

# check if convert is available
convert=$(which convert)
case $? in
        0)
                echo "convert found at $convert"
                ;;
        *)
                echo "Testing for docker"
		docker=$(which docker)
		case $? in
			0) 
				echo "Docker found"
				;;
			*) 
			echo "No convert found ... exiting"
                	exit 2
			;;
		esac
                ;;
esac

# Allowing for different options
#

if [[ "$eps" == "yes" ]]
then
    echo "Processing EPS"
    for file in $(find $(pwd)/$path -name \*.eps); do
	echo "   $file"
    	$convert "$file" "${file%.eps}.png"
    done
fi
if [[ "$pdf" == "yes" ]]
then
    echo "Processing PDF"
    for file in $(find $(pwd)/$path -name \*.eps); do
	echo "   $file"
    	$convert "$file" "${file%.eps}.png"
    done
fi
