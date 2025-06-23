#!/bin/bash
# Fix Ollama/llama.cpp CUDA runtime issue

echo "=== FIXING CUDA RUNTIME FOR OLLAMA/LLAMA.CPP ==="
echo "Problem: Model loads in VRAM but inference runs on CPU"
echo

# 1. Check CUDA versions
echo "1. Checking CUDA driver vs runtime versions..."
echo "Driver version:"
nvidia-smi | grep "Driver Version" || echo "Can't get driver version"

echo
echo "CUDA runtime version:"
nvcc --version | grep "release" || echo "No nvcc found"

echo
echo "2. Checking CUDA libraries..."
echo "libcudart (CUDA runtime):"
find /usr -name "libcudart.so*" 2>/dev/null | head -5

echo
echo "libcublas (needed for inference):"
find /usr -name "libcublas.so*" 2>/dev/null | head -5

# 3. Fix library paths for Ollama
echo
echo "3. Creating Ollama fix script..."
cat > /moneyball/fix_ollama_gpu.sh << 'EOF'
#!/bin/bash
# Force Ollama to use correct CUDA libraries

# Kill existing Ollama
pkill -f ollama

# Set correct library paths
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:/usr/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Check what Ollama is using
echo "Ollama binary location:"
which ollama

echo
echo "Ollama CUDA dependencies:"
ldd $(which ollama) | grep -E "cuda|cublas" || echo "No CUDA libs found"

# Start Ollama with debug info
echo
echo "Starting Ollama with CUDA debug..."
OLLAMA_DEBUG=1 ollama serve &
sleep 5

# Test inference
echo
echo "Testing GPU inference..."
nvidia-smi dmon -s u -d 1 -c 10 &
MONITOR=$!
sleep 1

time ollama run llama3:8b "What is 2+2?"

kill $MONITOR 2>/dev/null
EOF
chmod +x /moneyball/fix_ollama_gpu.sh

# 4. Alternative: Use LD_PRELOAD
echo
echo "4. Creating LD_PRELOAD fix..."
cat > /moneyball/ollama_gpu_preload.sh << 'EOF'
#!/bin/bash
# Force load CUDA libraries

export LD_PRELOAD="/usr/local/cuda/lib64/libcudart.so:/usr/local/cuda/lib64/libcublas.so"
export CUDA_VISIBLE_DEVICES=0

echo "Starting Ollama with preloaded CUDA libraries..."
ollama serve
EOF
chmod +x /moneyball/ollama_gpu_preload.sh

# 5. Check for multiple CUDA installations
echo
echo "5. Checking for multiple CUDA installations..."
find / -name "libcudart.so" 2>/dev/null | grep -v "/proc" | head -10

# 6. Create test script
echo
echo "6. Creating CUDA test script..."
cat > /moneyball/test_cuda_libs.py << 'EOF'
#!/usr/bin/env python3
import ctypes
import os

print("Testing CUDA library loading...")

# Try to load CUDA libraries
libs = [
    "/usr/local/cuda/lib64/libcudart.so",
    "/usr/lib64/libcudart.so",
    "libcudart.so"
]

for lib in libs:
    try:
        ctypes.CDLL(lib)
        print(f"✅ Loaded: {lib}")
    except:
        print(f"❌ Failed: {lib}")

# Check environment
print("\nEnvironment:")
print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
print(f"CUDA_HOME: {os.environ.get('CUDA_HOME', 'Not set')}")
EOF
chmod +x /moneyball/test_cuda_libs.py

echo
echo "=== DIAGNOSIS ==="
echo "This is likely a CUDA runtime library issue where:"
echo "1. Model loads to VRAM (CUDA driver works)"
echo "2. Inference runs on CPU (CUDA runtime not found)"
echo
echo "Try these fixes:"
echo "1. /moneyball/fix_ollama_gpu.sh      # Set paths and test"
echo "2. /moneyball/ollama_gpu_preload.sh  # Force load CUDA libs"
echo "3. /moneyball/test_cuda_libs.py      # Test library loading"
echo
echo "The issue is usually that Ollama/llama.cpp can't find libcublas.so"