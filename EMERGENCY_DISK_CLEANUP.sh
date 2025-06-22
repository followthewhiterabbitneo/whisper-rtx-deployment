#!/bin/bash
# EMERGENCY - Find and remove Ollama models filling up disk

echo "=== EMERGENCY DISK CLEANUP ==="
echo "CRITICAL: Root filesystem is filling up!"
echo

# 1. Check disk usage
echo "1. Disk usage:"
df -h /
echo

# 2. Find where Ollama is storing models
echo "2. Finding Ollama model locations:"
echo

echo "Default Ollama locations:"
du -sh /usr/share/ollama 2>/dev/null
du -sh /var/lib/ollama 2>/dev/null
du -sh ~/.ollama 2>/dev/null
du -sh /root/.ollama 2>/dev/null
du -sh /opt/ollama 2>/dev/null

echo
echo "3. Searching for large model files:"
find / -name "*.bin" -size +1G 2>/dev/null | head -20
find / -name "*ollama*" -type d 2>/dev/null | xargs du -sh 2>/dev/null | sort -h | tail -20

echo
echo "4. Check Ollama's model directory:"
echo "OLLAMA_MODELS=${OLLAMA_MODELS:-not set}"

# Common locations
OLLAMA_LOCATIONS=(
    "/usr/share/ollama/models"
    "/var/lib/ollama/models"
    "$HOME/.ollama/models"
    "/root/.ollama/models"
    "/tmp/ollama*"
)

for loc in "${OLLAMA_LOCATIONS[@]}"; do
    if [ -d "$loc" ]; then
        echo
        echo "Found models at: $loc"
        du -sh "$loc"/* 2>/dev/null | sort -h
    fi
done

echo
echo "5. IMMEDIATE ACTIONS:"
echo
echo "Stop Ollama completely:"
echo "  pkill -9 ollama"
echo
echo "Remove all models:"
echo "  rm -rf /usr/share/ollama/models/*"
echo "  rm -rf ~/.ollama/models/*"
echo "  rm -rf /root/.ollama/models/*"
echo
echo "Find large files:"
echo "  find / -type f -size +1G -exec ls -lh {} \; 2>/dev/null"
echo
echo "CRITICAL: Models should NEVER be in / filesystem!"
echo "They should be in /moneyball!"