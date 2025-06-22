#!/bin/bash
# Clean up Gemma models and tar files from /moneyball

echo "=== CLEANING UP GEMMA AND OLD FILES FROM /moneyball ==="
echo

# 1. Current disk usage
echo "1. Current disk usage:"
df -h /moneyball
echo

# 2. Find Gemma-related files
echo "2. Finding Gemma-related files:"
echo
echo "Gemma model files:"
find /moneyball -name "*gemma*" -type f -size +100M -exec ls -lh {} \; 2>/dev/null
echo
echo "Gemma directories:"
find /moneyball -name "*gemma*" -type d 2>/dev/null | xargs du -sh 2>/dev/null | sort -h

# 3. Find tar.gz files
echo
echo "3. Finding tar.gz files:"
find /moneyball -name "*.tar.gz" -o -name "*.tar" -o -name "*.tgz" -exec ls -lh {} \; 2>/dev/null | sort -k5 -h

# 4. Find GGUF model files
echo
echo "4. Finding GGUF model files:"
find /moneyball -name "*.gguf" -exec ls -lh {} \; 2>/dev/null

# 5. Find other large files
echo
echo "5. Other large files (>1GB):"
find /moneyball -type f -size +1G -exec ls -lh {} \; 2>/dev/null | grep -v -E "(gemma|\.tar)" | sort -k5 -h

# 6. Create cleanup commands
echo
echo "=== CLEANUP COMMANDS ==="
echo
echo "To remove Gemma files:"
echo "  find /moneyball -name '*gemma*' -type f -delete"
echo "  rm -rf /moneyball/gemma*"
echo "  rm -rf /moneyball/*gemma*"
echo
echo "To remove tar files:"
echo "  find /moneyball -name '*.tar.gz' -delete"
echo "  find /moneyball -name '*.tar' -delete"
echo
echo "To remove specific large files:"
echo "  rm /moneyball/path/to/large/file"
echo
echo "To check what will be deleted first:"
echo "  find /moneyball -name '*gemma*' -o -name '*.tar*' | xargs du -ch | tail -1"

# 7. Space that will be freed
echo
echo "6. Space to be freed:"
echo "Gemma files:"
find /moneyball -name "*gemma*" -type f -exec du -ch {} + 2>/dev/null | tail -1
echo "Tar files:"
find /moneyball -name "*.tar*" -type f -exec du -ch {} + 2>/dev/null | tail -1