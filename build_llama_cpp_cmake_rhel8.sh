#!/bin/bash
# Build llama.cpp with CMake on RHEL8 with CUDA support

echo "=== BUILDING LLAMA.CPP WITH CMAKE ON RHEL8 ==="
echo "This script will build llama.cpp with CMake and CUDA support"
echo

# Set up environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

echo "1. Checking prerequisites..."
echo "CUDA_HOME: $CUDA_HOME"
which cmake || echo "WARNING: cmake not found"
which nvcc || echo "WARNING: nvcc not found"
echo

# Navigate to moneyball directory
cd /moneyball || exit 1

# Clean up any failed build
if [ -d "llama.cpp" ]; then
    echo "2. Cleaning up previous build..."
    cd llama.cpp
    rm -rf build CMakeCache.txt
    git clean -fdx
    git pull
else
    echo "2. Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
fi

# Create build directory
echo
echo "3. Setting up CMake build..."
mkdir -p build
cd build

# Configure with CMake
echo
echo "4. Configuring CMake with CUDA..."
cmake .. \
    -DLLAMA_CUDA=ON \
    -DCMAKE_CUDA_ARCHITECTURES=89 \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_NATIVE=OFF \
    -DLLAMA_F16C=OFF \
    -DLLAMA_AVX512=OFF

# Check if configuration succeeded
if [ $? -ne 0 ]; then
    echo "❌ CMake configuration failed!"
    echo "Trying fallback options..."
    cmake .. \
        -DLLAMA_CUDA=ON \
        -DCMAKE_BUILD_TYPE=Release
fi

# Build
echo
echo "5. Building llama.cpp..."
cmake --build . --config Release -j $(nproc)

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo
    echo "✅ Build successful!"
    
    # List built binaries
    echo
    echo "6. Built binaries:"
    find . -name "main" -type f -executable
    find . -name "llama-cli" -type f -executable
    
    # Create symlinks for easy access
    if [ -f "bin/main" ]; then
        ln -sf $(pwd)/bin/main /moneyball/llama.cpp/main
        echo "Created symlink: /moneyball/llama.cpp/main"
    elif [ -f "bin/llama-cli" ]; then
        ln -sf $(pwd)/bin/llama-cli /moneyball/llama.cpp/main
        echo "Created symlink: /moneyball/llama.cpp/main -> llama-cli"
    fi
    
    # Test GPU support
    echo
    echo "7. Testing GPU support..."
    if [ -f "/moneyball/llama.cpp/main" ]; then
        /moneyball/llama.cpp/main --help | grep -i gpu || echo "No GPU options found"
    fi
    
    # Create wrapper script
    echo
    echo "8. Creating wrapper script..."
    cat > /moneyball/llama_gpu.sh << 'EOF'
#!/bin/bash
# Direct GPU inference with llama.cpp
MODEL="${MODEL:-/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf}"

if [ ! -f "$MODEL" ]; then
    echo "Model not found: $MODEL"
    echo "Available models:"
    find /moneyball -name "*.gguf" -type f 2>/dev/null | head -10
    exit 1
fi

exec /moneyball/llama.cpp/main \
    -m "$MODEL" \
    --gpu-layers 999 \
    --threads 8 \
    --ctx-size 4096 \
    --temp 0.7 \
    --top-p 0.9 \
    -p "$*" \
    -n 500
EOF
    chmod +x /moneyball/llama_gpu.sh
    
    echo
    echo "=== BUILD COMPLETE ==="
    echo "Test with: /moneyball/llama_gpu.sh 'What is 2+2?'"
    echo "Or directly: /moneyball/llama.cpp/main -m model.gguf -p 'prompt'"
else
    echo
    echo "❌ Build failed!"
    echo "Check the error messages above"
    echo
    echo "Common fixes:"
    echo "1. Install cmake3: sudo yum install cmake3"
    echo "2. Use cmake3 instead of cmake"
    echo "3. Check CUDA installation"
    echo "4. Try without CUDA: cmake .. -DLLAMA_CUDA=OFF"
fi