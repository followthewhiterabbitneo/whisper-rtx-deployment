#!/bin/bash
# EMERGENCY - Clean up ALL Ollama stuff from home directory

echo "=== EMERGENCY HOME DIRECTORY CLEANUP ==="
echo "This will remove ALL Ollama data from home directories"
echo ""

# Kill Ollama first
pkill -f ollama

# Show what's using space
echo "Space usage in home:"
du -sh ~/.ollama 2>/dev/null
du -sh ~/ollama 2>/dev/null
du -sh ~/.cache/ollama 2>/dev/null

# Remove from home
echo ""
echo "Removing from home directory..."
rm -rf ~/.ollama
rm -rf ~/ollama
rm -rf ~/.cache/ollama
rm -rf ~/.config/ollama
rm -rf ~/run_gemma.sh
rm -rf ~/.local/share/ollama
rm -rf ~/.local/state/ollama

# Check /tmp
echo ""
echo "Cleaning /tmp..."
rm -rf /tmp/ollama*
rm -rf /var/tmp/ollama*

# Find any other ollama files in home
echo ""
echo "Finding other ollama files in home..."
find ~ -name "*ollama*" -type f -o -name "*ollama*" -type d 2>/dev/null | grep -v "/moneyball" | head -20

# Clean those too
find ~ -name "*ollama*" -type f -o -name "*ollama*" -type d 2>/dev/null | grep -v "/moneyball" | xargs rm -rf 2>/dev/null

# Check disk space after
echo ""
echo "Disk space after cleanup:"
df -h ~
df -h /home

echo ""
echo "=== CLEANUP COMPLETE ==="
echo "ALL Ollama data removed from home directory!"
echo "Only /moneyball should have Ollama data now"