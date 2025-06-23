#!/bin/bash
# Properly test and fix Ollama GPU inference

echo "=== TESTING OLLAMA GPU INFERENCE ==="
echo

# 1. Check if Ollama is running
echo "1. Checking Ollama status..."
if pgrep -f "ollama serve" > /dev/null; then
    echo "✅ Ollama is already running"
else
    echo "❌ Ollama not running, starting it..."
    
    # Set environment
    export CUDA_HOME=/usr/local/cuda-12.0
    export LD_LIBRARY_PATH=$CUDA_HOME/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
    export CUDA_VISIBLE_DEVICES=0
    
    # Start Ollama in background
    nohup ollama serve > /moneyball/ollama.log 2>&1 &
    echo "Started Ollama, PID: $!"
    sleep 5
fi

# 2. Check what CUDA version Ollama is using
echo
echo "2. Checking Ollama's CUDA libraries..."
OLLAMA_PID=$(pgrep -f "ollama serve" | head -1)
if [ -n "$OLLAMA_PID" ]; then
    echo "Ollama PID: $OLLAMA_PID"
    echo "Libraries in use:"
    lsof -p $OLLAMA_PID 2>/dev/null | grep -E "cuda|cublas" | head -10
fi

# 3. List available models
echo
echo "3. Available models:"
ollama list

# 4. Test GPU inference with monitoring
echo
echo "4. Testing GPU inference..."
echo "Watching GPU utilization (should go above 0%):"

# Start GPU monitor
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 2

# Run inference
echo
echo "Running inference test..."
time echo "What is 2+2? Give a brief answer." | ollama run llama3:8b --verbose 2>&1 | tee /tmp/ollama_test.log

# Stop monitor
kill $MONITOR 2>/dev/null
wait $MONITOR 2>/dev/null

# 5. Check for CUDA errors
echo
echo "5. Checking for CUDA errors in output..."
grep -i "cuda\|gpu\|error" /tmp/ollama_test.log || echo "No CUDA messages found"

# 6. Alternative test with explicit model load
echo
echo "6. Testing with explicit settings..."
cat > /moneyball/ollama_gpu_test.sh << 'EOF'
#!/bin/bash
# Force GPU layers
export OLLAMA_NUM_GPU_LAYERS=35
export CUDA_VISIBLE_DEVICES=0

echo "Testing with forced GPU layers..."
ollama run llama3:8b "Hi" --verbose
EOF
chmod +x /moneyball/ollama_gpu_test.sh

echo
echo "=== RESULTS ==="
echo "Check the GPU utilization above:"
echo "- If it stayed at 0%: GPU inference not working"
echo "- If it went up: GPU inference is working!"
echo
echo "To see Ollama logs: tail -f /moneyball/ollama.log"
echo "To test with forced GPU: /moneyball/ollama_gpu_test.sh"