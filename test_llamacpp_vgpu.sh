#!/bin/bash
# Test llama.cpp with virtual GPU (works better than Ollama for vGPU)

echo "=== TESTING LLAMA.CPP WITH VIRTUAL GPU ==="
echo "Since Ollama can't detect vGPU, using llama.cpp directly"
echo

# 1. Find llama.cpp binary
echo "1. Looking for llama.cpp binary..."
LLAMA_BIN=""
for bin in \
    /moneyball/llama.cpp/llama-cli \
    /moneyball/llama.cpp/main \
    /moneyball/llama-simple/main \
    /moneyball/working_llama; do
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        LLAMA_BIN="$bin"
        echo "Found: $bin"
        break
    fi
done

if [ -z "$LLAMA_BIN" ]; then
    echo "❌ No llama.cpp binary found!"
    echo "Build with: cd /moneyball/llama-simple && LLAMA_CUDA=1 make"
    exit 1
fi

# 2. Find model
echo
echo "2. Looking for model..."
MODEL=""
for model in \
    /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    /moneyball/models/*.gguf; do
    if [ -f "$model" ]; then
        MODEL="$model"
        echo "Found: $model"
        break
    fi
done

if [ -z "$MODEL" ]; then
    echo "❌ No GGUF model found!"
    exit 1
fi

# 3. Test with GPU monitoring
echo
echo "3. Testing GPU inference..."
echo "==== WATCH GPU UTILIZATION % ====="

# Monitor GPU
nvidia-smi dmon -s u -d 1 -c 30 &
MONITOR_PID=$!
sleep 2

# Run inference
echo
echo "Running inference test..."
START=$(date +%s)
$LLAMA_BIN \
    -m "$MODEL" \
    -p "What is the capital of France? Answer in one word." \
    -n 50 \
    --gpu-layers 35 \
    --threads 4 \
    --temp 0 \
    2>&1 | grep -v "^ggml_"

END=$(date +%s)
TIME=$((END-START))

# Stop monitor
kill $MONITOR_PID 2>/dev/null

echo
echo "=== RESULTS ==="
echo "Time: $TIME seconds"
echo "If GPU utilization went above 0%, GPU inference is working!"

# 4. Create easy-to-use wrapper
echo
echo "4. Creating wrapper script..."
cat > /moneyball/llama_gpu.sh << EOF
#!/bin/bash
# Easy llama.cpp GPU inference
$LLAMA_BIN \\
    -m "$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --temp 0.7 \\
    2>&1 | grep -v "^ggml_"
EOF
chmod +x /moneyball/llama_gpu.sh

echo
echo "=== SUCCESS ==="
echo "Use: /moneyball/llama_gpu.sh 'your prompt here'"
echo "Example: /moneyball/llama_gpu.sh 'Explain AI in 3 sentences'"