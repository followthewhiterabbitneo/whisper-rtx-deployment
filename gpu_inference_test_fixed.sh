#!/bin/bash
# Fixed GPU inference test with proper variables

echo "=== DETAILED GPU INFERENCE TEST ==="

# Find llama binary
LLAMA_BIN=""
for bin in /moneyball/llama.cpp/llama-cli /moneyball/llama.cpp/main /moneyball/llama-simple/main /moneyball/working_llama; do
    if [ -x "$bin" ]; then
        LLAMA_BIN="$bin"
        echo "Using binary: $bin"
        break
    fi
done

if [ -z "$LLAMA_BIN" ]; then
    echo "❌ No llama.cpp binary found!"
    exit 1
fi

# Find model
MODEL=""
for model in /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf /moneyball/models/*.gguf; do
    if [ -f "$model" ]; then
        MODEL="$model"
        echo "Using model: $model"
        break
    fi
done

if [ -z "$MODEL" ]; then
    echo "❌ No GGUF model found!"
    exit 1
fi

# Test different GPU layer counts
echo
echo "Testing inference with different GPU layers..."
echo "============================================="

for layers in 0 20 35; do
    echo
    echo "Test: --gpu-layers $layers"
    echo "-------------------------"
    
    # Clear line
    sleep 1
    
    # Monitor GPU
    nvidia-smi dmon -s u -d 1 -c 10 > /tmp/gpu_test_${layers}.txt &
    MON=$!
    sleep 1
    
    # Run inference
    START=$(date +%s.%N)
    $LLAMA_BIN -m "$MODEL" -p "What is 2+2?" -n 20 --gpu-layers $layers 2>&1 | grep -v "^ggml_" | tail -5
    END=$(date +%s.%N)
    
    kill $MON 2>/dev/null
    wait $MON 2>/dev/null
    
    # Calculate time
    TIME=$(echo "$END - $START" | bc 2>/dev/null || echo "N/A")
    echo "Time: $TIME seconds"
    
    # Check max GPU usage
    if [ -f /tmp/gpu_test_${layers}.txt ]; then
        MAX=$(awk '{if(NR>1 && $3>max)max=$3}END{print max}' /tmp/gpu_test_${layers}.txt 2>/dev/null || echo "0")
        echo "Max GPU usage: ${MAX}%"
    fi
done

echo
echo "=== RESULTS SUMMARY ==="
echo "- layers=0 (CPU only) should be slowest with 0% GPU"
echo "- layers=35 (GPU) should be fastest with >0% GPU usage"
echo
echo "If all show 0% GPU, the binary may not have CUDA support compiled in"