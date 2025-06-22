#!/bin/bash
# Fix slow GPU inference - 3 minutes is NOT normal!

echo "=== FIXING SLOW GPU INFERENCE ==="
echo "3 minutes for simple math is wrong - GPU isn't being used properly"
echo

# 1. Check current GPU status
echo "1. Current GPU utilization:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv

# 2. Kill current Ollama
echo
echo "2. Restarting Ollama with explicit GPU settings:"
pkill -f ollama
sleep 3

# 3. Set aggressive GPU usage
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_NUM_GPU=999
export OLLAMA_GPU_LAYERS=999

# 4. Start with debug info
echo
echo "3. Starting Ollama with GPU debug:"
OLLAMA_DEBUG=1 ollama serve 2>&1 | tee /tmp/ollama_gpu_debug.log &
sleep 5

# 5. Check what's happening
echo
echo "4. Checking GPU layer allocation:"
grep -i "gpu\|cuda\|layer" /tmp/ollama_gpu_debug.log | tail -20

# 6. Test with explicit GPU layers
echo
echo "5. Testing inference (monitoring GPU):"

# Start GPU monitor
nvidia-smi dmon -s u -d 5 -c 10 &
MONITOR_PID=$!

# Run test
time echo "What is 1+1?" | ollama run llama3

kill $MONITOR_PID 2>/dev/null

# 7. Alternative - recreate model with explicit GPU
echo
echo "6. Recreating model with explicit GPU settings:"
cat > /moneyball/Modelfile_gpu << EOF
FROM /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf

PARAMETER num_gpu 999
PARAMETER num_thread 8
EOF

ollama create llama3-gpu -f /moneyball/Modelfile_gpu

echo
echo "7. Testing GPU model:"
time echo "What is 1+1?" | ollama run llama3-gpu

echo
echo "=== DIAGNOSIS ==="
echo "If still slow, the issue is:"
echo "1. Model running on CPU despite GPU memory usage"
echo "2. GPU compute kernels not loading"
echo "3. Need to use different backend"
echo
echo "Alternative: Use llama.cpp directly with CUDA"