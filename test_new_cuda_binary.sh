#!/bin/bash
# Test the newly built CUDA-enabled llama.cpp

echo "=== TESTING NEW CUDA-ENABLED LLAMA.CPP ==="
echo

# 1. Find the new binary
echo "1. Locating new binary..."
NEW_BINARY=""
for bin in /moneyball/llama-cuda-arch/main /moneyball/llama-cuda/main /moneyball/llama-simple/main; do
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        # Check if it has CUDA
        if ldd "$bin" 2>/dev/null | grep -q "libcuda"; then
            NEW_BINARY="$bin"
            echo "✅ Found CUDA-enabled binary: $bin"
            break
        else
            echo "❌ No CUDA in: $bin"
        fi
    fi
done

if [ -z "$NEW_BINARY" ]; then
    echo "❌ No CUDA-enabled binary found!"
    exit 1
fi

# 2. Verify CUDA libraries are linked
echo
echo "2. CUDA libraries linked:"
ldd "$NEW_BINARY" | grep -E "cuda|cublas|cudart" || echo "Warning: No CUDA libraries visible"

# 3. Find model
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
if [ ! -f "$MODEL" ]; then
    MODEL=$(find /moneyball -name "*.gguf" -type f 2>/dev/null | head -1)
fi
echo
echo "3. Using model: $MODEL"

# 4. GPU test with monitoring
echo
echo "4. RUNNING GPU TEST - WATCH THE GPU UTILIZATION %"
echo "================================================"
echo "If GPU % goes above 0, SUCCESS!"
echo

# Start detailed GPU monitor
nvidia-smi dmon -s um -d 1 -c 30 &
MONITOR_PID=$!
sleep 2

# Run inference with GPU layers
echo
echo "Starting inference with 35 GPU layers..."
START=$(date +%s)
$NEW_BINARY \
    -m "$MODEL" \
    -p "What is the capital of France? Answer in one word." \
    -n 20 \
    --gpu-layers 35 \
    --threads 4 \
    2>&1 | grep -v "^ggml_\|^llama_model"
END=$(date +%s)

# Stop monitor
kill $MONITOR_PID 2>/dev/null
wait $MONITOR_PID 2>/dev/null

# 5. Results
echo
echo "=== RESULTS ==="
echo "Time taken: $((END-START)) seconds"
echo

# Check GPU memory to confirm model loaded
echo "GPU Memory usage:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv

# 6. Create working script
echo
echo "5. Creating working GPU inference script..."
cat > /moneyball/llama_gpu_working.sh << EOF
#!/bin/bash
# Working GPU-accelerated llama.cpp

export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:\$LD_LIBRARY_PATH

$NEW_BINARY \\
    -m "$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --temp 0.7 \\
    --top-p 0.9 \\
    2>&1 | grep -v "^ggml_\|^llama_model"
EOF
chmod +x /moneyball/llama_gpu_working.sh

echo
echo "=== SUMMARY ==="
echo "If you saw GPU utilization > 0%, GPU inference is working!"
echo "Use: /moneyball/llama_gpu_working.sh 'your prompt here'"
echo
echo "If GPU was still 0%, check:"
echo "1. Were there CUDA libraries linked in step 2?"
echo "2. Did the model load into GPU memory?"
echo "3. Try with different --gpu-layers values (10, 20, 30)"