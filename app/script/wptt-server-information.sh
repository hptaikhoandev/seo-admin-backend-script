#!/bin/bash
clear

. /etc/wptt/.wptt.conf
if [[ $ngon_ngu = '' ]]; then
    ngon_ngu='vi'
fi
. /etc/wptt/lang/$ngon_ngu.sh

# Detect OS type
OS_TYPE=$(uname -s)
if [[ "$OS_TYPE" == "Linux" ]]; then
    CPU_COUNT=$(lscpu | grep "^CPU(s):" | awk '{print $2}')
    
    # Get total RAM in KB and round up to GB
    RAM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print ($2 / 1024 / 1024)+0.9}')  # Add 0.9 before floor rounding
    RAM_TOTAL=$(echo "$RAM_TOTAL" | awk '{print int($1)}')  # Round up

elif [[ "$OS_TYPE" == "Darwin" ]]; then
    CPU_COUNT=$(sysctl -n hw.ncpu)
    
    # Convert bytes to GB and round up
    RAM_TOTAL=$(sysctl -n hw.memsize | awk '{print ($1 / 1024 / 1024 / 1024)+0.9}')
    RAM_TOTAL=$(echo "$RAM_TOTAL" | awk '{print int($1)}')

elif [[ "$OS_TYPE" == "CYGWIN"* || "$OS_TYPE" == "MINGW"* ]]; then
    CPU_COUNT=$(wmic cpu get NumberOfLogicalProcessors | awk 'NR==2')
    
    # Get RAM in KB, convert to GB, and round up
    RAM_TOTAL=$(wmic OS get TotalVisibleMemorySize | awk 'NR==2 {print ($1 / 1024 / 1024 / 1024)+0.9}')
    RAM_TOTAL=$(echo "$RAM_TOTAL" | awk '{print int($1)}')

else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

# Print values only (no extra text)
echo "$CPU_COUNT"
echo "$RAM_TOTAL"
