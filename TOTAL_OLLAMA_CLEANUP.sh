#!/bin/bash
# TOTAL cleanup - remove ALL Ollama data EVERYWHERE except /moneyball

echo "=== TOTAL OLLAMA CLEANUP - EVERYWHERE EXCEPT /moneyball ==="
echo "This will find and remove ALL Ollama data outside /moneyball"
echo "Press Ctrl+C to cancel..."
sleep 3

# Kill all Ollama
pkill -9 ollama

# Find ALL ollama directories and files outside /moneyball
echo ""
echo "1. Finding all Ollama data outside /moneyball..."
echo "This may take a minute..."

# Common locations first
echo ""
echo "2. Cleaning known locations..."
rm -rf ~/.ollama
rm -rf ~/ollama
rm -rf ~/.cache/ollama
rm -rf ~/.config/ollama
rm -rf ~/.local/share/ollama
rm -rf ~/.local/state/ollama
rm -rf /tmp/ollama*
rm -rf /var/tmp/ollama*
rm -rf /usr/local/lib/ollama
rm -rf /usr/local/bin/ollama
rm -rf /opt/ollama

# System directories (need sudo)
echo ""
echo "3. Cleaning system directories (may need sudo)..."
sudo rm -rf /usr/local/lib/ollama 2>/dev/null
sudo rm -rf /etc/ollama 2>/dev/null
sudo rm -rf /var/lib/ollama 2>/dev/null
sudo rm -rf /var/cache/ollama 2>/dev/null

# Find everything else
echo ""
echo "4. Searching entire system (excluding /moneyball)..."
echo "Large files/dirs with 'ollama' in name:"

# Find large ollama files/dirs outside /moneyball
find / -name "*ollama*" -size +100M 2>/dev/null | grep -v "/moneyball" | grep -v "/proc" | grep -v "/sys" | head -20

# Find ollama directories
find / -type d -name "*ollama*" 2>/dev/null | grep -v "/moneyball" | grep -v "/proc" | grep -v "/sys" | head -20

# Show disk usage
echo ""
echo "5. Disk usage by directory:"
du -sh /*ollama* 2>/dev/null | grep -v "/moneyball"
du -sh /home/*/.ollama 2>/dev/null
du -sh /home/*/.cache/*ollama* 2>/dev/null

# Clean cache directories
echo ""
echo "6. Cleaning cache directories..."
find /home -type d -name ".ollama" -o -name "*ollama*" 2>/dev/null | grep -v "/moneyball" | xargs rm -rf 2>/dev/null
find /var -type d -name "*ollama*" 2>/dev/null | xargs sudo rm -rf 2>/dev/null
find /tmp -name "*ollama*" 2>/dev/null | xargs rm -rf 2>/dev/null

# Final check
echo ""
echo "7. Final check - remaining ollama files:"
find / -name "*ollama*" 2>/dev/null | grep -v "/moneyball" | grep -v "/proc" | grep -v "/sys" | wc -l

echo ""
echo "8. Disk space after cleanup:"
df -h /home
df -h /
df -h /moneyball

echo ""
echo "=== CLEANUP COMPLETE ==="
echo "All Ollama data outside /moneyball has been removed!"
echo ""
echo "To use Ollama again, ONLY use scripts in /moneyball/whisper-rtx-deployment/"