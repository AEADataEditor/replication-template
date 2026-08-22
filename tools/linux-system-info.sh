#!/bin/bash

# Tested on openSUSE

echo "System info:"
osname=$(cat /etc/*release | grep PRETTY_NAME | awk -F= ' {print $2 } ')
cpuname=$(cat /proc/cpuinfo | grep 'model name' | awk -F: ' { sum+=1; model=$2 } END { print $2 ", " sum " cores" }')
meminfo=$(free -g | grep Mem | awk ' { print $2  } ')

if command -v lspci &>/dev/null; then
    gpuinfo=$(lspci | grep -E -i '(vga|3d controller|display controller)' | sed 's/.*: //')
else
    gpuinfo="(lspci not available)"
fi

# Try to get GPU VRAM: nvidia-smi for NVIDIA, sysfs for AMD
gpumem=""
if command -v nvidia-smi &>/dev/null; then
    gpumem=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | paste -sd '/' -)
elif ls /sys/class/drm/card*/device/mem_info_vram_total &>/dev/null 2>&1; then
    gpumem=$(awk '{printf "%.0f MiB", $1/1024/1024}' /sys/class/drm/card*/device/mem_info_vram_total | paste -sd '/' -)
fi

# print it
echo "- OS: $osname"
echo "- Processor: $cpuname"
echo "- Memory available: ${meminfo}GB memory"
if [ -n "$gpuinfo" ]; then
    memsuffix=""
    [ -n "$gpumem" ] && memsuffix=" ($gpumem)"
    echo "$gpuinfo" | while IFS= read -r line; do
        echo "- GPU: ${line}${memsuffix}"
    done
else
    echo "- GPU: none detected"
fi