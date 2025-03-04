#!/bin/bash

# Tested on openSUSE

echo "System info:"
osname=$(cat /etc/*release | grep PRETTY_NAME | awk -F= ' {print $2 } ')
cpuname=$(cat /proc/cpuinfo | grep 'model name' | awk -F: ' { sum+=1; model=$2 } END { print $2 ", " sum " cores" }')
meminfo=$(free -g | grep Mem | awk ' { print $2  } ')

# print it
echo "- OS: $osname"
echo "- Processor: $cpuname"
echo "- Memory available: ${meminfo}GB memory"