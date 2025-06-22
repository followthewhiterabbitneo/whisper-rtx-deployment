#!/bin/bash
# Quick build llama.cpp - disable CURL to avoid dependency

echo "=== Quick Build llama.cpp ==="

cd /moneyball/llama.cpp

# Clean build directory
rm -rf build
mkdir -p build
cd build

# Configure without CURL
echo "Configuring (disabling CURL)..."
cmake .. -DGGML_CUDA=ON -DLLAMA_CURL=OFF

# Build
echo "Building..."
cmake --build . --config Release -j4

# Copy executables to main directory
echo ""
echo "Copying executables..."
if [ -f "bin/llama-cli" ]; then
    cp bin/llama-cli ../main
    echo "✓ Copied llama-cli as main"
fi

if [ -f "bin/llama-server" ]; then
    cp bin/llama-server ../server
    echo "✓ Copied llama-server as server"
fi

# Alternative names (newer versions)
if [ -f "bin/main" ]; then
    cp bin/main ../
    echo "✓ Copied main"
fi

if [ -f "bin/server" ]; then
    cp bin/server ../
    echo "✓ Copied server"
fi

cd /moneyball/llama.cpp

# Test Gemma
echo ""
echo "=== Testing Gemma ==="
MODEL="/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"

if [ -f "./main" ] || [ -f "./llama-cli" ]; then
    echo "Testing model..."
    EXEC="./main"
    [ -f "./llama-cli" ] && EXEC="./llama-cli"
    
    $EXEC -m "$MODEL" -n 50 -p "Legal summary: Customer called about loan status." --no-display-prompt 2>/dev/null || \
    $EXEC -m "$MODEL" -n 50 -p "Legal summary: Customer called about loan status."
else
    echo "Executables not found. Check build output above."
fi

echo ""
echo "Done! To run server:"
echo "./server -m $MODEL -c 2048"