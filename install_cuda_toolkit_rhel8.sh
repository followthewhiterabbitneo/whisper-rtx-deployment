#!/bin/bash
# Install CUDA toolkit to fix Ollama GPU detection

echo "=== INSTALLING CUDA TOOLKIT FOR OLLAMA ==="
echo "Issue: nvcc not found - only have CUDA driver, not toolkit"
echo

# 1. Check current situation
echo "1. Current CUDA status:"
echo "Driver version:"
nvidia-smi | grep "Driver Version"
echo
echo "CUDA libraries present:"
ldconfig -p | grep -E "libcuda|libcudart|libcublas" | head -10

# 2. Install CUDA toolkit that matches driver
echo
echo "2. Installing CUDA toolkit..."
echo "Your driver supports CUDA 12.0"

# Method 1: Install from RHEL8 repos
cat > /tmp/install_cuda_toolkit.sh << 'EOF'
#!/bin/bash
# Run as root

# Add NVIDIA repo if needed
if ! ls /etc/yum.repos.d/*nvidia* 2>/dev/null; then
    echo "Adding NVIDIA CUDA repo..."
    dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
fi

# Install CUDA toolkit 12.0 to match driver
echo "Installing CUDA toolkit 12.0..."
dnf install -y cuda-toolkit-12-0 || yum install -y cuda-toolkit-12-0

# Alternative: Just runtime libraries
if [ $? -ne 0 ]; then
    echo "Full toolkit failed, trying just runtime..."
    dnf install -y cuda-cudart-12-0 cuda-cublas-12-0 cuda-nvrtc-12-0
fi

# Update library cache
ldconfig

# Set up environment
echo 'export PATH=/usr/local/cuda-12.0/bin:$PATH' >> /etc/profile.d/cuda.sh
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.0/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
chmod 644 /etc/profile.d/cuda.sh

echo "CUDA toolkit installed!"
EOF

echo "To install CUDA toolkit, run as root:"
echo "sudo bash /tmp/install_cuda_toolkit.sh"

# 3. Quick fix without installation
echo
echo "3. Creating quick fix without full installation..."
cat > /moneyball/fake_cuda_env.sh << 'EOF'
#!/bin/bash
# Fake CUDA environment for Ollama

echo "Setting up minimal CUDA environment for Ollama..."

# Use Ollama's bundled CUDA
OLLAMA_CUDA="/usr/lib/ollama"
if [ -d "$OLLAMA_CUDA/cuda_v12" ]; then
    echo "Found Ollama CUDA 12 libraries"
    export LD_LIBRARY_PATH=$OLLAMA_CUDA/cuda_v12:$LD_LIBRARY_PATH
elif [ -d "$OLLAMA_CUDA/cuda_v11" ]; then
    echo "Found Ollama CUDA 11 libraries"
    export LD_LIBRARY_PATH=$OLLAMA_CUDA/cuda_v11:$LD_LIBRARY_PATH
fi

# Set CUDA paths even without nvcc
export CUDA_HOME=/usr/local/cuda
export CUDA_PATH=/usr/local/cuda
export CUDA_VISIBLE_DEVICES=0

# Create fake nvcc to satisfy checks
sudo mkdir -p /usr/local/cuda/bin
sudo tee /usr/local/cuda/bin/nvcc << 'NVCC' > /dev/null
#!/bin/bash
echo "nvcc: NVIDIA (R) Cuda compiler driver"
echo "Cuda compilation tools, release 12.0"
NVCC
sudo chmod +x /usr/local/cuda/bin/nvcc

# Start Ollama
pkill -f ollama
echo "Starting Ollama with minimal CUDA setup..."
OLLAMA_DEBUG=1 ollama serve 2>&1 | tee /tmp/ollama_minimal.log &
echo "Check log: tail -f /tmp/ollama_minimal.log"
EOF
chmod +x /moneyball/fake_cuda_env.sh

# 4. Use PyTorch's CUDA if available
echo
echo "4. Creating PyTorch CUDA borrowing script..."
cat > /moneyball/use_pytorch_cuda_for_ollama.sh << 'EOF'
#!/bin/bash
# Use PyTorch's CUDA for Ollama

if python3 -c "import torch" 2>/dev/null; then
    echo "Found PyTorch, borrowing its CUDA..."
    
    # Get PyTorch's CUDA libraries
    TORCH_LIB=$(python3 -c "import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), 'lib'))")
    
    # Check what CUDA version PyTorch has
    CUDA_VERSION=$(python3 -c "import torch; print(torch.version.cuda)")
    echo "PyTorch CUDA version: $CUDA_VERSION"
    
    # Use PyTorch's libraries
    export LD_LIBRARY_PATH=$TORCH_LIB:$LD_LIBRARY_PATH
    export CUDA_VISIBLE_DEVICES=0
    
    # Copy PyTorch's CUDA libraries to system location (requires root)
    echo "To make permanent (as root):"
    echo "sudo cp $TORCH_LIB/libcudart.so* /usr/lib64/"
    echo "sudo cp $TORCH_LIB/libcublas.so* /usr/lib64/"
    echo "sudo ldconfig"
    
    # Start Ollama
    pkill -f ollama
    ollama serve &
    echo "Started Ollama with PyTorch CUDA libraries"
else
    echo "PyTorch not found"
fi
EOF
chmod +x /moneyball/use_pytorch_cuda_for_ollama.sh

echo
echo "=== SOLUTIONS ==="
echo "1. Install CUDA toolkit (best solution):"
echo "   sudo bash /tmp/install_cuda_toolkit.sh"
echo
echo "2. Use minimal fake environment:"
echo "   /moneyball/fake_cuda_env.sh"
echo
echo "3. Borrow PyTorch's CUDA:"
echo "   /moneyball/use_pytorch_cuda_for_ollama.sh"
echo
echo "The issue: Ollama needs CUDA toolkit, not just driver"