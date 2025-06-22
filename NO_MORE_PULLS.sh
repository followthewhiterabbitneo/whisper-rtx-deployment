#!/bin/bash
# STOP PULLING MODELS WE ALREADY HAVE!

echo "=== STOP PULLING MODELS ==="
echo

# Kill any ollama pull processes
echo "1. Killing any pull operations..."
pkill -f "ollama pull"

# Show what we have
echo
echo "2. Models we ALREADY HAVE:"
ollama list

# Show running models
echo
echo "3. Models currently loaded:"
ollama ps

# Try to run with existing models
echo
echo "4. Testing existing models (NO PULL):"

# Try different model names
for model in "llama3:8b" "llama3" "llama" "llama3:8b-instruct" "llama3-legal" "llama3:latest"; do
    echo
    echo "Trying: $model"
    timeout 5 ollama run $model "Hi" 2>&1 | head -3
    if [ $? -eq 0 ]; then
        echo "✅ WORKS! Use: ollama run $model"
        export WORKING_MODEL=$model
        break
    fi
done

echo
echo "=== NEVER USE 'ollama pull' AGAIN ==="
echo "The models are already here!"
echo
echo "To check what's really on disk:"
echo "  find /moneyball -name '*.gguf' -o -name '*.bin' | grep -i llama"
echo "  find / -name '*llama*.gguf' 2>/dev/null"
echo
echo "We spent all this time setting up - don't download again!"