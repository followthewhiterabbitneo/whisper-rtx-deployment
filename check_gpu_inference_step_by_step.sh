#!/bin/bash
# Step by step GPU inference verification

echo "=== STEP-BY-STEP GPU INFERENCE CHECK ==="
echo "We have inference working, now let's verify GPU usage"
echo

# Step 1: Baseline GPU state
echo "Step 1: Current GPU state (before inference)"
echo "========================================"
nvidia-smi --query-gpu=index,name,memory.used,memory.free,utilization.gpu --format=csv
echo

# Step 2: Check what binary we're using
echo "Step 2: Which llama.cpp binary are we using?"
echo "============================================"
LLAMA_BIN=$(which llama 2>/dev/null || echo "")
if [ -z "$LLAMA_BIN" ]; then
    # Find the working binary
    for bin in /moneyball/llama.cpp/llama-cli /moneyball/llama.cpp/main /moneyball/llama-simple/main; do
        if [ -x "$bin" ]; then
            LLAMA_BIN="$bin"
            break
        fi
    done
fi
echo "Binary: $LLAMA_BIN"
echo "Checking if it has CUDA support..."
ldd "$LLAMA_BIN" 2>/dev/null | grep -E "cuda|cublas" || echo "No CUDA libraries linked"
echo

# Step 3: Simple GPU test
echo "Step 3: Quick GPU test with monitoring"
echo "======================================"
echo "Instructions: Watch the 'sm' column - it shows GPU compute usage %"
echo "If it stays at 0%, inference is on CPU. If it goes up, GPU is working!"
echo
echo "Starting monitor (20 seconds)..."

# Start monitor in background, save to file
nvidia-smi dmon -s u -d 1 -c 20 > /tmp/gpu_monitor.txt &
MONITOR_PID=$!
sleep 2

# Find model
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Run short inference
echo "Running inference..."
if [ -n "$LLAMA_BIN" ] && [ -f "$MODEL" ]; then
    $LLAMA_BIN -m "$MODEL" -p "Count to 5" -n 20 --gpu-layers 35 2>&1 | grep -v "^ggml_"
else
    echo "Binary or model not found!"
fi

# Wait for monitor to finish
wait $MONITOR_PID

# Step 4: Analyze results
echo
echo "Step 4: GPU usage analysis"
echo "=========================="
echo "GPU utilization during inference:"
cat /tmp/gpu_monitor.txt | grep -v "^#" | awk '{print $3"%"}' | sort -n | tail -5 | while read usage; do
    echo "  Peak usage: $usage"
done

MAX_USAGE=$(cat /tmp/gpu_monitor.txt | grep -v "^#" | awk '{print $3}' | sort -n | tail -1)
echo
if [ "$MAX_USAGE" -gt "0" ]; then
    echo "✅ GPU IS BEING USED! Peak: ${MAX_USAGE}%"
else
    echo "❌ GPU NOT USED (0% utilization)"
fi

# Step 5: Memory check
echo
echo "Step 5: GPU memory usage"
echo "======================="
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
echo "If this increased from Step 1, model is loaded in VRAM"

# Step 6: Create detailed test
echo
echo "Step 6: Creating detailed GPU test script"
echo "========================================"
cat > /moneyball/gpu_inference_test.sh << 'EOF'
#!/bin/bash
# Detailed GPU inference test

echo "=== DETAILED GPU INFERENCE TEST ==="

# Test different GPU layer counts
for layers in 0 20 35; do
    echo
    echo "Testing with --gpu-layers $layers"
    echo "--------------------------------"
    
    # Clear GPU memory
    sleep 2
    
    # Monitor GPU
    nvidia-smi dmon -s u -d 1 -c 10 > /tmp/gpu_test_${layers}.txt &
    MON=$!
    sleep 1
    
    # Run inference
    time $LLAMA_BIN -m $MODEL -p "Hi" -n 10 --gpu-layers $layers 2>&1 | grep -v "^ggml_" | tail -5
    
    kill $MON 2>/dev/null
    wait $MON 2>/dev/null
    
    # Check max usage
    MAX=$(awk '{if($3>max)max=$3}END{print max}' /tmp/gpu_test_${layers}.txt 2>/dev/null)
    echo "Max GPU usage: ${MAX:-0}%"
done

echo
echo "Compare the times and GPU usage:"
echo "- layers=0 should be slowest, 0% GPU"
echo "- layers=35 should be fastest, >0% GPU"
EOF
chmod +x /moneyball/gpu_inference_test.sh

echo
echo "=== NEXT STEPS ==="
echo "1. If GPU usage was 0%, we need to check why"
echo "2. Run detailed test: /moneyball/gpu_inference_test.sh"
echo "3. This will compare CPU vs GPU inference"