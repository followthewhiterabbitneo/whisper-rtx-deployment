#!/bin/bash
# Check GPU memory usage to verify GPU inference

echo "=== GPU MEMORY USAGE CHECK ==="
echo "When GPU works, memory usage should increase significantly"
echo

# 1. Baseline GPU memory
echo "1. GPU memory BEFORE loading model:"
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv
BEFORE_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
echo "Memory used: ${BEFORE_MEM} MB"
echo

# 2. Find CUDA binary
CUDA_BINARY=""
for bin in /moneyball/llama-cuda-arch/main /moneyball/llama-cuda/main /moneyball/llama-simple/main; do
    if [ -x "$bin" ]; then
        CUDA_BINARY="$bin"
        break
    fi
done

if [ -z "$CUDA_BINARY" ]; then
    echo "No binary found!"
    exit 1
fi

MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# 3. Load model and check memory
echo "2. Loading model to GPU..."
echo "Running inference with --gpu-layers 35"
echo

# Start continuous memory monitoring
echo "GPU Memory Usage (watch for increase):"
echo "======================================"
nvidia-smi --query-gpu=timestamp,memory.used --format=csv -l 1 > /tmp/gpu_mem_log.txt &
MONITOR_PID=$!

# Run inference
$CUDA_BINARY \
    -m "$MODEL" \
    -p "Hello" \
    -n 10 \
    --gpu-layers 35 \
    --threads 4 \
    --log-disable 2>&1 > /tmp/inference_out.txt &

INFERENCE_PID=$!

# Monitor for 10 seconds
for i in {1..10}; do
    MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    echo "Time $i: ${MEM} MB"
    sleep 1
done

# Kill processes
kill $MONITOR_PID 2>/dev/null
kill $INFERENCE_PID 2>/dev/null
wait

# 4. Analyze results
echo
echo "3. GPU memory AFTER loading model:"
AFTER_MEM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
echo "Memory used: ${AFTER_MEM} MB"

DIFF=$((AFTER_MEM - BEFORE_MEM))
echo
echo "=== MEMORY ANALYSIS ==="
echo "Before: ${BEFORE_MEM} MB"
echo "After: ${AFTER_MEM} MB"
echo "Difference: ${DIFF} MB"
echo

if [ $DIFF -gt 1000 ]; then
    echo "✅ GPU MEMORY INCREASED BY ${DIFF} MB - GPU IS WORKING!"
    echo "The model is loaded in GPU memory!"
else
    echo "❌ GPU memory didn't increase significantly"
    echo "Model is NOT using GPU memory"
fi

# 5. Check memory log for pattern
echo
echo "4. Memory usage pattern:"
if [ -f /tmp/gpu_mem_log.txt ]; then
    echo "Peak memory during inference:"
    sort -t',' -k2 -n /tmp/gpu_mem_log.txt | tail -5
fi

# 6. Test with different GPU layers
echo
echo "5. Testing memory with different GPU layers..."
cat > /moneyball/test_gpu_layers.sh << 'EOF'
#!/bin/bash
# Test GPU memory with different layer counts

echo "GPU Layers vs Memory Usage Test"
echo "==============================="

for layers in 0 10 20 35; do
    echo
    echo "Testing --gpu-layers $layers"
    
    # Get baseline
    BEFORE=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    
    # Run with timeout
    timeout 30 $CUDA_BINARY \
        -m "$MODEL" \
        -p "test" \
        -n 5 \
        --gpu-layers $layers \
        --log-disable > /dev/null 2>&1 &
    
    PID=$!
    sleep 5
    
    # Check memory
    DURING=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    
    kill $PID 2>/dev/null
    wait $PID 2>/dev/null
    
    DIFF=$((DURING - BEFORE))
    echo "Memory increase: ${DIFF} MB"
done

echo
echo "More layers = more GPU memory = GPU is being used"
EOF
chmod +x /moneyball/test_gpu_layers.sh

echo
echo "=== CONCLUSION ==="
echo "For Llama 3 8B model, expect ~4-6 GB memory increase when using GPU"
echo "If memory doesn't increase, GPU offloading isn't working"
echo
echo "Run layer test: /moneyball/test_gpu_layers.sh"