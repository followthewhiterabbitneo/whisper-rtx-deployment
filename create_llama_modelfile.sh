#!/bin/bash
# Create proper Modelfile for Llama

echo "=== CREATING LLAMA MODELFILE ==="
echo

# 1. First, let's see what Llama models Ollama knows about
echo "1. Checking Ollama's known models:"
ollama list | grep -i llama

# 2. Find actual Llama GGUF files
echo
echo "2. Finding Llama GGUF files on system:"
find / -name "*llama*.gguf" -type f 2>/dev/null | head -10

# 3. Check in Ollama's blob storage
echo
echo "3. Checking Ollama blob storage:"
find /usr/share/ollama -name "*.blob" -o -name "*.bin" 2>/dev/null | head -10
find /var/lib/ollama -name "*.blob" -o -name "*.bin" 2>/dev/null | head -10

# 4. Create new Modelfile
echo
echo "4. Creating new Modelfile..."

# If we find a llama model in ollama list, use it
LLAMA_MODEL=$(ollama list | grep -i llama | head -1 | awk '{print $1}')

if [ -n "$LLAMA_MODEL" ]; then
    echo "Found Ollama model: $LLAMA_MODEL"
    cat > /moneyball/Modelfile.llama << EOF
FROM $LLAMA_MODEL

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
EOF
else
    echo "No Llama model in 'ollama list'"
    echo "Creating Modelfile to use base llama3:8b"
    cat > /moneyball/Modelfile.llama << EOF
FROM llama3:8b

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
EOF
fi

echo
echo "5. Created: /moneyball/Modelfile.llama"
cat /moneyball/Modelfile.llama

echo
echo "6. To use this model:"
if [ -n "$LLAMA_MODEL" ]; then
    echo "   ollama run $LLAMA_MODEL 'your prompt'"
else
    echo "   First: ollama pull llama3:8b  (ONLY if not found above)"
    echo "   Then: ollama run llama3:8b 'your prompt'"
fi

echo
echo "Or create custom model:"
echo "   ollama create llama3-gpu -f /moneyball/Modelfile.llama"
echo "   ollama run llama3-gpu 'your prompt'"