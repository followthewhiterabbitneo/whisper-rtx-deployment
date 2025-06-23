#!/bin/bash
# Fix llama.cpp CUDA build on RHEL8

echo "=== FIXING LLAMA.CPP CUDA BUILD ==="
echo

# Check CUDA installation
echo "1. Checking CUDA setup..."
which nvcc || echo "❌ nvcc not found in PATH"
ls -la /usr/local/cuda/bin/nvcc || echo "❌ CUDA not at /usr/local/cuda"

# Set up CUDA paths explicitly
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

echo
echo "2. CUDA paths set:"
echo "CUDA_HOME=$CUDA_HOME"
echo "nvcc location: $(which nvcc)"

cd /moneyball/llama-simple || exit 1

# Clean previous build
echo
echo "3. Cleaning previous build..."
make clean

# Build with explicit CUDA flags
echo
echo "4. Building with CUDA (watching for CUDA messages)..."
LLAMA_CUDA=1 CUDA_PATH=$CUDA_HOME make -j4 2>&1 | tee build.log

# Check if CUDA was actually included
echo
echo "5. Checking if CUDA was included in build..."
grep -i "cuda\|nvcc\|gpu" build.log || echo "❌ No CUDA messages in build log!"

# Check the binary
echo
echo "6. Checking binary for CUDA support..."
if [ -f "llama-cli" ]; then
    echo "Using llama-cli (new name):"
    ./llama-cli --help 2>&1 | grep -i "gpu\|cuda" || echo "❌ No GPU options in help"
    ldd ./llama-cli | grep cuda || echo "❌ No CUDA libraries linked"
elif [ -f "main" ]; then
    echo "Using main (deprecated):"
    ./main --help 2>&1 | grep -i "gpu\|cuda" || echo "❌ No GPU options in help"
    ldd ./main | grep cuda || echo "❌ No CUDA libraries linked"
fi

# Alternative: Try even older version
echo
echo "7. If CUDA still not working, try older version..."
cat > /moneyball/build_old_cuda.sh << 'EOF'
#!/bin/bash
cd /moneyball
rm -rf llama-old
git clone https://github.com/ggerganov/llama.cpp llama-old
cd llama-old
git checkout b2430  # Even older version
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
LLAMA_CUDA=1 CUDA_PATH=$CUDA_HOME make -j4
echo "Binary at: $(pwd)/main"
EOF
chmod +x /moneyball/build_old_cuda.sh

# Create diagnostic script
echo
echo "8. Creating diagnostic script..."
cat > /moneyball/diagnose_cuda.sh << 'EOF'
#!/bin/bash
echo "=== CUDA DIAGNOSIS ==="
echo "1. CUDA compiler:"
nvcc --version

echo
echo "2. CUDA libraries:"
ldconfig -p | grep cuda

echo
echo "3. GPU info:"
nvidia-smi -L

echo
echo "4. Test PyTorch CUDA (comparison):"
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"

echo
echo "5. All llama binaries:"
find /moneyball -name "main" -o -name "llama-cli" 2>/dev/null | while read bin; do
    echo "Checking: $bin"
    ldd "$bin" 2>/dev/null | grep -q cuda && echo "  ✅ Has CUDA" || echo "  ❌ No CUDA"
done
EOF
chmod +x /moneyball/diagnose_cuda.sh

echo
echo "=== NEXT STEPS ==="
echo "1. Run diagnostics: /moneyball/diagnose_cuda.sh"
echo "2. If no CUDA in current build, try: /moneyball/build_old_cuda.sh"
echo "3. Or go back to Ollama: ollama serve && ollama run llama3"