#!/bin/bash
# Rebuild llama.cpp with CUDA - handles both main and llama-cli

echo "=== REBUILDING LLAMA.CPP WITH CUDA (MODERN VERSION) ==="
echo

# 1. Set up environment
echo "1. Setting up CUDA environment..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Check CUDA
which nvcc && nvcc --version || echo "WARNING: nvcc not found"
echo

# 2. Build directory
cd /moneyball
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_DIR="llama-cuda-${TIMESTAMP}"

# Clone latest version (not old b3447)
echo "2. Cloning latest llama.cpp..."
git clone https://github.com/ggerganov/llama.cpp "$BUILD_DIR"
cd "$BUILD_DIR"

# Get current version
echo "Version:"
git log --oneline -1

# 3. Build with CUDA
echo
echo "3. Building with CUDA support..."
make clean

# Modern llama.cpp uses GGML_CUDA
GGML_CUDA=1 make -j$(nproc) 2>&1 | tee build.log

# Also try old flag in case
if [ ! -f "llama-cli" ] && [ ! -f "main" ]; then
    echo "Trying with LLAMA_CUDA flag..."
    make clean
    LLAMA_CUDA=1 make -j$(nproc) 2>&1 | tee build_alt.log
fi

# 4. Find which binary was created
echo
echo "4. Checking which binary was created..."
BINARY=""
BINARY_TYPE=""

if [ -f "build/bin/llama-cli" ]; then
    BINARY="$(pwd)/build/bin/llama-cli"
    BINARY_TYPE="llama-cli (new)"
elif [ -f "llama-cli" ]; then
    BINARY="$(pwd)/llama-cli"
    BINARY_TYPE="llama-cli"
elif [ -f "build/bin/main" ]; then
    BINARY="$(pwd)/build/bin/main"
    BINARY_TYPE="main (in build/bin)"
elif [ -f "main" ]; then
    BINARY="$(pwd)/main"
    BINARY_TYPE="main (deprecated)"
else
    echo "❌ No binary found!"
    echo "Checking build directory:"
    find . -name "llama-cli" -o -name "main" 2>/dev/null
    exit 1
fi

echo "✅ Found binary: $BINARY_TYPE"
echo "Path: $BINARY"

# 5. Verify CUDA support
echo
echo "5. Verifying CUDA support..."
echo "Checking CUDA libraries:"
ldd "$BINARY" | grep -E "cuda|cublas" || echo "WARNING: No CUDA libraries"

echo
echo "Checking GPU options:"
"$BINARY" --help 2>&1 | grep -i "gpu" | head -5 || echo "No GPU options"

# 6. Test GPU
echo
echo "6. Testing GPU inference..."
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

if [ -f "$MODEL" ]; then
    # Suppress deprecation warning
    export LLAMA_NO_DEPRECATION_WARNING=1
    
    echo "GPU Monitor (watch for >0% utilization):"
    nvidia-smi dmon -s um -d 1 -c 15 &
    MONITOR=$!
    sleep 2
    
    "$BINARY" \
        -m "$MODEL" \
        -p "Test" \
        -n 10 \
        --gpu-layers 35 \
        --threads 4 \
        --log-disable 2>&1 | grep -v "^ggml_\|deprecated\|WARNING"
    
    kill $MONITOR 2>/dev/null
fi

# 7. Create universal wrapper
echo
echo "7. Creating universal wrapper..."
cat > /moneyball/llama_gpu.sh << EOF
#!/bin/bash
# Universal GPU-accelerated llama.cpp wrapper

# Suppress deprecation warnings
export LLAMA_NO_DEPRECATION_WARNING=1

# Set library paths
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:\$LD_LIBRARY_PATH

# Use the binary we just built
BINARY="$BINARY"
MODEL="$MODEL"

\$BINARY \\
    -m "\$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --temp 0.7 \\
    --log-disable 2>&1 | grep -v "^ggml_\|deprecated\|WARNING"
EOF
chmod +x /moneyball/llama_gpu.sh

# Create symlink
ln -sf "$BINARY" /moneyball/llama-gpu-latest

echo
echo "=== BUILD COMPLETE ==="
echo "Binary type: $BINARY_TYPE"
echo "Binary path: $BINARY"
echo "Wrapper: /moneyball/llama_gpu.sh 'your prompt'"
echo "Symlink: /moneyball/llama-gpu-latest"