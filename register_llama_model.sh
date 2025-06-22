#!/bin/bash
# Register the extracted GGUF with Ollama

echo "=== REGISTERING LLAMA MODEL WITH OLLAMA ==="
echo

# 1. Check if extraction completed
echo "1. Checking extracted files:"
cd /moneyball/whisper-rtx-deployment/models
ls -lh *.gguf

# 2. Get the exact GGUF filename
GGUF_FILE=$(ls *.gguf 2>/dev/null | grep -i llama | head -1)
if [ -z "$GGUF_FILE" ]; then
    echo "ERROR: No GGUF file found! Is extraction still running?"
    echo "Checking for zip process:"
    ps aux | grep -i unzip
    exit 1
fi

echo
echo "2. Found GGUF file: $GGUF_FILE"
FULL_PATH="/moneyball/whisper-rtx-deployment/models/$GGUF_FILE"

# 3. Verify file is complete
echo
echo "3. Verifying file integrity:"
file "$GGUF_FILE"

# 4. Create Modelfile with absolute path
echo
echo "4. Creating Modelfile with absolute path:"
cd /moneyball/whisper-rtx-deployment
cat > Modelfile << EOF
FROM $FULL_PATH

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
PARAMETER gpu_layers 999
EOF

echo "Modelfile contents:"
cat Modelfile

# 5. Ensure Ollama is running
echo
echo "5. Starting Ollama service:"
pkill -f "ollama serve"
sleep 2
export OLLAMA_MODELS=/moneyball/ollama/models
ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# 6. Create the model
echo
echo "6. Creating model in Ollama:"
ollama create llama3 -f Modelfile

# 7. Verify it's registered
echo
echo "7. Checking ollama list:"
ollama list

# 8. Test the model
echo
echo "8. Testing model:"
ollama run llama3 "Hello, respond in one word"

echo
echo "=== Model should now be registered! ==="
echo "Use: ollama run llama3 'your prompt'"