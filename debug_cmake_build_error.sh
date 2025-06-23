#!/bin/bash
# Debug CMake build error at 48%

echo "=== DEBUGGING CMAKE BUILD ERROR ==="
echo

# 1. Find latest build directory
LATEST_BUILD=$(ls -dt /moneyball/llama-cmake-cuda-* 2>/dev/null | head -1)
if [ -d "$LATEST_BUILD" ]; then
    echo "1. Checking build at: $LATEST_BUILD"
    cd "$LATEST_BUILD/build"
    
    # Check build log
    echo
    echo "2. Last error in build log:"
    if [ -f "../cmake_build.log" ]; then
        grep -B5 -A5 "error:" ../cmake_build.log | tail -30
    else
        echo "No cmake_build.log found"
    fi
    
    # Check CMake errors
    echo
    echo "3. CMake configuration:"
    if [ -f "CMakeCache.txt" ]; then
        grep -E "CUDA|CMAKE_BUILD_TYPE|CMAKE_CXX_COMPILER" CMakeCache.txt | head -10
    fi
fi

# 2. Common fixes
echo
echo "4. Creating build script with common fixes..."
cat > /moneyball/build_llama_cmake_fixed.sh << 'EOF'
#!/bin/bash
# Build llama.cpp with CMake - with error fixes

echo "=== BUILDING LLAMA.CPP (FIXED VERSION) ==="

# Environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH

cd /moneyball
rm -rf llama-cmake-fixed
git clone https://github.com/ggerganov/llama.cpp llama-cmake-fixed
cd llama-cmake-fixed

# Try older stable version if latest fails
echo "Using stable version..."
git checkout b3719  # Known stable version

mkdir build && cd build

# Configure with minimal options first
echo "Configuring with minimal options..."
cmake3 .. \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DCMAKE_BUILD_TYPE=Release

# Build only the main binary
echo
echo "Building main binary only..."
make llama-cli -j4 2>&1 | tee build_fixed.log || make main -j4 2>&1 | tee -a build_fixed.log

# Check what was built
echo
echo "Checking for binaries..."
find . -name "llama-cli" -o -name "main" -type f -executable

# If that fails, try make without cmake
if [ ! -f "bin/llama-cli" ] && [ ! -f "bin/main" ]; then
    echo
    echo "CMake failed, trying simple make..."
    cd ..
    make clean
    GGML_CUDA=1 make main -j4
    ls -la main
fi
EOF
chmod +x /moneyball/build_llama_cmake_fixed.sh

# 3. Alternative: Use the working old version
echo
echo "5. Alternative - use the working version..."
cat > /moneyball/use_working_binary.sh << 'EOF'
#!/bin/bash
# Use the previously working binary

echo "Using previously working binary..."
WORKING_BIN="/moneyball/llama-cuda/main"

if [ -f "$WORKING_BIN" ]; then
    echo "Found: $WORKING_BIN"
    echo "Testing..."
    
    nvidia-smi dmon -s um -d 1 -c 10 &
    MON=$!
    sleep 1
    
    $WORKING_BIN \
        -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
        -p "test" \
        -n 10 \
        --gpu-layers 35
    
    kill $MON 2>/dev/null
else
    echo "No working binary found at $WORKING_BIN"
fi
EOF
chmod +x /moneyball/use_working_binary.sh

echo
echo "=== SOLUTIONS ==="
echo "1. Try fixed build: /moneyball/build_llama_cmake_fixed.sh"
echo "2. Use working binary: /moneyball/use_working_binary.sh"
echo "3. The error at 48% is likely due to:"
echo "   - C++ standard library issues"
echo "   - Missing dependencies"
echo "   - Too new version incompatible with RHEL8"