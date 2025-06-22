#!/bin/bash
# Setup CUDA environment variables and check symlinks

echo "=== CUDA ENVIRONMENT SETUP ==="
echo "Detecting CUDA installation and fixing environment variables"
echo

# 1. Find CUDA installation
echo "1. Looking for CUDA installations:"
CUDA_PATHS=(
    "/usr/local/cuda"
    "/usr/local/cuda-*"
    "/opt/cuda"
    "/usr/lib/cuda"
    "/usr/share/cuda"
)

CUDA_HOME=""
for path in ${CUDA_PATHS[@]}; do
    for cuda_dir in $path; do
        if [ -d "$cuda_dir" ]; then
            echo "Found: $cuda_dir"
            if [ -z "$CUDA_HOME" ]; then
                # Check if it's a symlink
                if [ -L "$cuda_dir" ]; then
                    REAL_PATH=$(readlink -f "$cuda_dir")
                    echo "  -> Symlink to: $REAL_PATH"
                    CUDA_HOME="$REAL_PATH"
                else
                    CUDA_HOME="$cuda_dir"
                fi
            fi
        fi
    done
done

if [ -z "$CUDA_HOME" ]; then
    echo "❌ No CUDA installation found!"
    echo
    echo "2. Checking for NVIDIA libraries:"
    find /usr -name "libcuda.so*" 2>/dev/null | head -10
    exit 1
fi

echo
echo "2. Selected CUDA_HOME: $CUDA_HOME"

# 2. Check CUDA version
if [ -f "$CUDA_HOME/version.txt" ]; then
    echo "CUDA Version: $(cat $CUDA_HOME/version.txt)"
elif [ -f "$CUDA_HOME/version.json" ]; then
    echo "CUDA Version: $(cat $CUDA_HOME/version.json | grep version)"
fi

# 3. Verify CUDA binaries
echo
echo "3. Checking CUDA binaries:"
CUDA_BINARIES=("nvcc" "nvidia-smi" "deviceQuery")
for bin in ${CUDA_BINARIES[@]}; do
    if [ -f "$CUDA_HOME/bin/$bin" ]; then
        echo "✓ Found: $CUDA_HOME/bin/$bin"
    else
        which_path=$(which $bin 2>/dev/null)
        if [ -n "$which_path" ]; then
            echo "✓ Found in PATH: $which_path"
        else
            echo "✗ Missing: $bin"
        fi
    fi
done

# 4. Check libraries
echo
echo "4. Checking CUDA libraries:"
if [ -d "$CUDA_HOME/lib64" ]; then
    LIB_PATH="$CUDA_HOME/lib64"
elif [ -d "$CUDA_HOME/lib" ]; then
    LIB_PATH="$CUDA_HOME/lib"
else
    LIB_PATH=""
fi

if [ -n "$LIB_PATH" ]; then
    echo "Library path: $LIB_PATH"
    ls -la $LIB_PATH/libcudart.so* 2>/dev/null | head -3
    ls -la $LIB_PATH/libcublas.so* 2>/dev/null | head -3
fi

# 5. Check system CUDA libraries
echo
echo "5. System CUDA libraries:"
ldconfig -p | grep cuda | head -10

# 6. Create environment setup script
echo
echo "6. Creating CUDA environment setup script..."

cat > /moneyball/setup_cuda_env.sh << EOF
#!/bin/bash
# CUDA Environment Setup
# Generated on $(date)

# Set CUDA paths
export CUDA_HOME="$CUDA_HOME"
export CUDA_PATH="$CUDA_HOME"
export PATH="\$CUDA_HOME/bin:\$PATH"

# Set library paths
if [ -d "\$CUDA_HOME/lib64" ]; then
    export LD_LIBRARY_PATH="\$CUDA_HOME/lib64:\$LD_LIBRARY_PATH"
elif [ -d "\$CUDA_HOME/lib" ]; then
    export LD_LIBRARY_PATH="\$CUDA_HOME/lib:\$LD_LIBRARY_PATH"
fi

