#!/bin/bash
# Build llama.cpp with CMake and CUDA support

echo "=== BUILDING LLAMA.CPP WITH CMAKE AND CUDA ==="
echo

# 1. Set up environment
echo "1. Setting up CUDA environment..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

# Check requirements
echo "Checking requirements:"
which cmake3 || which cmake || echo "❌ CMake not found!"
which nvcc && nvcc --version | head -1

# 2. Fresh build
echo
echo "2. Creating fresh build..."
cd /moneyball
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUILD_DIR="llama-cmake-cuda-${TIMESTAMP}"

git clone https://github.com/ggerganov/llama.cpp "$BUILD_DIR"
cd "$BUILD_DIR"

# 3. CMake build with CUDA
echo
echo "3. Building with CMake and CUDA..."
mkdir build
cd build

# Use cmake3 if available (RHEL8), otherwise cmake
CMAKE_CMD=$(which cmake3 || which cmake)
echo "Using: $CMAKE_CMD"

# Configure with CUDA enabled, CURL disabled
$CMAKE_CMD .. \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_ARCHITECTURES=native

# Build
echo
echo "4. Compiling..."
make -j$(nproc) 2>&1 | tee ../cmake_build.log

# 4. Find binaries
echo
echo "5. Finding built binaries..."
echo "Executables in build directory:"
find . -type f -executable -name "*llama*" -o -name "main" | grep -v ".so"

# Common locations in CMake builds
for binary in bin/llama-cli bin/main bin/llama examples/main/main; do
    if [ -f "$binary" ] && [ -x "$binary" ]; then
        echo
        echo "✅ Found: $binary"
        echo "Size: $(ls -lh $binary | awk '{print $5}')"
        echo "CUDA check:"
        ldd "$binary" | grep -E "cuda|cublas" || echo "No CUDA libraries linked"
        FOUND_BINARY="$(pwd)/$binary"
    fi
done

# 5. Test if found
if [ -n "$FOUND_BINARY" ]; then
    echo
    echo "6. Testing GPU inference..."
    MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
    
    # GPU monitor
    nvidia-smi dmon -s um -d 1 -c 15 &
    MONITOR=$!
    sleep 2
    
    # Test
    $FOUND_BINARY \
        -m "$MODEL" \
        -p "Hi" \
        -n 10 \
        --gpu-layers 35 \
        --threads 4 \
        --log-disable 2>&1 | head -20
    
    kill $MONITOR 2>/dev/null
    
    # Create wrapper
    echo
    echo "7. Creating wrapper script..."
    cat > /moneyball/llama_gpu.sh << EOF
#!/bin/bash
# CMake-built CUDA llama.cpp
export LD_LIBRARY_PATH=/usr/lib64:/usr/local/cuda/lib64:\$LD_LIBRARY_PATH
$FOUND_BINARY \\
    -m "$MODEL" \\
    -p "\$*" \\
    -n 200 \\
    --gpu-layers 35 \\
    --threads 4 \\
    --log-disable 2>&1 | grep -v "^ggml_"
EOF
    chmod +x /moneyball/llama_gpu.sh
    
    echo
    echo "=== SUCCESS ==="
    echo "Binary: $FOUND_BINARY"
    echo "Wrapper: /moneyball/llama_gpu.sh 'your prompt'"
else
    echo
    echo "❌ No binary found!"
    echo "Check cmake_build.log for errors"
    tail -20 ../cmake_build.log
fi