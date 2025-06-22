#!/bin/bash
# DELETE ALL GEMMA REFERENCES FROM CODEBASE

echo "=== DELETING ALL GEMMA REFERENCES ==="
echo

# 1. Find all files with Gemma references
echo "1. Finding files with Gemma references:"
grep -r -i "gemma" /moneyball/whisper-rtx-deployment --exclude-dir=.git | cut -d: -f1 | sort -u > /tmp/gemma_files.txt
cat /tmp/gemma_files.txt

echo
echo "2. Showing Gemma references:"
grep -r -i "gemma" /moneyball/whisper-rtx-deployment --exclude-dir=.git | head -20

# 3. Delete files that are primarily about Gemma
echo
echo "3. Files to DELETE completely:"
for file in /moneyball/whisper-rtx-deployment/*gemma*.{py,sh,md,txt}; do
    if [ -f "$file" ]; then
        echo "  Deleting: $file"
        rm -f "$file"
    fi
done

# 4. Remove the Modelfile with Gemma reference
echo
echo "4. Removing old Modelfile with Gemma:"
if grep -q "gemma" /moneyball/whisper-rtx-deployment/Modelfile 2>/dev/null; then
    echo "  Deleting Modelfile with Gemma reference"
    rm -f /moneyball/whisper-rtx-deployment/Modelfile
fi

# 5. Clean up Python scripts with Gemma imports/references
echo
echo "5. Cleaning Python files with Gemma references:"
for file in $(grep -l -i "gemma" /moneyball/whisper-rtx-deployment/*.py 2>/dev/null); do
    echo "  File: $file"
    # Count how many lines have gemma
    gemma_count=$(grep -i -c "gemma" "$file")
    total_lines=$(wc -l < "$file")
    
    # If more than 20% of lines mention gemma, delete the file
    if [ $gemma_count -gt $((total_lines / 5)) ]; then
        echo "    -> Deleting (too many Gemma references)"
        rm -f "$file"
    else
        echo "    -> Has $gemma_count Gemma references (keeping file, manual edit needed)"
    fi
done

# 6. Remove Gemma from shell scripts
echo
echo "6. Removing Gemma references from shell scripts:"
for file in /moneyball/whisper-rtx-deployment/*.sh; do
    if [ -f "$file" ] && grep -q -i "gemma" "$file"; then
        # Create backup
        cp "$file" "$file.bak"
        # Remove lines with gemma
        sed -i '/[Gg]emma/d' "$file"
        # Check if file is now empty or broken
        if [ ! -s "$file" ] || [ $(wc -l < "$file") -lt 5 ]; then
            echo "  File $file became too small, restoring"
            mv "$file.bak" "$file"
        else
            echo "  Cleaned: $file"
            rm -f "$file.bak"
        fi
    fi
done

# 7. Final check
echo
echo "7. Remaining Gemma references:"
grep -r -i "gemma" /moneyball/whisper-rtx-deployment --exclude-dir=.git --exclude="*.bak" | wc -l
echo "references found"

echo
echo "8. Files deleted:"
git status --porcelain | grep "^D" | cut -c4-

echo
echo "=== GEMMA PURGE COMPLETE ==="
echo "All Gemma-specific files deleted"
echo "Ready to commit these deletions"