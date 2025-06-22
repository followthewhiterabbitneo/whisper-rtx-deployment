#!/bin/bash
# Simple GPU diagnostic

echo "=== Simple GPU Check ==="

# Basic checks
echo "1. Current user: $(whoami)"
echo "2. GPU visible:"
nvidia-smi -L || echo "nvidia-smi failed"

echo ""
echo "3. Check what's terminating:"
set -x  # Show commands as they run

# Try to start Ollama directly
/moneyball/ollama/bin/ollama serve &
PID=$!
echo "Started with PID: $PID"

sleep 2

# Check if still running
if ps -p $PID > /dev/null; then
    echo "Ollama is running"
else
    echo "Ollama terminated"
    
    # Check for errors
    echo ""
    echo "Checking for segfault or permissions:"
    dmesg | tail -10 | grep -i "ollama\|segfault" || echo "No kernel messages"
    
    echo ""
    echo "Try running directly to see error:"
    /moneyball/ollama/bin/ollama serve
fi