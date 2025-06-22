#!/bin/bash
# FIND THE ACTUAL MODELS RIGHT NOW

echo "=== SEARCHING FOR ALL MODELS ON SYSTEM ==="
echo

# 1. Find ALL model files
echo "1. Finding ALL model files (.gguf, .bin):"
find / -type f \( -name "*.gguf" -o -name "*.bin" \) -size +100M 2>/dev/null | grep -E "(llama|gguf|model)" | while read file; do
    ls -lh "$file"
done

echo
echo "2. Finding Ollama model directories:"
find / -type d -name "*model*" 2>/dev/null | grep -i ollama | while read dir; do
    echo "Found: $dir"
    ls -la "$dir" 2>/dev/null | head -5
done

echo
echo "3. Checking Ollama manifest files:"
find / -name "manifest" -path "*/ollama/*" 2>/dev/null | while read manifest; do
    echo "Manifest: $manifest"
    cat "$manifest" 2>/dev/null | head -10
done

echo
echo "4. Finding by size (models are BIG):"
find /moneyball -type f -size +1G 2>/dev/null | while read file; do
    ls -lh "$file"
done

echo
echo "5. Check Ollama's actual data:"
for dir in /usr/share/ollama /var/lib/ollama ~/.ollama /root/.ollama /moneyball/ollama; do
    if [ -d "$dir" ]; then
        echo
        echo "=== $dir ==="
        find "$dir" -type f -name "*.gguf" -o -name "*.bin" 2>/dev/null | while read f; do
            ls -lh "$f"
        done
    fi
done

echo
echo "=== ACTUAL MODELS FOUND ABOVE ==="
echo "Use the EXACT paths/names found!"