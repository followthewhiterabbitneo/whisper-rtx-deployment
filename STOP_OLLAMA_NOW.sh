#!/bin/bash
# STOP OLLAMA IMMEDIATELY

echo "=== STOPPING OLLAMA IMMEDIATELY ==="

# 1. Kill all Ollama processes
echo "Killing all Ollama processes..."
pkill -9 ollama
pkill -9 -f "ollama serve"
pkill -9 -f "ollama run"
pkill -9 -f "ollama pull"

# 2. Check what's running
echo
echo "Checking for remaining processes:"
ps aux | grep ollama | grep -v grep

# 3. Find and show model storage
echo
echo "Model storage locations:"
find / -name "ollama" -type d 2>/dev/null | while read dir; do
    if [ -d "$dir/models" ]; then
        echo "FOUND: $dir/models"
        du -sh "$dir/models" 2>/dev/null
    fi
done

# 4. Emergency cleanup commands
echo
echo "=== EMERGENCY CLEANUP COMMANDS ==="
echo
echo "1. Remove models from root filesystem:"
echo "   sudo rm -rf /usr/share/ollama/models/*"
echo "   sudo rm -rf /var/lib/ollama/models/*"
echo "   sudo rm -rf ~/.ollama/models/*"
echo
echo "2. Set Ollama to use /moneyball:"
echo "   export OLLAMA_MODELS=/moneyball/ollama/models"
echo "   mkdir -p /moneyball/ollama/models"
echo
echo "3. Never let Ollama use root filesystem again!"
echo
echo "STOP USING OLLAMA UNTIL THIS IS FIXED!"