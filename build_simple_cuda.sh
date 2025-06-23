#!/bin/bash
# Build simple llama.cpp with CUDA support

echo "=== BUILDING SIMPLE LLAMA.CPP WITH CUDA ==="
echo "Using make instead of cmake to avoid filesystem issues"
echo

cd /moneyball
rm -rf llama-simple
git clone https://github.com/ggerganov/llama.cpp llama-simple
cd llama-simple

# Use older stable version
echo "Checking out stable version b3447..."
git checkout b3447

# Build with CUDA
echo
echo "Building with CUDA support..."
LLAMA_CUDA=1 make clean
LLAMA_CUDA=1 make -j4

# Check if build succeeded
if [ -f "main" ]; then
    echo
    echo "✅ Build successful!"
    echo "Binary at: $(pwd)/main"
    
    # Test GPU support
    echo
    echo "Testing GPU support..."
    ./main --help | grep -i gpu || echo "No GPU options found"
    
    # Create test script
    cat > /moneyball/test_simple_cuda.sh << 'EOF'
#!/bin/bash
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

echo "Testing with GPU monitoring..."
nvidia-smi dmon -s u -d 1 -c 15 &
MONITOR=$!
sleep 1

/moneyball/llama-simple/main \
    -m "$MODEL" \
    -p "What is 2+2?" \
    -n 50 \
    --gpu-layers 35 \
    --threads 4

kill $MONITOR 2>/dev/null
EOF
    chmod +x /moneyball/test_simple_cuda.sh
    
    echo
    echo "=== BUILD COMPLETE ==="
    echo "Test with: /moneyball/test_simple_cuda.sh"
else
    echo "❌ Build failed!"
fi