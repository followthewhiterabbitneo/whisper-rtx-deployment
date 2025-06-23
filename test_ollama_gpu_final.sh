#!/bin/bash
# Final test of Ollama GPU inference with nvcc installed

echo "=== TESTING OLLAMA GPU WITH NVCC INSTALLED ==="
echo

# 1. Verify CUDA setup
echo "1. Verifying CUDA installation:"
nvcc --version
echo
echo "CUDA libraries:"
ldconfig -p | grep -E "libcuda|libcudart|libcublas" | head -5

# 2. Source CUDA environment
echo
echo "2. Setting up environment..."
source /etc/profile.d/cuda.sh 2>/dev/null || true
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# 3. Kill any existing Ollama
echo
echo "3. Restarting Ollama..."
pkill -f "ollama serve" 2>/dev/null
sleep 2

# 4. Start Ollama with monitoring
echo "4. Starting Ollama serve..."
ollama serve > /tmp/ollama_gpu_test.log 2>&1 &
OLLAMA_PID=$!
echo "Ollama PID: $OLLAMA_PID"

# Wait for startup
echo "Waiting for Ollama to start..."
for i in {1..15}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo -n "."
    sleep 2
done
echo

# 5. Test GPU inference with monitoring
echo
echo "5. Testing GPU inference..."
echo "==== GPU UTILIZATION MONITOR ===="
echo "Watch the 'sm' column - it should go above 0% during inference"
echo

# Start GPU monitor
nvidia-smi dmon -s u -d 1 -c 30 &
MONITOR_PID=$!
sleep 2

# Run inference test
echo
echo "Running inference test..."
START_TIME=$(date +%s)
ollama run llama3:8b "What is the capital of France? Give a brief answer." 2>&1 | tee /tmp/ollama_result.txt
END_TIME=$(date +%s)
INFERENCE_TIME=$((END_TIME - START_TIME))

# Stop monitor
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

# 6. Check results
echo
echo "=== RESULTS ==="
echo "Inference time: ${INFERENCE_TIME} seconds"
echo

# Check GPU memory usage
echo "GPU Memory usage:"
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv

# Check if GPU was used
echo
if grep -q "looking for compatible GPUs" /tmp/ollama_gpu_test.log; then
    echo "❌ Ollama still can't find GPU"
    echo "Check log: tail -f /tmp/ollama_gpu_test.log"
else
    echo "✅ Ollama started without GPU detection errors"
fi

# 7. Create benchmark script
echo
echo "Creating benchmark script..."
cat > /moneyball/benchmark_ollama_gpu.sh << 'EOF'
#!/bin/bash
# Benchmark Ollama GPU performance

echo "=== OLLAMA GPU BENCHMARK ==="
echo "Running 3 inference tests..."

for i in 1 2 3; do
    echo
    echo "Test $i:"
    
    # Monitor GPU during test
    nvidia-smi dmon -s u -d 1 -c 20 > /tmp/gpu_usage_$i.txt &
    MONITOR=$!
    
    # Time the inference
    START=$(date +%s.%N)
    ollama run llama3:8b "Explain quantum computing in 3 sentences." > /tmp/result_$i.txt 2>&1
    END=$(date +%s.%N)
    
    kill $MONITOR 2>/dev/null
    
    # Calculate time
    TIME=$(echo "$END - $START" | bc)
    echo "Time: $TIME seconds"
    
    # Check max GPU usage
    MAX_GPU=$(awk '{if($2>max)max=$2}END{print max}' /tmp/gpu_usage_$i.txt 2>/dev/null)
    echo "Max GPU utilization: ${MAX_GPU:-0}%"
done

echo
echo "If GPU utilization was 0%, inference is still running on CPU"
EOF
chmod +x /moneyball/benchmark_ollama_gpu.sh

echo
echo "=== NEXT STEPS ==="
echo "1. If GPU utilization was above 0% - SUCCESS! 🎉"
echo "2. If still 0%, check: tail -f /tmp/ollama_gpu_test.log"
echo "3. Run benchmark: /moneyball/benchmark_ollama_gpu.sh"
echo
echo "Kill Ollama: kill $OLLAMA_PID"