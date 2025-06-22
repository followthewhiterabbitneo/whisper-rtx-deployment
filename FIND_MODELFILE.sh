#!/bin/bash
# FIND THE MODELFILE WE CREATED

echo "=== SEARCHING FOR MODELFILE ==="
echo

# 1. Find Modelfile
echo "1. Looking for Modelfile:"
find / -name "Modelfile" -type f 2>/dev/null | while read file; do
    echo "Found: $file"
    echo "Contents:"
    cat "$file"
    echo "---"
done

echo
echo "2. Looking for modelfile (lowercase):"
find / -name "modelfile" -type f 2>/dev/null | while read file; do
    echo "Found: $file"
    echo "Contents:"
    cat "$file"
    echo "---"
done

echo
echo "3. Looking in our project directory:"
find /moneyball/whisper-rtx-deployment -name "*odel*" -type f | while read file; do
    echo "Found: $file"
    grep -l "FROM" "$file" 2>/dev/null && echo "  ^ Contains FROM statement"
done

echo
echo "4. Searching for files with 'FROM llama' content:"
grep -r "FROM llama" /moneyball 2>/dev/null | head -20

echo
echo "5. Looking for llama3-legal model:"
find / -type d -name "*llama3-legal*" 2>/dev/null
find / -type f -name "*llama3-legal*" 2>/dev/null

echo
echo "6. Check git history for Modelfile:"
cd /moneyball/whisper-rtx-deployment
git log --all --full-history -- "*Modelfile*" | head -20

echo
echo "7. Search in ollama's model registry:"
find / -path "*/ollama/*" -name "*.json" 2>/dev/null | xargs grep -l "llama3-legal" 2>/dev/null

echo
echo "=== The Modelfile should show which .gguf file we're using! ==="