#!/bin/bash
# Install PyTorch with GPU support as root while preserving venv

echo "=== PyTorch GPU Installation (Root-compatible) ==="
echo

# 1. Detect virtual environments
echo "1. Looking for Python virtual environments:"

VENVS=(
    "/moneyball/llama-env-py39"
    "/moneyball/gemma-env"
    "/moneyball/llama-env-py38"
    "/moneyball/llama-env-new"
)

SELECTED_VENV=""
for venv in "${VENVS[@]}"; do
    if [ -d "$venv" ] && [ -f "$venv/bin/python" ]; then
        echo "Found: $venv"
        PYTHON_VERSION=$($venv/bin/python --version 2>&1)
        echo "  Python: $PYTHON_VERSION"
        
        if [ -z "$SELECTED_VENV" ]; then
            SELECTED_VENV="$venv"
        fi
    fi
done

if [ -z "$SELECTED_VENV" ]; then
    echo "❌ No virtual environment found!"
    exit 1
fi

echo
echo "2. Using virtual environment: $SELECTED_VENV"

# Set paths
VENV_PYTHON="$SELECTED_VENV/bin/python"
VENV_PIP="$SELECTED_VENV/bin/pip"

# 2. Check if we need root
echo
echo "3. Checking permissions:"

# Test if we can write to site-packages
SITE_PACKAGES=$($VENV_PYTHON -c "import site; print(site.getsitepackages()[0])")
if [ -w "$SITE_PACKAGES" ]; then
    echo "✓ Can write to $SITE_PACKAGES"
    USE_SUDO=""
else
    echo "⚠️  Need elevated permissions for $SITE_PACKAGES"
    USE_SUDO="sudo -E"
    
    # Check if we're already root
    if [ "$EUID" -eq 0 ]; then
        echo "✓ Already running as root"
        USE_SUDO=""
    fi
fi

# 3. Check current PyTorch
echo
echo "4. Current PyTorch status:"
$VENV_PYTHON -c "import torch; print(f'Version: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "PyTorch not installed"

# 4. Detect CUDA version
echo
echo "5. Detecting CUDA version:"
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/p')
    echo "CUDA version: $CUDA_VERSION"
else
    echo "nvcc not found, checking nvidia-smi..."
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | sed -n 's/.*CUDA Version: \([0-9]\+\.[0-9]\+\).*/\1/p')
    echo "CUDA version from nvidia-smi: $CUDA_VERSION"
fi

# 5. Determine PyTorch version
echo
echo "6. Selecting PyTorch version:"

if [[ "$CUDA_VERSION" == "12"* ]]; then
    echo "CUDA 12.x detected - using PyTorch with CUDA 12.1"
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    CUDA_TAG="cu121"
elif [[ "$CUDA_VERSION" == "11.8"* ]]; then
    echo "CUDA 11.8 detected"
    TORCH_INDEX="https://download.pytorch.org/whl/cu118"
    CUDA_TAG="cu118"
elif [[ "$CUDA_VERSION" == "11.7"* ]]; then
    echo "CUDA 11.7 detected"
    TORCH_INDEX="https://download.pytorch.org/whl/cu117"
    CUDA_TAG="cu117"
else
    echo "Unknown CUDA version, defaulting to CUDA 11.8"
    TORCH_INDEX="https://download.pytorch.org/whl/cu118"
    CUDA_TAG="cu118"
fi

# 6. Create installation script
INSTALL_SCRIPT="/tmp/pytorch_install_$$.sh"
cat > "$INSTALL_SCRIPT" << EOF
#!/bin/bash
# Temporary installation script

# Remove existing PyTorch
echo "Removing existing PyTorch..."
$VENV_PIP uninstall -y torch torchvision torchaudio 2>/dev/null || true

# Install PyTorch with CUDA
echo "Installing PyTorch with CUDA support..."
$VENV_PIP install --no-cache-dir torch torchvision torchaudio --index-url $TORCH_INDEX

# Verify
echo
echo "Verifying installation:"
$VENV_PYTHON -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
EOF

chmod +x "$INSTALL_SCRIPT"

# 7. Run installation
echo
echo "7. Running installation..."

if [ -n "$USE_SUDO" ]; then
    echo "Running with sudo..."
    sudo bash "$INSTALL_SCRIPT"
else
    bash "$INSTALL_SCRIPT"
fi

# Clean up
rm -f "$INSTALL_SCRIPT"

# 8. Final verification
echo
echo "8. Final verification:"

cat > /tmp/test_pytorch_$$.py << 'EOF'
import torch
import sys

print(f"Python: {sys.executable}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    try:
        x = torch.randn(10, 10).cuda()
        print("✓ GPU tensor creation successful")
    except Exception as e:
        print(f"✗ GPU operation failed: {e}")
else:
    print("CUDA not available")
    if torch.version.cuda:
        print(f"PyTorch built with CUDA {torch.version.cuda}")
        print("But runtime CUDA not accessible (vGPU issue?)")
    else:
        print("⚠️  This is a CPU-only build!")
EOF

$VENV_PYTHON /tmp/test_pytorch_$$.py
rm -f /tmp/test_pytorch_$$.py

# 9. Create wrapper script
cat > /moneyball/run_with_gpu.sh << EOF
#!/bin/bash
# Run Python with GPU environment

# Set CUDA environment
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
export PATH="\$CUDA_HOME/bin:\$PATH"
export LD_LIBRARY_PATH="\$CUDA_HOME/lib64:/usr/lib64/nvidia:\$LD_LIBRARY_PATH"
export CUDA_VISIBLE_DEVICES="0"

# Use the virtual environment
$VENV_PYTHON "\$@"
EOF

chmod +x /moneyball/run_with_gpu.sh

echo
echo "=== INSTALLATION COMPLETE ==="
echo
echo "To run Python scripts with GPU support:"
echo "  /moneyball/run_with_gpu.sh your_script.py"
echo
echo "Or activate environment manually:"
echo "  source $SELECTED_VENV/bin/activate"
echo "  export CUDA_VISIBLE_DEVICES=0"
echo "  python your_script.py"
echo
echo "Virtual environment: $SELECTED_VENV"
echo "Python executable: $VENV_PYTHON"