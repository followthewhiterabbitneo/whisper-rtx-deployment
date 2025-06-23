#!/bin/bash
# Fix nvcc GPU architecture warnings

echo "=== FIXING NVCC GPU ARCHITECTURE WARNINGS ==="
echo "Warning: nvcc cannot find GPU architecture"
echo

# 1. Check GPU compute capability
echo "1. Detecting GPU compute capability..."
nvidia-smi --query-gpu=name,compute_cap --format=csv
GPU_ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader,nounits | head -1 | tr -d '.')
echo "GPU architecture code: $GPU_ARCH"

# 2. Check nvcc supported architectures
echo
echo "2. NVCC supported architectures:"
nvcc --help | grep -A 20 "gpu-architecture" | head -20

# 3. Build with specific architecture
echo
echo "3. Creating fixed build script..."
cat > /moneyball/build_llama_cuda_arch.sh << EOF
#!/bin/bash
# Build llama.cpp with specific GPU architecture

echo "=== BUILDING WITH SPECIFIC GPU ARCHITECTURE ==="

# Set CUDA environment
export CUDA_HOME=/usr/local/cuda
export PATH=\$CUDA_HOME/bin:\$PATH
export LD_LIBRARY_PATH=\$CUDA_HOME/lib64:\$LD_LIBRARY_PATH

# Your GPU architecture (from detection above)
GPU_ARCH=${GPU_ARCH:-75}  # Default to 75 if not detected

cd /moneyball
rm -rf llama-cuda-arch
git clone https://github.com/ggerganov/llama.cpp llama-cuda-arch
cd llama-cuda-arch
git checkout b3447

echo "Building for GPU architecture: sm_\$GPU_ARCH"

# Build with specific architecture to avoid warnings
make clean
LLAMA_CUDA=1 CUDA_DOCKER_ARCH=sm_\$GPU_ARCH make -j4 2>&1 | grep -v "Warning" | tee build_clean.log

# Alternative: build with multiple architectures
if [ ! -f main ]; then
    echo "Trying with multiple architectures..."
    make clean
    LLAMA_CUDA=1 CUDA_DOCKER_ARCH="sm_70;sm_75;sm_80;sm_86;sm_89;sm_90" make -j4
fi

echo
echo "Build complete. Check for binary:"
ls -la main
EOF
chmod +x /moneyball/build_llama_cuda_arch.sh

# 4. Alternative: Suppress warnings
echo
echo "4. Creating build with suppressed warnings..."
cat > /moneyball/build_llama_quiet.sh << 'EOF'
#!/bin/bash
# Build with warnings suppressed

cd /moneyball/llama-cuda
make clean

# Build with warning suppression
echo "Building (warnings hidden)..."
LLAMA_CUDA=1 make -j4 2>&1 | grep -v "Warning:" | grep -v "nvcc warning" | tee build_quiet.log

# Show only important messages
echo
echo "Build summary:"
grep -E "Building|Linking|Error|CUDA|Success" build_quiet.log | tail -20

if [ -f main ]; then
    echo "✅ Build successful"
    echo "Testing CUDA support..."
    ldd main | grep cuda && echo "✅ CUDA linked" || echo "❌ No CUDA"
fi
EOF
chmod +x /moneyball/build_llama_quiet.sh

# 5. Test if it's just warnings
echo
echo "5. Quick test despite warnings..."
cat > /moneyball/test_despite_warnings.sh << 'EOF'
#!/bin/bash
# Test if GPU works despite warnings

echo "Testing GPU despite nvcc warnings..."

# Find any built binary
for bin in /moneyball/llama-cuda/main /moneyball/llama-simple/main; do
    if [ -x "$bin" ]; then
        echo "Testing: $bin"
        
        # Check if CUDA is linked
        if ldd "$bin" | grep -q cuda; then
            echo "✅ CUDA is linked - warnings might be harmless"
            
            # Quick GPU test
            nvidia-smi dmon -s u -d 1 -c 10 &
            MON=$!
            sleep 1
            
            $bin --help | grep -i gpu
            
            kill $MON 2>/dev/null
        else
            echo "❌ No CUDA linked"
        fi
        break
    fi
done
EOF
chmod +x /moneyball/test_despite_warnings.sh

echo
echo "=== SOLUTIONS ==="
echo "1. Build with specific architecture: /moneyball/build_llama_cuda_arch.sh"
echo "2. Build with suppressed warnings: /moneyball/build_llama_quiet.sh"
echo "3. Test if warnings are harmless: /moneyball/test_despite_warnings.sh"
echo
echo "The warnings might be because:"
echo "- Virtual GPU (GRID) architecture not recognized"
echo "- Mismatch between CUDA version and GPU"
echo "- Warnings might be harmless if CUDA still links"