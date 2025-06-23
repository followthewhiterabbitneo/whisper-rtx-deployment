#!/bin/bash
# Fix CUDA libraries the same way PyTorch does

echo "=== FIXING CUDA LIBRARIES (PyTorch METHOD) ==="
echo "The model loads in VRAM = CUDA driver works ✓"
echo "No GPU inference = CUDA runtime missing ✗"
echo

# 1. Check what PyTorch installed
echo "1. Checking PyTorch CUDA setup..."
python3 -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA version: {torch.version.cuda}')"

# 2. Find PyTorch's CUDA libraries
echo
echo "2. Finding PyTorch CUDA libraries..."
TORCH_PATH=$(python3 -c "import torch; import os; print(os.path.dirname(torch.__file__))")
echo "PyTorch path: $TORCH_PATH"
find $TORCH_PATH -name "libcudart.so*" -o -name "libcublas.so*" 2>/dev/null | head -10

# 3. Check current library paths
echo
echo "3. Current LD_LIBRARY_PATH:"
echo $LD_LIBRARY_PATH | tr ':' '\n'

# 4. Create fix script using PyTorch's libraries
echo
echo "4. Creating fix script..."
cat > /moneyball/fix_ollama_with_torch_cuda.sh << EOF
#!/bin/bash
# Use PyTorch's CUDA libraries for Ollama

# Find PyTorch lib path
TORCH_LIB=\$(python3 -c "import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), 'lib'))")

# Add PyTorch's CUDA libs to path
export LD_LIBRARY_PATH=\$TORCH_LIB:/usr/local/cuda-12.0/lib64:\$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=0

echo "Using PyTorch CUDA libraries from: \$TORCH_LIB"
echo "Starting Ollama with fixed paths..."

# Kill old Ollama
pkill -f ollama

# Start with correct libraries
ollama serve &
OLLAMA_PID=\$!
echo "Started Ollama with PID: \$OLLAMA_PID"
sleep 5

# Test GPU inference
echo
echo "Testing GPU inference..."
nvidia-smi dmon -s u -d 1 -c 20 &
MONITOR=\$!
sleep 2

time ollama run llama3:8b "What is 2+2? Be brief." 

kill \$MONITOR 2>/dev/null
EOF
chmod +x /moneyball/fix_ollama_with_torch_cuda.sh

# 5. Alternative: Install CUDA runtime directly
echo
echo "5. Alternative fix - install CUDA runtime libraries..."
cat > /moneyball/install_cuda_runtime.sh << 'EOF'
#!/bin/bash
# Install CUDA runtime libraries that match driver

echo "Installing CUDA runtime libraries..."

# Option 1: From NVIDIA repo
if command -v dnf &> /dev/null; then
    sudo dnf install -y cuda-cudart-12-0 cuda-cublas-12-0
elif command -v yum &> /dev/null; then
    sudo yum install -y cuda-cudart-12-0 cuda-cublas-12-0
fi

# Option 2: conda/mamba (if available)
if command -v conda &> /dev/null; then
    echo "Installing via conda..."
    conda install -y cudatoolkit=12.0 -c nvidia
fi

# Option 3: pip install
echo "Installing NVIDIA CUDA runtime via pip..."
pip install nvidia-cuda-runtime-cu12 nvidia-cublas-cu12
EOF
chmod +x /moneyball/install_cuda_runtime.sh

# 6. Check which CUDA Ollama is trying to use
echo
echo "6. Checking Ollama's CUDA preference..."
strings $(which ollama) 2>/dev/null | grep -i "cuda" | grep -E "\.so|v1[12]" | sort -u | head -10

echo
echo "=== SOLUTION ==="
echo "PyTorch brings its own CUDA runtime libraries that work."
echo "Ollama needs the same libraries but can't find them."
echo
echo "Fix options:"
echo "1. /moneyball/fix_ollama_with_torch_cuda.sh  # Use PyTorch's CUDA"
echo "2. /moneyball/install_cuda_runtime.sh        # Install CUDA runtime"
echo
echo "The issue: CUDA driver (kernel module) ≠ CUDA runtime (libraries)"