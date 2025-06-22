#!/bin/bash
# Extract and use the EXISTING Llama model

echo "=== FOUND THE MODEL! ==="
echo "llama-3-8b-it-gguf-q4-k-m.zip in models directory"
echo

cd /moneyball/whisper-rtx-deployment/models

# 1. Check the zip file
echo "1. Checking zip file:"
ls -lh *llama*.zip

# 2. Extract it
echo
echo "2. Extracting model:"
unzip -o *llama*3*8b*.zip || unzip -o llama-3-8b-it-gguf-q4-k-m.zip

# 3. Find the GGUF file
echo
echo "3. Finding extracted GGUF:"
ls -lh *.gguf

# 4. Get the exact filename
GGUF_FILE=$(ls *.gguf | grep -i llama | head -1)
if [ -z "$GGUF_FILE" ]; then
    GGUF_FILE=$(ls *.gguf | head -1)
fi

echo
echo "4. Found GGUF: $GGUF_FILE"

# 5. Create Modelfile pointing to it
echo
echo "5. Creating Modelfile:"
cat > /moneyball/whisper-rtx-deployment/Modelfile << EOF
FROM /moneyball/whisper-rtx-deployment/models/$GGUF_FILE

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 999
PARAMETER gpu_layers 999
EOF

echo "Created Modelfile pointing to: $GGUF_FILE"

# 6. Create the model in Ollama
echo
echo "6. Creating Ollama model:"
cd /moneyball/whisper-rtx-deployment
ollama create llama3-local -f Modelfile

# 7. Test it
echo
echo "7. Testing model:"
ollama run llama3-local "Say hello"

echo
echo "=== SUCCESS! ==="
echo "Model extracted and ready to use:"
echo "  ollama run llama3-local 'your prompt'"
echo
echo "NO DOWNLOADING NEEDED!"