# Add system NVIDIA libraries
export LD_LIBRARY_PATH="/usr/lib64/nvidia:/usr/lib/nvidia:\$LD_LIBRARY_PATH"

# Make all GPUs visible (change if you want to limit)
export CUDA_VISIBLE_DEVICES="0"

# Optional: Set compute mode
# export CUDA_LAUNCH_BLOCKING=1  # For debugging

echo "CUDA environment set:"
echo "  CUDA_HOME: \$CUDA_HOME"
echo "  CUDA_PATH: \$CUDA_PATH"
echo "  CUDA_VISIBLE_DEVICES: \$CUDA_VISIBLE_DEVICES"
echo "  LD_LIBRARY_PATH: \$LD_LIBRARY_PATH"

# Test CUDA
if command -v nvcc &> /dev/null; then
    echo "  nvcc: \$(nvcc --version | grep release)"
fi
EOF

chmod +x /moneyball/setup_cuda_env.sh

# 7. Create test script
cat > /moneyball/test_cuda_with_env.py << 'PYTEST'
#!/usr/bin/env python3
"""Test CUDA with proper environment"""
import os
import subprocess
import sys

print("=== CUDA ENVIRONMENT TEST ===")
print()

# Show environment
print("Environment variables:")
for var in ["CUDA_HOME", "CUDA_PATH", "CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH"]:
    print(f"  {var}: {os.environ.get(var, 'NOT SET')}")

print()

# Test PyTorch
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        
        # Try operation
        try:
            x = torch.randn(10, 10).cuda()
            print("✓ GPU tensor creation successful")
        except Exception as e:
            print(f"✗ GPU operation failed: {e}")
    else:
        # Try to get more info
        print("\nChecking why CUDA not available...")
        if hasattr(torch.cuda, "_initialized"):
            print(f"CUDA initialized: {torch.cuda._initialized}")
        
        # Force initialization
        try:
            torch.cuda.init()
            print("Forced CUDA init")
        except Exception as e:
            print(f"CUDA init error: {e}")
            
except ImportError:
    print("PyTorch not installed")
except Exception as e:
    print(f"Error: {e}")

# Test with ctypes
print("\nTesting CUDA library loading with ctypes:")
import ctypes
cuda_libs = [
    "libcuda.so",
    "libcuda.so.1",
    "/usr/lib64/libcuda.so",
    "/usr/lib64/nvidia/libcuda.so"
]

for lib in cuda_libs:
    try:
        ctypes.CDLL(lib)
        print(f"✓ Loaded: {lib}")
        break
    except Exception as e:
        print(f"✗ Failed to load {lib}: {e}")
PYTEST

chmod +x /moneyball/test_cuda_with_env.py

# 8. Create activation helper
cat > /moneyball/activate_cuda.sh << 'ACTIVATE'
#!/bin/bash
# Quick CUDA activation

# Source the environment
source /moneyball/setup_cuda_env.sh

# Activate Python environment
if [ -d "/moneyball/llama-env-py39" ]; then
    source /moneyball/llama-env-py39/bin/activate
    echo "Python environment activated"
fi

# Quick test
echo
echo "Quick GPU test:"
python -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "PyTorch test failed"

echo
echo "To test: python /moneyball/test_cuda_with_env.py"
echo "To run GPU benchmark: python /moneyball/whisper-rtx-deployment/standalone_gpu_test.py"
ACTIVATE

chmod +x /moneyball/activate_cuda.sh

# 9. Summary
echo
echo "=== SETUP COMPLETE ==="
echo
echo "Files created:"
echo "  /moneyball/setup_cuda_env.sh    - Environment variables"
echo "  /moneyball/test_cuda_with_env.py - Test script"
echo "  /moneyball/activate_cuda.sh      - Quick activation"
echo
echo "To use:"
echo "  1. source /moneyball/setup_cuda_env.sh"
echo "  2. python /moneyball/test_cuda_with_env.py"
echo
echo "Or simply run:"
echo "  /moneyball/activate_cuda.sh"
echo
echo "This will set CUDA_HOME, CUDA_PATH, CUDA_VISIBLE_DEVICES, and LD_LIBRARY_PATH"