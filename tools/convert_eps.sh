#!/bin/bash

# check for convert

convert=$(which convert)
case $? in
	0)
		echo "convert found at $convert"
		;;
	*)
		echo "No convert found ... exiting"
		exit 2
		;;
esac

for file in $(find . -name \*.eps); do
    $convert "$file" "${file%.eps}.png"
done

