#!/bin/bash
# Rebuild llama.cpp with CUDA - using the working configuration

echo "=== REBUILDING LLAMA.CPP WITH CUDA (PROVEN CONFIG) ==="
echo "Based on successful GPU inference configuration"
echo

# 1. Set up environment (as documented in CLAUDE.md)
echo "1. Setting up CUDA environment..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Verify CUDA
echo "CUDA check:"
which nvcc && nvcc --version || echo "WARNING: nvcc not found"
echo

# 2. Create fresh build directory
echo "2. Creating fresh build..."
cd /moneyball
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_DIR="llama-cuda-${TIMESTAMP}"

# Clone fresh copy
git clone https://github.com/ggerganov/llama.cpp "$BUILD_DIR"
cd "$BUILD_DIR"

# Use stable version that worked
echo "3. Using stable version b3447..."
git checkout b3447

# 3. Build with CUDA
echo
echo "4. Building with CUDA support..."
echo "This is the exact build process that worked before"

# Clean build with CUDA
make clean
LLAMA_CUDA=1 make -j$(nproc) 2>&1 | tee build.log

# 4. Verify CUDA was compiled in
echo
echo "5. Verifying CUDA support..."
if [ -f "main" ]; then
    echo "✅ Binary created: $(pwd)/main"
    
    # Check for CUDA libraries
    echo
    echo "Checking CUDA libraries:"
    ldd main | grep -E "cuda|cublas" || echo "WARNING: No CUDA libraries linked"
    
    # Check file size (CUDA builds are larger)
    echo
    echo "Binary size:"
    ls -lh main
    
    # Check for GPU options
    echo
    echo "GPU options:"
    ./main --help 2>&1 | grep -i "gpu" | head -5 || echo "No GPU options found"
else
    echo "❌ Build failed!"
    exit 1
fi

# 5. Test GPU inference
echo
echo "6. Testing GPU inference..."
MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

if [ -f "$MODEL" ]; then
    echo "Quick GPU test with monitoring..."
    
    # Monitor GPU
    nvidia-smi dmon -s um -d 1 -c 15 &
    MONITOR=$!
    sleep 2
    
    # Run test
    ./main \
        -m "$MODEL" \
        -p "Hello world" \
        -n 10 \
        --gpu-layers 35 \
        --threads 4 \
        --log-disable 2>&1 | grep -v "^ggml_"
    
    kill $MONITOR 2>/dev/null
    
    echo
    echo "Check if GPU utilization went above 0%"
fi

# 6. Create symlinks for easy access
echo
echo "7. Creating convenient access..."
ln -sf "$(pwd)/main" /moneyball/llama-gpu-latest
echo "Created symlink: /moneyball/llama-gpu-latest"

# Update the working script
cat > /moneyball/llama_gpu.sh << EOF
#!/bin/bash
# Updated GPU-accelerated llama.cpp

# Use latest build
BINARY="/moneyball/${BUILD_DIR}/main"
MODEL="$MODEL"

# Set library paths (important for vGPU)
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:\$LD_LIBRARY_PATH

\$BINARY \\
    -m "\$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --temp 0.7 \\
    --log-disable 2>&1 | grep -v "^ggml_\|deprecated"
EOF
chmod +x /moneyball/llama_gpu.sh

echo
echo "=== BUILD COMPLETE ==="
echo "New binary: /moneyball/${BUILD_DIR}/main"
echo "Symlink: /moneyball/llama-gpu-latest"
echo "Wrapper: /moneyball/llama_gpu.sh 'your prompt'"
echo
echo "Previous working binary preserved at: /moneyball/llama-cuda/main"