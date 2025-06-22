#!/bin/bash
# Build llama.cpp with filesystem fix for RHEL8

echo "=== BUILDING LLAMA.CPP WITH FILESYSTEM FIX ==="
echo

# Set up environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:$CUDA_HOME/lib64:$LD_LIBRARY_PATH

cd /moneyball/llama.cpp || exit 1

# Clean build directory
rm -rf build
mkdir build && cd build

# Configure with filesystem fix
echo "Configuring with C++17 filesystem fix..."
cmake3 .. \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=OFF \
    -DCMAKE_CUDA_ARCHITECTURES=89 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_FLAGS="-std=c++17" \
    -DCMAKE_EXE_LINKER_FLAGS="-lstdc++fs" \
    -DCMAKE_SHARED_LINKER_FLAGS="-lstdc++fs"

# If that fails, try with explicit standard library
if [ $? -ne 0 ]; then
    echo "Trying alternative filesystem linking..."
    cmake3 .. \
        -DGGML_CUDA=ON \
        -DLLAMA_CURL=OFF \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_STANDARD=17 \
        -DCMAKE_CXX_STANDARD_REQUIRED=ON \
        -DCMAKE_CXX_FLAGS="-std=c++17 -pthread" \
        -DCMAKE_EXE_LINKER_FLAGS="-lstdc++fs -pthread" \
        -DCMAKE_SHARED_LINKER_FLAGS="-lstdc++fs -pthread"
fi

# Build
echo
echo "Building with filesystem support..."
make -j$(nproc) VERBOSE=1

# If build fails at linking, try manual fix
if [ $? -ne 0 ]; then
    echo
    echo "Build failed - trying manual filesystem link fix..."
    
    # Find all CMakeFiles and add filesystem library
    find . -name "link.txt" -exec sed -i 's/$/& -lstdc++fs/' {} \;
    
    # Retry build
    make -j$(nproc)
fi

# Check result
if [ -f bin/llama-cli ] || [ -f bin/main ]; then
    echo "✅ Build successful!"
    
    # Link binary
    if [ -f bin/llama-cli ]; then
        ln -sf $(pwd)/bin/llama-cli /moneyball/llama.cpp/main
    elif [ -f bin/main ]; then
        ln -sf $(pwd)/bin/main /moneyball/llama.cpp/main
    fi
    
    echo "Test with: /moneyball/llama.cpp/main --version"
else
    echo "❌ Build still failed"
    echo
    echo "Alternative: Try older llama.cpp version"
    echo "cd /moneyball && rm -rf llama.cpp"
    echo "git clone --branch b3447 https://github.com/ggerganov/llama.cpp"
fi