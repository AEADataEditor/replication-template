#!/bin/bash

# Tested on macOS (Intel and Apple Silicon)

echo "System info:"
osname=$(sw_vers -productName)" "$(sw_vers -productVersion)
cpuname=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || sysctl -n hw.model)
cpucores=$(sysctl -n hw.logicalcpu)
meminforaw=$(sysctl -n hw.memsize)
meminfo=$(( meminforaw / 1024 / 1024 / 1024 ))

gpuinfo=$(system_profiler SPDisplaysDataType 2>/dev/null \
    | awk '/Chipset Model:/ { sub(/.*Chipset Model: /, ""); print }')

# print it
echo "- OS: $osname"
echo "- Processor: $cpuname, $cpucores cores"
echo "- Memory available: ${meminfo}GB memory"
if [ -n "$gpuinfo" ]; then
    echo "$gpuinfo" | while IFS= read -r line; do
        echo "- GPU: $line"
    done
else
    echo "- GPU: none detected"
fi
