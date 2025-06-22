#!/bin/bash
# Fix CUDA library paths for llama.cpp on RHEL8

echo "=== FIXING CUDA PATHS FOR RHEL8 ==="
echo

# 1. Show current issue
echo "1. Current CUDA library locations:"
echo "✓ CUDA driver found at: /usr/lib64/libcuda.so"
echo "✗ llama.cpp looking at: /usr/lib/x86_64-linux-gnu/libcuda.so"
echo

# 2. Create symlinks
echo "2. Creating compatibility symlinks..."
sudo mkdir -p /usr/lib/x86_64-linux-gnu
sudo ln -sf /usr/lib64/libcuda.so /usr/lib/x86_64-linux-gnu/libcuda.so
sudo ln -sf /usr/lib64/libcuda.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so.1

# 3. Set environment variables
echo
echo "3. Setting environment variables..."
cat > /moneyball/cuda_env.sh << 'EOF'
# CUDA environment for RHEL8
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64:$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export LIBRARY_PATH=/usr/lib64:$CUDA_HOME/lib64:$LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0
EOF

# 4. Create build script with correct paths
echo
echo "4. Creating fixed CMake build script..."
cat > /moneyball/build_llama_fixed.sh << 'EOF'
#!/bin/bash
# Build llama.cpp with correct CUDA paths for RHEL8

source /moneyball/cuda_env.sh

cd /moneyball/llama.cpp || exit 1

# Clean build
rm -rf build
mkdir build && cd build

# Configure with explicit CUDA paths
echo "Configuring with RHEL8 CUDA paths..."
cmake3 .. \
    -DLLAMA_CUDA=ON \
    -DCMAKE_CUDA_ARCHITECTURES=89 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
    -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
    -DCUDA_cudart_LIBRARY=/usr/local/cuda/lib64/libcudart.so \
    -DCUDA_cuda_LIBRARY=/usr/lib64/libcuda.so

# Build
echo "Building..."
make -j$(nproc)

# Test
if [ -f bin/main ]; then
    echo "Build successful! Testing..."
    ./bin/main --version
    ln -sf $(pwd)/bin/main /moneyball/llama.cpp/main
fi
EOF
chmod +x /moneyball/build_llama_fixed.sh

# 5. Alternative: Use LD_PRELOAD
echo
echo "5. Creating wrapper with LD_PRELOAD..."
cat > /moneyball/llama_gpu_fixed.sh << 'EOF'
#!/bin/bash
# Run llama.cpp with correct library paths
source /moneyball/cuda_env.sh
export LD_PRELOAD=/usr/lib64/libcuda.so

MODEL="${1:-/moneyball/whisper-rtx-deployment/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf}"
shift

exec /moneyball/llama.cpp/main \
    -m "$MODEL" \
    --gpu-layers 999 \
    --threads 8 \
    "$@"
EOF
chmod +x /moneyball/llama_gpu_fixed.sh

# 6. Test CUDA
echo
echo "6. Testing CUDA access..."
ldconfig -p | grep cuda

echo
echo "=== FIXES APPLIED ==="
echo "Option 1: Build with fixed paths"
echo "  /moneyball/build_llama_fixed.sh"
echo
echo "Option 2: Run with LD_PRELOAD"
echo "  /moneyball/llama_gpu_fixed.sh 'your prompt'"
echo
echo "Option 3: Source environment first"
echo "  source /moneyball/cuda_env.sh"
echo "  ./build_llama_cpp_cmake_rhel8.sh"