#!/bin/bash
# Force Ollama to use GPU - diagnose and fix

echo "=== Forcing Ollama GPU Usage ==="

# 1. Check why GPU isn't being used
echo "1. Checking Ollama GPU detection..."
pkill -f ollama

# Check GPU with Ollama
echo "Testing GPU detection:"
/moneyball/ollama/bin/ollama --version

# 2. Check CUDA availability
echo ""
echo "2. CUDA Check:"
which nvcc || echo "nvcc not found"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# Find CUDA libraries
echo ""
echo "3. Finding CUDA libraries:"
find /usr -name "libcudart.so*" 2>/dev/null | head -5
find /usr -name "libnvidia-ml.so*" 2>/dev/null | head -5

# 4. Set full CUDA environment
echo ""
echo "4. Setting CUDA environment..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Also try to find and set nvidia libraries
NVIDIA_LIB=$(find /usr -name "libnvidia-ml.so.1" 2>/dev/null | head -1 | xargs dirname)
if [ -n "$NVIDIA_LIB" ]; then
    export LD_LIBRARY_PATH=$NVIDIA_LIB:$LD_LIBRARY_PATH
    echo "Added NVIDIA lib path: $NVIDIA_LIB"
fi

# 5. Start Ollama with explicit GPU settings
echo ""
echo "5. Starting Ollama with GPU debug..."
cd /moneyball

# Create a wrapper that forces GPU
cat > /moneyball/ollama/start_gpu_ollama.sh << 'WRAPPER'
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOME=/moneyball/ollama/data
export OLLAMA_MODELS=/moneyball/ollama/models
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Find nvidia-ml library
NVIDIA_ML=$(find /usr -name "libnvidia-ml.so*" 2>/dev/null | grep -v "stub" | head -1)
if [ -f "$NVIDIA_ML" ]; then
    export LD_LIBRARY_PATH=$(dirname "$NVIDIA_ML"):$LD_LIBRARY_PATH
fi

echo "GPU Environment:"
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

# Start with debug
OLLAMA_DEBUG=1 exec /moneyball/ollama/bin/ollama "$@"
WRAPPER
chmod +x /moneyball/ollama/start_gpu_ollama.sh

# Start server
/moneyball/ollama/start_gpu_ollama.sh serve > /moneyball/ollama/gpu_debug.log 2>&1 &
OLLAMA_PID=$!

sleep 5

# 6. Check logs for GPU errors
echo ""
echo "6. GPU Detection in logs:"
grep -i "gpu\|cuda\|nvidia" /moneyball/ollama/gpu_debug.log | tail -20

# 7. Alternative - check if this Ollama build supports GPU
echo ""
echo "7. Checking Ollama binary:"
strings /moneyball/ollama/bin/ollama | grep -i cuda | head -5

# 8. Test with monitoring
echo ""
echo "8. Testing with GPU monitoring:"
(
    while true; do
        nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
        sleep 2
    done
) &
MONITOR_PID=$!

# Run test
/moneyball/ollama/bin/ollama run llama3-legal "Test GPU usage"

sleep 5
kill $MONITOR_PID 2>/dev/null

# 9. Suggestion
echo ""
echo "=== Analysis ==="
echo "If GPU still not used, the issue might be:"
echo "1. This Ollama binary wasn't compiled with CUDA support"
echo "2. vGPU restrictions (A40-8Q might have limitations)"
echo "3. Missing CUDA runtime libraries"
echo ""
echo "Alternative: Use llama.cpp directly:"
echo "- It definitely supports GPU"
echo "- Can load GGUF files"
echo "- More control over GPU layers"