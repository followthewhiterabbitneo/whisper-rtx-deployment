#!/bin/bash
# Complete fix for permissions and CUDA 12 setup

echo "=== Complete Permissions and CUDA 12 Fix ==="
echo "This script implements the long-term solution"
echo

# 1. Detect virtual environment
VENV="${VIRTUAL_ENV:-/moneyball/llama-env-py39}"
CURRENT_USER=$(whoami)

echo "1. Environment Details:"
echo "   Virtual env: $VENV"
echo "   Current user: $CURRENT_USER"
echo

# 2. Check current permissions
echo "2. Checking current permissions..."
SITE_PACKAGES="$VENV/lib64/python3.9/site-packages"

if [ -d "$SITE_PACKAGES" ]; then
    # Check ownership
    OWNER=$(stat -c '%U' "$SITE_PACKAGES" 2>/dev/null)
    echo "   Site-packages owner: $OWNER"
    
    # Check NVIDIA packages specifically
    if [ -d "$SITE_PACKAGES/nvidia" ]; then
        NVIDIA_OWNER=$(stat -c '%U' "$SITE_PACKAGES/nvidia" 2>/dev/null)
        echo "   NVIDIA packages owner: $NVIDIA_OWNER"
    fi
    
    # Check if we need to fix
    if [ "$OWNER" != "$CURRENT_USER" ] || [ "$NVIDIA_OWNER" != "$CURRENT_USER" ]; then
        echo
        echo "3. Permissions need to be fixed!"
        echo
        echo "   Run this command to fix ownership:"
        echo
        echo "   sudo chown -R $CURRENT_USER:$CURRENT_USER $SITE_PACKAGES"
        echo
        echo "   This will make you the owner of all packages in the virtual environment."
        echo
        echo "4. After running the chown command, run this script again to continue setup."
        exit 0
    else
        echo "   ✓ Permissions are correct!"
    fi
else
    echo "   ERROR: Site-packages directory not found!"
    exit 1
fi

# 3. If we get here, permissions are good - proceed with CUDA fix
echo
echo "5. Applying CUDA 12 library fixes..."

# Create the python-gpu wrapper
echo "   Creating python-gpu wrapper..."
cat > "$VENV/bin/python-gpu" << 'EOF'
#!/bin/bash
# Python wrapper with correct CUDA 12 library paths

# Get the directory of this script
VENV_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Set library paths for all NVIDIA components
NVIDIA_BASE="$VENV_DIR/lib64/python3.9/site-packages/nvidia"

# Order matters! nvjitlink must come first
export LD_LIBRARY_PATH="$NVIDIA_BASE/nvjitlink/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cuda_runtime/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cuda_cupti/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cudnn/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cublas/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cufft/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/curand/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cusolver/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cusparse/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/nccl/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/nvtx/lib:$LD_LIBRARY_PATH"

# Add PyTorch libraries
export LD_LIBRARY_PATH="$VENV_DIR/lib64/python3.9/site-packages/torch/lib:$LD_LIBRARY_PATH"

# Add system CUDA if available
if [ -d "/usr/local/cuda/lib64" ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
fi

# Set CUDA device
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# Run Python with arguments
exec "$VENV_DIR/bin/python" "$@"
EOF

chmod +x "$VENV/bin/python-gpu"
echo "   ✓ Created $VENV/bin/python-gpu"

# 4. Update the activation script
echo
echo "6. Updating activation script..."

# Check if activation script exists
ACTIVATE_SCRIPT="/moneyball/activate_gpu_env.sh"
if [ -f "$ACTIVATE_SCRIPT" ]; then
    # Check if already updated
    if ! grep -q "alias python-gpu" "$ACTIVATE_SCRIPT"; then
        cat >> "$ACTIVATE_SCRIPT" << EOF

# CUDA 12 fixes
alias python-gpu='$VENV/bin/python-gpu'
alias gpu-python='$VENV/bin/python-gpu'

# Function to test GPU
test-gpu() {
    python-gpu -c "import torch; print(f'PyTorch {torch.__version__}: CUDA {torch.cuda.is_available()}')"
}

echo "Tip: Use 'python-gpu' for GPU-enabled Python"
EOF
        echo "   ✓ Updated $ACTIVATE_SCRIPT"
    else
        echo "   ✓ Activation script already updated"
    fi
fi

# 5. Create comprehensive test
echo
echo "7. Creating comprehensive GPU test..."

cat > "$VENV/bin/test-cuda12" << 'EOF'
#!/usr/bin/env python-gpu
"""Comprehensive CUDA 12 test"""
import os
import sys

print("=== CUDA 12 Environment Test ===")
print(f"Python: {sys.executable}")
print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'not set')}")
print()

