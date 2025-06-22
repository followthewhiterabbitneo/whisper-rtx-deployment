#!/bin/bash
# Build llama.cpp with CUDA but without curl

echo "=== BUILDING LLAMA.CPP WITH CUDA (NO CURL) ===="
echo "Using the successful configuration from before"
echo

cd /moneyball/llama.cpp

# 1. Clean previous build
echo "1. Cleaning previous build:"
make clean

# 2. Build with CUDA enabled and curl disabled
echo
echo "2. Building with CUDA (curl disabled):"
LLAMA_CUDA=1 LLAMA_CURL=0 make -j8

# 3. Verify build
echo
echo "3. Checking build result:"
if [ -f "main" ]; then
    echo "✅ main binary built successfully!"
    ls -la main
    
    # Check CUDA linkage
    echo
    echo "4. CUDA libraries linked:"
    ldd main | grep -i cuda || echo "No CUDA libraries found (may still work)"
else
    echo "❌ Build failed! Trying alternative..."
    echo
    echo "Trying with LLAMA_CUBLAS instead:"
    make clean
    LLAMA_CUBLAS=1 LLAMA_CURL=0 make -j8
    
    if [ -f "main" ]; then
        echo "✅ Built with LLAMA_CUBLAS!"
    else
        echo "❌ Both build attempts failed"
        exit 1
    fi
fi

# 4. Quick test
echo
echo "5. Quick functionality test:"
./main --help | grep -i "gpu\|layer" | head -5

# 5. Create direct test
echo
echo "6. Creating direct GPU test:"
cat > /moneyball/direct_gpu_test.sh << 'EOF'
#!/bin/bash
# Direct GPU test with monitoring

MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

echo "=== DIRECT GPU TEST ==="
echo "Watch the GPU Util column!"
echo

# Start GPU monitor
nvidia-smi dmon -s u -d 1 &
MONITOR_PID=$!

# Give it a moment to start
sleep 2

echo
echo "Running inference..."
time /moneyball/llama.cpp/main \
    -m "$MODEL" \
    -p "What is 2+2? Answer:" \
    -n 20 \
    --n-gpu-layers 999 \
    -t 8 \
    --log-disable 2>&1 | grep -v "^llama_"

# Stop monitor
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

echo
echo "✅ If GPU Util % went up, GPU compute is working!"
echo "❌ If GPU Util stayed at 0%, it's using CPU"
EOF
chmod +x /moneyball/direct_gpu_test.sh

echo
echo "=== BUILD COMPLETE ===="
echo "Built with: LLAMA_CUDA=1 LLAMA_CURL=0"
echo
echo "Test GPU compute with:"
echo "  /moneyball/direct_gpu_test.sh"
echo
echo "This uses the exact same build flags that worked before!"