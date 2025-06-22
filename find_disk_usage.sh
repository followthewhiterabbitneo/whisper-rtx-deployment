#!/bin/bash
# Find what's using disk space on root filesystem

echo "=== FINDING DISK USAGE ON ROOT ==="
echo

# 1. Overall usage
echo "1. Filesystem usage:"
df -h /
echo

# 2. Top 20 largest directories on root
echo "2. Largest directories on / (excluding /moneyball):"
du -xh / 2>/dev/null | grep -v "^/moneyball" | sort -rh | head -20
echo

# 3. Find large files
echo "3. Files larger than 1GB on root:"
find / -xdev -type f -size +1G -exec ls -lh {} \; 2>/dev/null | grep -v "/moneyball"
echo

# 4. Check common culprits
echo "4. Checking common space hogs:"
echo
echo "/var/log size:"
du -sh /var/log 2>/dev/null
echo
echo "/tmp size:"
du -sh /tmp 2>/dev/null
echo
echo "/var/cache size:"
du -sh /var/cache 2>/dev/null
echo
echo "/home sizes:"
du -sh /home/* 2>/dev/null | sort -h
echo

# 5. Check for Ollama remnants
echo "5. Searching for Ollama/model files:"
find / -xdev -name "*ollama*" -o -name "*.gguf" -o -name "*.bin" -size +100M 2>/dev/null | head -20

# 6. Check docker if present
echo
echo "6. Docker usage (if applicable):"
du -sh /var/lib/docker 2>/dev/null || echo "Docker not found"

# 7. Package manager cache
echo
echo "7. Package caches:"
du -sh /var/cache/yum 2>/dev/null || echo "No yum cache"
du -sh /var/cache/dnf 2>/dev/null || echo "No dnf cache"  
du -sh /var/cache/apt 2>/dev/null || echo "No apt cache"

echo
echo "=== CLEANUP SUGGESTIONS ==="
echo
echo "Clean package cache:"
echo "  sudo yum clean all"
echo "  sudo dnf clean all"
echo
echo "Clean temp files:"
echo "  sudo rm -rf /tmp/*"
echo "  sudo rm -rf /var/tmp/*"
echo
echo "Clean old logs:"
echo "  sudo journalctl --vacuum-time=1d"
echo "  sudo find /var/log -name '*.log' -mtime +7 -delete"
echo
echo "If you see large .gguf or .bin files, those are models!"