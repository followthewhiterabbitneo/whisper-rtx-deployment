#!/bin/bash
# Install llama.cpp with CMake and CUDA support

echo "=== INSTALLING LLAMA.CPP WITH CMAKE & CUDA ===="
echo "Using CMake for better CUDA detection and configuration"
echo

# 1. Check prerequisites
echo "1. Checking prerequisites:"
which cmake >/dev/null 2>&1 || { echo "❌ cmake not found! Install with: sudo yum install cmake3"; exit 1; }
which nvcc >/dev/null 2>&1 || { echo "⚠️  nvcc not found, but may still work with runtime CUDA"; }

cd /moneyball

# 2. Clone or update llama.cpp
echo
echo "2. Setting up llama.cpp:"
if [ -d "llama.cpp" ]; then
    echo "Updating existing repository..."
    cd llama.cpp
    git pull
    rm -rf build  # Clean previous build
else
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
fi

# 3. Create build directory
echo
echo "3. Creating CMake build directory:"
mkdir -p build
cd build

# 4. Configure with CMake
echo
echo "4. Configuring with CMake (CUDA enabled):"
cmake .. \
    -DLLAMA_CUDA=ON \
    -DCMAKE_CUDA_ARCHITECTURES=86 \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_NATIVE=OFF \
    -DLLAMA_F16C=OFF

# Note: Architecture 86 is for A40. Adjust if needed:
# 70 = V100, 75 = T4, 80 = A100, 86 = A40, 89 = RTX 4090

# 5. Build
echo
echo "5. Building with $(nproc) cores:"
make -j$(nproc)

# 6. Verify CUDA support
echo
echo "6. Verifying CUDA support:"
if ldd bin/main | grep -q "libcuda"; then
    echo "✅ CUDA libraries linked!"
else
    echo "⚠️  CUDA libraries not found in binary"
fi

# 7. Test GPU detection
echo
echo "7. Testing GPU detection:"
./bin/main --help 2>&1 | grep -A5 -i "gpu\|cuda" || echo "No GPU options found in help"

# 8. Quick inference test
echo
echo "8. Quick GPU inference test:"
if [ -f "/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf" ]; then
    time ./bin/main \
        -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
        -p "What is 2+2?" \
        -n 20 \
        -ngl 999 \
        --n-gpu-layers 999 \
        -t 8
else
    echo "Model not found, skipping inference test"
fi

# 9. Create optimized wrapper
echo
echo "9. Creating optimized wrapper script:"
cat > /moneyball/llama_gpu_cmake.sh << 'EOF'
#!/bin/bash
# GPU inference with CMake-built llama.cpp
exec /moneyball/llama.cpp/build/bin/main \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -ngl 999 \
    --n-gpu-layers 999 \
    -t 8 \
    -c 4096 \
    --temp 0.7 \
    --top-p 0.9 \
    --repeat-penalty 1.1 \
    -n 500 \
    -p "$*"
EOF
chmod +x /moneyball/llama_gpu_cmake.sh

# 10. Create server wrapper
echo
echo "10. Creating server mode wrapper:"
cat > /moneyball/llama_server_gpu.sh << 'EOF'
#!/bin/bash
# Run llama.cpp in server mode with GPU
exec /moneyball/llama.cpp/build/bin/server \
    -m /moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf \
    -ngl 999 \
    --n-gpu-layers 999 \
    -t 8 \
    -c 4096 \
    --host 0.0.0.0 \
    --port 8080
EOF
chmod +x /moneyball/llama_server_gpu.sh

echo
echo "=== CMAKE BUILD COMPLETE ===="
echo "✅ llama.cpp built with CMake and CUDA support"
echo
echo "Usage:"
echo "  Direct: /moneyball/llama_gpu_cmake.sh 'your prompt'"
echo "  Server: /moneyball/llama_server_gpu.sh"
echo "         Then: curl http://localhost:8080/completion -d '{\"prompt\":\"Hello\"}'"
echo
echo "If this works fast, you've solved the GPU compute issue!"