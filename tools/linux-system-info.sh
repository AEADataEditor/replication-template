#!/bin/bash

# Tested on openSUSE

echo "System info:"
cat /etc/*release | grep PRETTY_NAME | awk -F= ' {print $2 } '
cat /proc/cpuinfo | grep "model name" | awk -F: ' { sum+=1; model=$2 } END { print $2 ", " sum " cores" }'
free -g | grep Mem | awk ' { print $2 "GB memory" } '
