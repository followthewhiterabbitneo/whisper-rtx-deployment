#!/bin/bash
# Check if llama.cpp is actually using GPU

echo "=== CHECKING GPU INFERENCE ==="
echo

# 1. Check current GPU status
echo "1. Current GPU status:"
nvidia-smi

echo
echo "2. Testing GPU layers..."
# Test with different GPU layer counts
for layers in 0 15 33 50 99; do
    echo
    echo "Testing with --gpu-layers $layers"
    
    # Monitor GPU while running
    nvidia-smi dmon -s u -d 1 -c 10 &
    MONITOR=$!
    sleep 1
    
    # Run quick test
    timeout 30 /moneyball/llama.cpp/llama-cli \
        -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
        -p "Hi" \
        -n 10 \
        --gpu-layers $layers \
        --threads 4 \
        --log-disable 2>&1 | grep -E "gpu|layer|cuda|model size|llm_load_tensors"
    
    kill $MONITOR 2>/dev/null
    wait $MONITOR 2>/dev/null
    
    echo "---"
done

echo
echo "3. Checking CUDA in binary..."
ldd /moneyball/llama.cpp/llama-cli | grep -i cuda || echo "No CUDA libraries linked!"

echo
echo "4. Testing with verbose output..."
/moneyball/llama.cpp/llama-cli \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -p "Test" \
    -n 5 \
    --gpu-layers 33 \
    --verbose-prompt 2>&1 | grep -E "CUDA|cuda|GPU|gpu|offload"

echo
echo "=== DIAGNOSIS ==="
echo "If GPU utilization stays at 0%:"
echo "1. The binary might not have CUDA support compiled in"
echo "2. Try the simple make version instead of cmake"
echo
echo "Quick fix - build without cmake:"
cat > /moneyball/build_simple_cuda.sh << 'EOF'
#!/bin/bash
cd /moneyball
rm -rf llama-simple
git clone https://github.com/ggerganov/llama.cpp llama-simple
cd llama-simple
git checkout b3447
LLAMA_CUDA=1 make -j4
echo "Test with: $(pwd)/main"
EOF
chmod +x /moneyball/build_simple_cuda.sh
echo "Run: /moneyball/build_simple_cuda.sh"