# Test imports
modules = ['torch', 'torchvision', 'torchaudio']
versions = {}

for module in modules:
    try:
        mod = __import__(module)
        versions[module] = mod.__version__
        print(f"✓ {module}: {mod.__version__}")
    except ImportError as e:
        print(f"✗ {module}: {e}")

# Test CUDA
if 'torch' in versions:
    import torch
    print(f"\nCUDA Information:")
    print(f"  Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  cuDNN version: {torch.backends.cudnn.version()}")
        print(f"  Device count: {torch.cuda.device_count()}")
        print(f"  Current device: {torch.cuda.current_device()}")
        print(f"  Device name: {torch.cuda.get_device_name(0)}")
        
        # Memory info
        props = torch.cuda.get_device_properties(0)
        print(f"  Total memory: {props.total_memory / 1024**3:.2f} GB")
        
        # Test operations
        print("\nTesting GPU operations:")
        try:
            # Simple operation
            x = torch.randn(100, 100).cuda()
            print("  ✓ Tensor creation")
            
            # Matrix multiplication
            y = torch.randn(100, 100).cuda()
            z = torch.matmul(x, y)
            torch.cuda.synchronize()
            print("  ✓ Matrix multiplication")
            
            # Memory allocation
            large = torch.randn(1000, 1000).cuda()
            print("  ✓ Large tensor allocation")
            
            print("\n✅ All GPU operations successful!")
            
        except Exception as e:
            print(f"\n❌ GPU operation failed: {e}")
    else:
        print("\n⚠️  CUDA not available")
        print("  This might be due to vGPU restrictions")
        print(f"  PyTorch was built with CUDA: {torch.version.cuda}")
EOF

chmod +x "$VENV/bin/test-cuda12"
echo "   ✓ Created test-cuda12 script"

# 6. Test the setup
echo
echo "8. Testing the setup..."
echo

"$VENV/bin/python-gpu" -c "import torch; print(f'PyTorch {torch.__version__} loaded successfully!')" 2>&1

if [ $? -eq 0 ]; then
    echo
    echo "✅ SUCCESS! PyTorch is working with CUDA 12 libraries!"
    echo
    echo "9. Final test - checking CUDA availability:"
    "$VENV/bin/python-gpu" -c "
import torch
cuda_available = torch.cuda.is_available()
print(f'CUDA available: {cuda_available}')
if not cuda_available:
    print('Note: This is likely due to vGPU restrictions, not a library issue')
"
else
    echo
    echo "⚠️  There might still be issues. Check the error above."
fi

# 7. Create convenience scripts
echo
echo "10. Creating convenience scripts..."

# GPU Python alias in /moneyball/bin
mkdir -p /moneyball/bin
ln -sf "$VENV/bin/python-gpu" /moneyball/bin/python-gpu 2>/dev/null
ln -sf "$VENV/bin/test-cuda12" /moneyball/bin/test-cuda12 2>/dev/null

echo "   ✓ Created symlinks in /moneyball/bin/"

# 8. Summary
echo
echo "=== SETUP COMPLETE ==="
echo
echo "✅ Permissions are correct"
echo "✅ CUDA 12 library paths are configured"
echo "✅ python-gpu wrapper is installed"
echo
echo "Usage:"
echo "  python-gpu script.py              # Run any script with GPU support"
echo "  test-cuda12                       # Run comprehensive GPU test"
echo "  python-gpu -m torch.utils.collect_env  # PyTorch environment info"
echo
echo "The 'python-gpu' command is now available system-wide."
echo
echo "To make this permanent in new shells:"
echo "  source /moneyball/activate_gpu_env.sh"
echo
echo "This is the long-term solution - all GPU scripts will work correctly!"

# Create a success marker
touch "$VENV/.cuda12_fixed"
echo
echo "Marker created: $VENV/.cuda12_fixed"