#!/bin/bash
# Build llama.cpp with CMake, CUDA enabled, curl disabled

echo "=== BUILDING LLAMA.CPP WITH CMAKE ===="
echo "CUDA enabled, curl disabled"
echo

cd /moneyball/llama.cpp

# 1. Clean any previous builds
echo "1. Cleaning previous builds:"
rm -rf build
mkdir build
cd build

# 2. Configure with CMake
echo
echo "2. Configuring with CMake:"
cmake .. \
    -DLLAMA_CUDA=ON \
    -DLLAMA_CURL=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_NATIVE=OFF \
    -DLLAMA_LTO=OFF \
    -DLLAMA_CCACHE=OFF

# 3. Build
echo
echo "3. Building with $(nproc) cores:"
cmake --build . --config Release -j $(nproc)

# 4. Check build
echo
echo "4. Checking build:"
if [ -f "bin/main" ]; then
    echo "✅ Successfully built with CMake!"
    ls -la bin/
else
    echo "❌ CMake build failed"
    echo "Build files might be in different location:"
    find . -name "main" -type f 2>/dev/null
fi

# 5. Test GPU support
echo
echo "5. Testing GPU support:"
if [ -f "bin/main" ]; then
    ./bin/main --help | grep -i "gpu\|layer" | head -5
fi

# 6. Create test with CMake binary
echo
echo "6. Creating CMake test script:"
cat > /moneyball/test_cmake_gpu.sh << 'EOF'
#!/bin/bash
# Test CMake-built llama.cpp GPU

MODEL="/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
BINARY="/moneyball/llama.cpp/build/bin/main"

if [ ! -f "$BINARY" ]; then
    echo "Binary not found at: $BINARY"
    # Try alternative location
    BINARY="/moneyball/llama.cpp/build/main"
    if [ ! -f "$BINARY" ]; then
        echo "Binary not found!"
        exit 1
    fi
fi

echo "=== CMAKE GPU TEST ==="
echo "Using binary: $BINARY"
echo "Watch GPU utilization!"
echo

# Monitor GPU
nvidia-smi dmon -s u -d 1 &
MON_PID=$!
sleep 2

# Run test
time "$BINARY" \
    -m "$MODEL" \
    -p "What is 10 divided by 2?" \
    -n 30 \
    --n-gpu-layers 999 \
    -t 8 \
    --log-disable

kill $MON_PID 2>/dev/null
wait $MON_PID 2>/dev/null

echo
echo "Done! Check if GPU Util % increased during inference."
EOF
chmod +x /moneyball/test_cmake_gpu.sh

# 7. Show CMake configuration
echo
echo "7. CMake configuration summary:"
if [ -f "CMakeCache.txt" ]; then
    echo "CUDA settings:"
    grep -i "cuda\|gpu" CMakeCache.txt | grep -v "^//" | head -10
    echo
    echo "CURL setting:"
    grep -i "curl" CMakeCache.txt | grep -v "^//"
fi

echo
echo "=== CMAKE BUILD COMPLETE ===="
echo "Test with: /moneyball/test_cmake_gpu.sh"
echo
echo "If regular make fails, this CMake approach often works better!"