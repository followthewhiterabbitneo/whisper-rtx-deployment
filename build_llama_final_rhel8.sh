#!/bin/bash
# Final working build script for llama.cpp on RHEL8

echo "=== BUILDING LLAMA.CPP ON RHEL8 ==="
echo

# Set up environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:$CUDA_HOME/lib64:$LD_LIBRARY_PATH

cd /moneyball/llama.cpp || exit 1

# Clean build directory
rm -rf build
mkdir build && cd build

# Configure with all the fixes
echo "Configuring CMake with RHEL8 fixes..."
cmake3 .. \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=OFF \
    -DCMAKE_CUDA_ARCHITECTURES=89 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
    -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
    -DCUDA_cudart_LIBRARY=/usr/local/cuda/lib64/libcudart.so \
    -DCUDA_cuda_LIBRARY=/usr/lib64/libcuda.so

# Check if configuration succeeded
if [ $? -ne 0 ]; then
    echo "❌ CMake configuration failed!"
    echo "Trying without CUDA..."
    cmake3 .. -DGGML_CUDA=OFF -DLLAMA_CURL=OFF
fi

# Build
echo
echo "Building llama.cpp..."
make -j$(nproc)

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo
    echo "✅ Build successful!"
    
    # Find and link the binary
    if [ -f bin/llama-cli ]; then
        ln -sf $(pwd)/bin/llama-cli /moneyball/llama.cpp/main
        echo "Linked: /moneyball/llama.cpp/main -> llama-cli"
    elif [ -f bin/main ]; then
        ln -sf $(pwd)/bin/main /moneyball/llama.cpp/main
        echo "Linked: /moneyball/llama.cpp/main"
    fi
    
    # Test
    echo
    echo "Testing llama.cpp..."
    /moneyball/llama.cpp/main --version || echo "Version check failed"
    
    # Create final wrapper
    cat > /moneyball/llama_test.sh << 'EOF'
#!/bin/bash
# Test llama.cpp with a model
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Find a model
MODEL=$(find /moneyball -name "*.gguf" -type f 2>/dev/null | grep -i llama | head -1)
if [ -z "$MODEL" ]; then
    MODEL=$(find /moneyball -name "*.gguf" -type f 2>/dev/null | head -1)
fi

if [ -z "$MODEL" ]; then
    echo "No GGUF model found!"
    echo "Download a model first"
    exit 1
fi

echo "Using model: $MODEL"
echo "Testing with prompt: 'What is 2+2?'"
echo

/moneyball/llama.cpp/main \
    -m "$MODEL" \
    -p "What is 2+2?" \
    -n 50 \
    --gpu-layers 33 \
    --threads 8
EOF
    chmod +x /moneyball/llama_test.sh
    
    echo
    echo "=== BUILD COMPLETE ==="
    echo "Test with: /moneyball/llama_test.sh"
else
    echo
    echo "❌ Build failed!"
fi