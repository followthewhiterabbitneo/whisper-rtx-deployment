#!/bin/bash
# Fix Ollama GPU detection issue

echo "=== FIXING OLLAMA GPU DETECTION ==="
echo "Ollama is stuck 'looking for compatible GPUs'"
echo

# 1. Check GPU visibility
echo "1. Checking if GPU is visible to system..."
nvidia-smi -L
echo
nvidia-ml-py3 2>/dev/null || echo "nvidia-ml-py not installed"

# 2. Check CUDA version mismatch
echo
echo "2. Checking CUDA versions..."
echo "Driver CUDA version:"
nvidia-smi | grep "CUDA Version" | awk '{print $9}'
echo
echo "Runtime CUDA version:"
nvcc --version 2>/dev/null | grep release || echo "No nvcc found"

# 3. Check what Ollama is looking for
echo
echo "3. Checking Ollama's CUDA requirements..."
# Ollama bundles its own CUDA libraries
ls -la /usr/lib/ollama/cuda* 2>/dev/null || echo "No Ollama CUDA libs in /usr/lib"
ls -la ~/.ollama/cuda* 2>/dev/null || echo "No Ollama CUDA libs in home"

# 4. Force Ollama to recognize GPU
echo
echo "4. Creating GPU detection fix..."
cat > /moneyball/force_ollama_gpu.sh << 'EOF'
#!/bin/bash
# Force Ollama to detect GPU

echo "Forcing Ollama GPU detection..."

# Method 1: Set CUDA device explicitly
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# Method 2: Use Ollama's own CUDA libraries
if [ -d /usr/lib/ollama ]; then
    echo "Using Ollama's bundled CUDA..."
    export LD_LIBRARY_PATH=/usr/lib/ollama:$LD_LIBRARY_PATH
fi

# Method 3: Debug mode
export OLLAMA_DEBUG=1
export OLLAMA_GPU_DISCOVERY=1

# Kill existing Ollama
pkill -f "ollama serve"
sleep 2

# Start with debug output
echo "Starting Ollama with debug output..."
echo "Watch for GPU detection messages..."
echo
ollama serve 2>&1 | tee /tmp/ollama_gpu_debug.log &
OLLAMA_PID=$!

# Wait for startup
sleep 10

# Check if it found GPU
if grep -i "gpu" /tmp/ollama_gpu_debug.log; then
    echo
    echo "GPU detection messages found!"
else
    echo
    echo "No GPU messages - checking log..."
    grep -i "cuda\|nvidia\|gpu" /tmp/ollama_gpu_debug.log || echo "No CUDA/GPU references"
fi

echo
echo "Ollama PID: $OLLAMA_PID"
echo "Full log: /tmp/ollama_gpu_debug.log"
echo "Kill with: kill $OLLAMA_PID"
EOF
chmod +x /moneyball/force_ollama_gpu.sh

# 5. Alternative: Use specific Ollama version
echo
echo "5. Creating Ollama version check..."
cat > /moneyball/check_ollama_version.sh << 'EOF'
#!/bin/bash
# Check Ollama version and GPU support

echo "Ollama version:"
ollama --version

echo
echo "Checking Ollama binary for CUDA support..."
strings $(which ollama) | grep -i "cuda" | grep -E "11\.|12\." | sort -u | head -10

echo
echo "Ollama expects CUDA versions:"
strings $(which ollama) | grep -E "cuda_v1[12]" | sort -u

# Check if running in container/VM
echo
echo "Checking virtualization..."
systemd-detect-virt || echo "Not virtualized"

# GPU passthrough check
echo
echo "Checking GPU passthrough..."
lspci | grep -i nvidia
EOF
chmod +x /moneyball/check_ollama_version.sh

# 6. Nuclear option - bypass Ollama
echo
echo "6. Creating direct llama.cpp alternative..."
cat > /moneyball/bypass_ollama.sh << 'EOF'
#!/bin/bash
# If Ollama won't detect GPU, use llama.cpp directly

echo "Bypassing Ollama - using llama.cpp directly..."

# Find working llama binary
LLAMA_BIN=""
for bin in /moneyball/llama.cpp/llama-cli /moneyball/llama-simple/main /moneyball/working_llama; do
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        LLAMA_BIN="$bin"
        break
    fi
done

if [ -n "$LLAMA_BIN" ]; then
    echo "Using: $LLAMA_BIN"
    MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
    
    # Test with GPU layers
    $LLAMA_BIN -m "$MODEL" -p "What is 2+2?" -n 50 --gpu-layers 35
else
    echo "No llama.cpp binary found"
    echo "Build one with: cd /moneyball/llama-simple && make clean && LLAMA_CUDA=1 make"
fi
EOF
chmod +x /moneyball/bypass_ollama.sh

echo
echo "=== DIAGNOSIS COMPLETE ==="
echo "Try these in order:"
echo "1. /moneyball/check_ollama_version.sh  # Check CUDA version mismatch"
echo "2. /moneyball/force_ollama_gpu.sh      # Force GPU detection with debug"
echo "3. /moneyball/bypass_ollama.sh         # Skip Ollama, use llama.cpp"
echo
echo "The issue is likely:"
echo "- CUDA version mismatch (Ollama wants specific version)"
echo "- Virtual GPU not properly passed through"
echo "- Ollama's bundled CUDA conflicts with system CUDA"