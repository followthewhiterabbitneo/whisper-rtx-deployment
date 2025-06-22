#!/bin/bash
# Fix PyTorch CUDA 12 library issues

echo "=== Fixing PyTorch CUDA 12 Library Issues ==="
echo

# 1. Show the error
echo "1. Current error:"
echo "   undefined symbol: __nvJitLinkAddData_12_1"
echo "   This is a known CUDA 12 compatibility issue"
echo

# 2. Check current environment
echo "2. Checking environment:"
echo "   Virtual env: $VIRTUAL_ENV"
echo "   LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo

# 3. Find the problematic library
echo "3. Finding NVIDIA libraries:"
TORCH_LIB_PATH="$VIRTUAL_ENV/lib64/python3.9/site-packages/torch/lib"
NVIDIA_LIB_PATH="$VIRTUAL_ENV/lib64/python3.9/site-packages/nvidia"

echo "   PyTorch libs: $TORCH_LIB_PATH"
echo "   NVIDIA libs: $NVIDIA_LIB_PATH"

# List NVIDIA libraries
if [ -d "$NVIDIA_LIB_PATH" ]; then
    echo
    echo "   NVIDIA packages installed:"
    ls -1 "$NVIDIA_LIB_PATH" | head -10
fi

# 4. Fix library path order
echo
echo "4. Fixing library path order..."

# Create wrapper script that sets correct library order
cat > "$VIRTUAL_ENV/bin/python-gpu" << 'EOF'
#!/bin/bash
# Python wrapper with correct CUDA library paths

# Get the directory of this script
VENV_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Set library paths in correct order
export LD_LIBRARY_PATH="$VENV_DIR/lib64/python3.9/site-packages/nvidia/nvjitlink/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV_DIR/lib64/python3.9/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV_DIR/lib64/python3.9/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV_DIR/lib64/python3.9/site-packages/torch/lib:$LD_LIBRARY_PATH"

# Also add system CUDA if available
if [ -d "/usr/local/cuda/lib64" ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
fi

# Set CUDA device
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# Run Python with arguments
exec "$VENV_DIR/bin/python" "$@"
EOF

chmod +x "$VIRTUAL_ENV/bin/python-gpu"

# 5. Test the fix
echo
echo "5. Testing the fix..."

"$VIRTUAL_ENV/bin/python-gpu" -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>&1 | head -5

# If that worked, test CUDA
if [ $? -eq 0 ]; then
    echo
    echo "6. Testing CUDA access:"
    "$VIRTUAL_ENV/bin/python-gpu" -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'Device: {torch.cuda.get_device_name(0)}')
"
fi

# 6. Alternative fix - downgrade to CUDA 11.8
echo
echo "7. Alternative solution available:"
echo "   If the above doesn't work, we can downgrade to CUDA 11.8"
echo "   which is more stable with PyTorch."

cat > /moneyball/install_pytorch_cuda118.sh << 'ALTFIX'
#!/bin/bash
# Alternative: Install PyTorch with CUDA 11.8

echo "Installing PyTorch with CUDA 11.8 (more stable)..."

# Uninstall current version
pip uninstall -y torch torchvision torchaudio

# Clean cache
pip cache purge

# Install CUDA 11.8 version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Test
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"
ALTFIX

chmod +x /moneyball/install_pytorch_cuda118.sh

# 7. Create permanent fix
echo
echo "8. Creating permanent fix..."

# Update activation script
cat >> /moneyball/activate_gpu_env.sh << 'EOF'

# Fix for CUDA 12 library issues
if [ -d "$VIRTUAL_ENV/lib64/python3.9/site-packages/nvidia" ]; then
    export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib64/python3.9/site-packages/nvidia/nvjitlink/lib:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib64/python3.9/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
fi

# Alias for GPU Python
alias python-gpu="$VIRTUAL_ENV/bin/python-gpu"
EOF

# 8. Create test script
cat > /moneyball/test_pytorch_fixed.py << 'EOF'
#!/usr/bin/env python
"""Test PyTorch with CUDA 12 fix"""
import os
import sys

print("=== PyTorch CUDA 12 Test ===")
print(f"Python: {sys.executable}")
print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'not set')[:200]}...")
print()

try:
    import torch
    print(f"✓ PyTorch imported successfully")
    print(f"  Version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  cuDNN version: {torch.backends.cudnn.version()}")
        print(f"  Device count: {torch.cuda.device_count()}")
        print(f"  Device name: {torch.cuda.get_device_name(0)}")
        
        # Test tensor operation
        try:
            x = torch.randn(100, 100).cuda()
            y = torch.randn(100, 100).cuda()
            z = torch.matmul(x, y)
            torch.cuda.synchronize()
            print("  ✓ GPU operations working!")
        except Exception as e:
            print(f"  ✗ GPU operation failed: {e}")
    else:
        print("\n  Debugging CUDA availability...")
        print(f"  PyTorch CUDA build: {torch.version.cuda}")
        print(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')}")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nTrying to diagnose...")
    import subprocess
    result = subprocess.run(["ldd", f"{os.environ.get('VIRTUAL_ENV')}/lib64/python3.9/site-packages/torch/lib/libtorch_cuda.so"], 
                          capture_output=True, text=True)
    print("Missing libraries:")
    for line in result.stdout.split('\n'):
        if 'not found' in line:
            print(f"  {line}")
EOF

chmod +x /moneyball/test_pytorch_fixed.py

# 9. Summary
echo
echo "=== FIX APPLIED ==="
echo
echo "To use PyTorch with GPU:"
echo "1. Use the wrapper: python-gpu script.py"
echo "   Example: python-gpu /moneyball/test_pytorch_fixed.py"
echo
echo "2. Or set library paths manually:"
echo "   export LD_LIBRARY_PATH=\"\$VIRTUAL_ENV/lib64/python3.9/site-packages/nvidia/nvjitlink/lib:\$LD_LIBRARY_PATH\""
echo
echo "3. If still having issues, downgrade to CUDA 11.8:"
echo "   /moneyball/install_pytorch_cuda118.sh"
echo
echo "The wrapper 'python-gpu' sets all the correct library paths automatically."