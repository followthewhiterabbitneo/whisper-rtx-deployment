#!/bin/bash
# Register GGUF with Ollama - FIXED version

echo "=== REGISTERING LLAMA MODEL (FIXED) ==="
echo

# 1. Find the GGUF file
cd /moneyball/whisper-rtx-deployment/models
GGUF_FILE=$(ls *.gguf 2>/dev/null | grep -i llama | head -1)

if [ -z "$GGUF_FILE" ]; then
    echo "ERROR: No GGUF file found!"
    ls -la
    exit 1
fi

echo "Found GGUF: $GGUF_FILE"
FULL_PATH="/moneyball/whisper-rtx-deployment/models/$GGUF_FILE"

# 2. Check if Ollama is already running
echo
echo "Checking Ollama service:"
if pgrep -f "ollama serve" > /dev/null; then
    echo "✓ Ollama is already running"
else
    echo "Starting Ollama..."
    export OLLAMA_MODELS=/moneyball/ollama/models
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
fi

# 3. Create FIXED Modelfile (no gpu_layers)
echo
echo "Creating Modelfile (without gpu_layers):"
cd /moneyball/whisper-rtx-deployment
cat > Modelfile << EOF
FROM $FULL_PATH

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
EOF

echo "Modelfile contents:"
cat Modelfile

# 4. Remove any existing llama3 model
echo
echo "Removing any existing llama3 model:"
ollama rm llama3 2>/dev/null || true

# 5. Create the model
echo
echo "Creating model in Ollama:"
ollama create llama3 -f Modelfile

# 6. List models
echo
echo "Current models:"
ollama list

# 7. Test it
echo
echo "Testing model:"
time ollama run llama3 "Hello"

echo
echo "✅ Model registered!"
echo "Use: ollama run llama3 'your prompt'"

# 8. Show GPU usage
echo
echo "GPU Memory usage:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader