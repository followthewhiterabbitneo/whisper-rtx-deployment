#!/bin/bash
# Safe cleanup of root filesystem

echo "=== SAFE ROOT FILESYSTEM CLEANUP ==="
echo "Current usage:"
df -h /
echo

# 1. Clean package manager cache (safe)
echo "1. Cleaning package manager cache..."
sudo yum clean all 2>/dev/null || sudo dnf clean all 2>/dev/null || sudo apt-get clean 2>/dev/null
echo

# 2. Clean journal logs (safe)
echo "2. Cleaning old journal logs..."
sudo journalctl --vacuum-time=2d
echo

# 3. Remove old log files (safe)
echo "3. Removing old log files..."
sudo find /var/log -type f -name "*.log" -mtime +7 -exec rm {} \;
sudo find /var/log -type f -name "*.gz" -mtime +7 -exec rm {} \;
echo

# 4. Clean tmp (safe)
echo "4. Cleaning tmp directories..."
sudo find /tmp -type f -mtime +1 -delete 2>/dev/null
sudo find /var/tmp -type f -mtime +7 -delete 2>/dev/null
echo

# 5. Find and list model files for manual review
echo "5. Finding potential model files:"
echo "These files might be AI models - review before deleting:"
echo
find / -xdev \( -name "*.gguf" -o -name "*.bin" -o -name "*.safetensors" \) -size +500M -exec ls -lh {} \; 2>/dev/null | grep -v "/moneyball"

echo
echo "6. Checking for Ollama data outside /moneyball:"
for dir in /usr/share /var/lib /opt; do
    if [ -d "$dir" ]; then
        find "$dir" -name "*ollama*" -type d 2>/dev/null | while read d; do
            size=$(du -sh "$d" 2>/dev/null | cut -f1)
            echo "Found: $d ($size)"
        done
    fi
done

echo
echo "After cleanup:"
df -h /

echo
echo "If still above 85%, run:"
echo "  ./find_disk_usage.sh"
echo "to see what's using space"