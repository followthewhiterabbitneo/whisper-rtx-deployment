#!/bin/bash
# Test CUDA binary - handles both main and llama-cli

echo "=== TESTING CUDA-ENABLED LLAMA.CPP ==="
echo "Note: 'main' is deprecated but still created by older builds"
echo

# 1. Find the CUDA-enabled binary (main or llama-cli)
echo "1. Finding CUDA-enabled binary..."
CUDA_BINARY=""
BINARY_NAME=""

# Check directories where we built
for dir in /moneyball/llama-cuda-arch /moneyball/llama-cuda /moneyball/llama-simple; do
    if [ -d "$dir" ]; then
        echo "Checking $dir..."
        
        # Check for llama-cli first (newer)
        if [ -f "$dir/llama-cli" ] && [ -x "$dir/llama-cli" ]; then
            if ldd "$dir/llama-cli" 2>/dev/null | grep -q "libcuda"; then
                CUDA_BINARY="$dir/llama-cli"
                BINARY_NAME="llama-cli"
                echo "✅ Found CUDA-enabled llama-cli: $CUDA_BINARY"
                break
            fi
        fi
        
        # Check for main (older/deprecated)
        if [ -f "$dir/main" ] && [ -x "$dir/main" ]; then
            if ldd "$dir/main" 2>/dev/null | grep -q "libcuda"; then
                CUDA_BINARY="$dir/main"
                BINARY_NAME="main (deprecated)"
                echo "✅ Found CUDA-enabled main: $CUDA_BINARY"
                break
            fi
        fi
    fi
done

if [ -z "$CUDA_BINARY" ]; then
    echo "❌ No CUDA-enabled binary found!"
    echo "Your build might have created 'main' without CUDA support"
    exit 1
fi

# 2. Show what we're using
echo
echo "2. Using binary: $BINARY_NAME"
echo "Path: $CUDA_BINARY"
echo "CUDA libraries linked:"
ldd "$CUDA_BINARY" | grep -E "cuda|cublas" | head -5

# 3. Model
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
echo
echo "3. Model: $MODEL"

# 4. THE GPU TEST
echo
echo "4. GPU INFERENCE TEST"
echo "===================="
echo "WATCH THE GPU UTILIZATION % BELOW!"
echo "If 'sm' column goes above 0% = GPU is working!"
echo

# Monitor GPU
nvidia-smi dmon -s um -d 1 -c 25 &
MONITOR_PID=$!
sleep 2

# Run inference
echo
echo "Running inference..."
time $CUDA_BINARY \
    -m "$MODEL" \
    -p "Count from 1 to 5." \
    -n 30 \
    --gpu-layers 35 \
    --threads 4 \
    --log-disable 2>&1 | grep -v "^ggml_\|^llama_\|WARNING"

# Stop monitor
kill $MONITOR_PID 2>/dev/null

# 5. Check results
echo
echo "5. Checking GPU memory..."
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
echo "MB used (should be >1000 if model loaded to GPU)"

# 6. Create alias for easier use
echo
echo "6. Creating helper script..."
cat > /moneyball/llama_gpu_final.sh << EOF
#!/bin/bash
# GPU-accelerated llama.cpp wrapper

# Suppress deprecation warning if using main
export LLAMA_NO_DEPRECATION_WARNING=1

$CUDA_BINARY \\
    -m "$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --log-disable 2>&1 | grep -v "^ggml_\|^llama_\|WARNING\|deprecated"
EOF
chmod +x /moneyball/llama_gpu_final.sh

echo
echo "=== FINAL CHECK ==="
echo "Did you see GPU utilization go above 0%?"
echo "- YES: GPU inference is working! 🎉"
echo "- NO: The binary might not have CUDA compiled in properly"
echo
echo "Use: /moneyball/llama_gpu_final.sh 'your prompt'">