#!/bin/bash
# Force Ollama to detect virtual GPU (GRID/vGPU)

echo "=== FORCING OLLAMA TO DETECT VIRTUAL GPU ==="
echo

# 1. Check actual GPU
echo "1. Your GPU details:"
nvidia-smi -L
nvidia-smi --query-gpu=name,compute_cap --format=csv

# 2. Check why Ollama can't see it
echo
echo "2. Debugging Ollama GPU detection..."
# Ollama uses nvidia-ml library
python3 -c "
try:
    import pynvml
    pynvml.nvmlInit()
    count = pynvml.nvmlDeviceGetCount()
    print(f'Python sees {count} GPU(s)')
    for i in range(count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle).decode()
        print(f'GPU {i}: {name}')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null || echo "pynvml not available"

# 3. Force Ollama to use GPU anyway
echo
echo "3. Creating forced GPU config..."
cat > /moneyball/ollama_force_gpu.sh << 'EOF'
#!/bin/bash
# Force Ollama to use GPU even if it can't detect it

echo "Forcing Ollama GPU usage..."

# Set environment to force GPU
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_NUM_GPU=1
export OLLAMA_GPU_LAYERS=35
export OLLAMA_CUDA_FORCE_DISABLE=false
export OLLAMA_SKIP_GPU_DISCOVERY=true

# For virtual GPUs
export NVIDIA_VISIBLE_DEVICES=0
export NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Kill old instance
pkill -f ollama

# Try to start with forced GPU
echo "Starting Ollama with forced GPU settings..."
OLLAMA_DEBUG=1 ollama serve 2>&1 | tee /tmp/ollama_force_gpu.log &
OLLAMA_PID=$!

echo "Ollama PID: $OLLAMA_PID"
echo "Watching log for GPU messages..."
sleep 5

# Check if it still complains
if grep -i "no compatible GPUs" /tmp/ollama_force_gpu.log; then
    echo
    echo "❌ Ollama still can't use GPU"
    echo "This is a known issue with virtual GPUs (GRID/vGPU)"
else
    echo "✅ Ollama started"
fi

echo
echo "Log: tail -f /tmp/ollama_force_gpu.log"
EOF
chmod +x /moneyball/ollama_force_gpu.sh

# 4. Alternative: Patch Ollama binary
echo
echo "4. Creating Ollama patcher (advanced)..."
cat > /moneyball/patch_ollama_vgpu.sh << 'EOF'
#!/bin/bash
# Patch Ollama for vGPU support

echo "Checking Ollama binary..."
OLLAMA_BIN=$(which ollama)
echo "Ollama at: $OLLAMA_BIN"

# Check what it's looking for
echo
echo "GPU detection strings in Ollama:"
strings $OLLAMA_BIN | grep -i "compatible\|gpu\|cuda" | grep -i "no\|fail\|error" | head -10

echo
echo "To fix vGPU detection, you may need:"
echo "1. Newer Ollama version with vGPU support"
echo "2. Use llama.cpp directly instead"
echo "3. Install Ollama from source with vGPU patches"
EOF
chmod +x /moneyball/patch_ollama_vgpu.sh

# 5. Final solution: Use llama.cpp
echo
echo "5. Creating llama.cpp wrapper (works with vGPU)..."
cat > /moneyball/use_llamacpp_instead.sh << 'EOF'
#!/bin/bash
# Use llama.cpp which works with virtual GPUs

echo "=== USING LLAMA.CPP INSTEAD OF OLLAMA ==="
echo "llama.cpp handles virtual GPUs better"

# Find working binary
LLAMA_BIN=""
for bin in /moneyball/llama-simple/main /moneyball/llama.cpp/llama-cli /moneyball/llama.cpp/main; do
    if [ -x "$bin" ]; then
        LLAMA_BIN="$bin"
        echo "Found: $bin"
        break
    fi
done

if [ -z "$LLAMA_BIN" ]; then
    echo "No llama.cpp found. Building..."
    cd /moneyball/llama-simple || exit 1
    LLAMA_CUDA=1 make clean && LLAMA_CUDA=1 make -j4
    LLAMA_BIN="/moneyball/llama-simple/main"
fi

# Test with GPU
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

echo "Testing GPU inference with llama.cpp..."
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=$!
sleep 1

$LLAMA_BIN -m "$MODEL" -p "What is 2+2?" -n 50 --gpu-layers 35

kill $MONITOR 2>/dev/null

echo
echo "If GPU usage went up, use llama.cpp instead of Ollama"
EOF
chmod +x /moneyball/use_llamacpp_instead.sh

echo
echo "=== VIRTUAL GPU (vGPU) ISSUE ==="
echo "Ollama has problems detecting virtual GPUs (GRID/vGPU)"
echo
echo "Try these solutions:"
echo "1. Force GPU: /moneyball/ollama_force_gpu.sh"
echo "2. Check issue: /moneyball/patch_ollama_vgpu.sh"
echo "3. Use llama.cpp: /moneyball/use_llamacpp_instead.sh"
echo
echo "llama.cpp usually works better with virtual GPUs!"