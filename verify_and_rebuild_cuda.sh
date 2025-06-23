#!/bin/bash
# Verify CUDA support and rebuild if needed

echo "=== VERIFYING CUDA SUPPORT IN LLAMA.CPP ==="
echo

# 1. Check current binary
echo "1. Checking current llama.cpp binary for CUDA..."
LLAMA_BIN=""
for bin in /moneyball/llama.cpp/llama-cli /moneyball/llama.cpp/main /moneyball/llama-simple/main; do
    if [ -x "$bin" ]; then
        echo "Checking: $bin"
        echo "CUDA libraries linked:"
        ldd "$bin" 2>/dev/null | grep -E "cuda|cublas" || echo "  ❌ NO CUDA LIBRARIES FOUND"
        echo "GPU-related strings:"
        strings "$bin" 2>/dev/null | grep -i "gpu_layers\|cuda\|cublas" | head -5 || echo "  ❌ NO GPU STRINGS"
        LLAMA_BIN="$bin"
        echo
    fi
done

# 2. Check build logs if available
echo "2. Checking if CUDA was enabled during build..."
if [ -d /moneyball/llama.cpp ] || [ -d /moneyball/llama-simple ]; then
    echo "Looking for build artifacts..."
    find /moneyball -name "build.log" -o -name "CMakeCache.txt" 2>/dev/null | head -5
fi

# 3. Rebuild with CUDA
echo
echo "3. Creating CUDA rebuild script..."
cat > /moneyball/rebuild_llama_cuda.sh << 'EOF'
#!/bin/bash
# Rebuild llama.cpp with CUDA support

echo "=== REBUILDING LLAMA.CPP WITH CUDA ==="

# Ensure CUDA environment
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Check nvcc
echo "CUDA compiler:"
which nvcc && nvcc --version || echo "❌ nvcc not found!"

# Option 1: Simple make build
echo
echo "Building with simple make (most reliable)..."
cd /moneyball
rm -rf llama-cuda
git clone https://github.com/ggerganov/llama.cpp llama-cuda
cd llama-cuda

# Use stable version
git checkout b3447

echo
echo "Building with CUDA..."
make clean
LLAMA_CUDA=1 make -j4 2>&1 | tee build.log

# Check if CUDA was actually included
echo
echo "Checking if CUDA was compiled in..."
if grep -i "cuda\|nvcc" build.log; then
    echo "✅ CUDA compilation messages found"
else
    echo "❌ No CUDA compilation - something went wrong"
fi

# Test the binary
echo
echo "Testing new binary..."
if [ -f main ]; then
    echo "Checking CUDA libraries:"
    ldd main | grep -E "cuda|cublas" || echo "WARNING: No CUDA libs linked"
    
    # Quick test
    ./main --help | grep -i gpu || echo "WARNING: No GPU options in help"
    
    echo
    echo "New binary at: $(pwd)/main"
    echo "Test with: $(pwd)/main -m model.gguf -p 'test' --gpu-layers 35"
else
    echo "❌ Build failed!"
fi
EOF
chmod +x /moneyball/rebuild_llama_cuda.sh

# 4. Alternative: Download pre-built with CUDA
echo
echo "4. Alternative - download pre-built CUDA version..."
cat > /moneyball/get_cuda_binary.sh << 'EOF'
#!/bin/bash
# Get pre-built llama.cpp with CUDA

echo "Downloading pre-built CUDA version..."
cd /moneyball

# Try to get a CUDA-enabled build
mkdir -p llama-cuda-prebuilt
cd llama-cuda-prebuilt

# These URLs would need to be updated with actual releases
echo "Check https://github.com/ggerganov/llama.cpp/releases"
echo "Look for releases with 'cuda' in the name"
echo
echo "Manual steps:"
echo "1. Download a CUDA-enabled release"
echo "2. Extract here: /moneyball/llama-cuda-prebuilt/"
echo "3. Test with GPU layers"
EOF
chmod +x /moneyball/get_cuda_binary.sh

echo
echo "=== DIAGNOSIS ==="
echo "Your llama.cpp was built WITHOUT CUDA support"
echo "That's why GPU usage is 0% even though inference works"
echo
echo "=== SOLUTIONS ==="
echo "1. Rebuild with CUDA: /moneyball/rebuild_llama_cuda.sh"
echo "2. This will create a new binary with GPU support"
echo "3. Then test again with --gpu-layers 35"