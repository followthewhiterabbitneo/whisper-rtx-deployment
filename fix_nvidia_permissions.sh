#!/bin/bash
# Fix NVIDIA package permissions in virtual environment

echo "=== Fixing NVIDIA Package Permissions ==="
echo

# Check if we need sudo
VENV="${VIRTUAL_ENV:-/moneyball/llama-env-py39}"
NVIDIA_PATH="$VENV/lib64/python3.9/site-packages/nvidia"

echo "Checking permissions for: $NVIDIA_PATH"

# Check who owns the files
if [ -d "$NVIDIA_PATH" ]; then
    echo "Current ownership:"
    ls -ld "$NVIDIA_PATH" | head -5
    echo
    
    # Get current user
    CURRENT_USER=$(whoami)
    echo "Current user: $CURRENT_USER"
    
    # Check if we own the directory
    OWNER=$(stat -c '%U' "$NVIDIA_PATH" 2>/dev/null)
    echo "Directory owner: $OWNER"
    
    if [ "$OWNER" != "$CURRENT_USER" ]; then
        echo
        echo "Need to fix ownership. Run this command:"
        echo
        echo "sudo chown -R $CURRENT_USER:$CURRENT_USER $VENV/lib64/python3.9/site-packages/"
        echo
        echo "Or if you want to fix just NVIDIA packages:"
        echo "sudo chown -R $CURRENT_USER:$CURRENT_USER $NVIDIA_PATH"
        echo
        echo "After fixing permissions, run:"
        echo "./fix_pytorch_cuda12.sh"
    else
        echo "Permissions look correct. Try running fix_pytorch_cuda12.sh again."
    fi
else
    echo "NVIDIA packages not found at expected location"
fi

# Alternative: Create the fix without modifying files
echo
echo "=== Alternative: Set Library Path Without Modifying Files ==="
echo

cat > /moneyball/run_with_cuda12.sh << 'EOF'
#!/bin/bash
# Run Python with CUDA 12 library paths

# Get virtual environment
VENV="${VIRTUAL_ENV:-/moneyball/llama-env-py39}"

# Set all NVIDIA library paths
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/nvjitlink/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cuda_runtime/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cuda_cupti/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cufft/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/curand/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cusolver/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/cusparse/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/nccl/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/nvidia/nvtx/lib:$LD_LIBRARY_PATH"

# Also add PyTorch libs
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/torch/lib:$LD_LIBRARY_PATH"

# Set CUDA device
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

echo "CUDA 12 environment set"
echo "LD_LIBRARY_PATH configured for all NVIDIA libraries"

# If script provided, run it
if [ $# -gt 0 ]; then
    python "$@"
else
    echo
    echo "Usage: $0 script.py [args]"
    echo "Or source this script and then run python"
fi
EOF

chmod +x /moneyball/run_with_cuda12.sh

# Create a test without needing to modify files
cat > /moneyball/test_cuda12_nomod.py << 'EOF'
#!/usr/bin/env python
"""Test CUDA 12 without modifying any files"""
import os
import sys

print("Testing PyTorch CUDA 12...")
print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'not set')[:100]}...")

try:
    import torch
    print(f"✓ PyTorch loaded: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        x = torch.randn(10, 10).cuda()
        print("  ✓ GPU tensor created successfully!")
    else:
        print("  Note: CUDA not available (vGPU issue)")
        
except Exception as e:
    print(f"Error: {e}")
    
    # Try to help diagnose
    import subprocess
    print("\nChecking for missing libraries...")
    venv = os.environ.get('VIRTUAL_ENV', '/moneyball/llama-env-py39')
    lib_path = f"{venv}/lib64/python3.9/site-packages/torch/lib/libtorch_cuda.so"
    
    if os.path.exists(lib_path):
        result = subprocess.run(["ldd", lib_path], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'not found' in line:
                print(f"  Missing: {line}")
EOF

chmod +x /moneyball/test_cuda12_nomod.py

echo
echo "=== Solutions Available ==="
echo
echo "Option 1 - Fix permissions (recommended):"
echo "  sudo chown -R $(whoami):$(whoami) $VENV/lib64/python3.9/site-packages/"
echo
echo "Option 2 - Use wrapper script (no permissions needed):"
echo "  /moneyball/run_with_cuda12.sh your_script.py"
echo
echo "Option 3 - Set environment manually:"
echo "  source /moneyball/run_with_cuda12.sh"
echo "  python your_script.py"
echo
echo "Test with:"
echo "  /moneyball/run_with_cuda12.sh /moneyball/test_cuda12_nomod.py"