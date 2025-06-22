#!/bin/bash
# Clean up ALL Ollama installations outside /moneyball

echo "=== CLEANING UP OLLAMA MESS ==="
echo "This will remove all Ollama traces outside /moneyball"
echo "Press Ctrl+C to cancel, or wait 5 seconds..."
sleep 5

# Stop any running Ollama services
echo "1. Stopping Ollama services..."
sudo systemctl stop ollama 2>/dev/null
pkill -f ollama 2>/dev/null

# Remove system files (need sudo)
echo "2. Removing system installations..."
sudo rm -rf /usr/local/bin/ollama
sudo rm -rf /usr/local/lib/ollama
sudo rm -rf /etc/systemd/system/ollama.service
sudo systemctl daemon-reload

# Remove user directories
echo "3. Removing user directories..."
rm -rf ~/.ollama
rm -rf ~/ollama
rm -rf ~/.cache/ollama

# Remove any ollama user/group (if created)
echo "4. Removing ollama user/group..."
sudo userdel ollama 2>/dev/null
sudo groupdel ollama 2>/dev/null

# Find and list any remaining ollama files
echo "5. Checking for remaining files..."
echo "Files outside /moneyball:"
find / -name "*ollama*" 2>/dev/null | grep -v "/moneyball" | grep -v "/proc" | grep -v "/sys" | head -20

echo ""
echo "=== CLEANUP COMPLETE ==="
echo ""
echo "Now you can use the portable version:"
echo "./setup_ollama_portable_rhel8.sh"
echo ""
echo "Or just use what's already working in /moneyball:"
echo "ollama run gemma2-legal 'Your prompt here'"