#!/bin/bash
# Test if python-gpu wrapper fixes the library issue

echo "=== Testing python-gpu Wrapper ==="
echo

# 1. Test regular python (should fail)
echo "1. Testing regular python (expect failure):"
python -c "import torch; print('Regular python works!')" 2>&1 | head -5
echo

# 2. Test python-gpu wrapper (should work)
echo "2. Testing python-gpu wrapper:"
python-gpu -c "import torch; print(f'✓ PyTorch {torch.__version__} loaded successfully!')" 2>&1

if [ $? -eq 0 ]; then
    echo
    echo "✅ SUCCESS! The python-gpu wrapper fixes the library issue!"
    echo
    
    # Do more tests
    echo "3. Testing CUDA availability:"
    python-gpu -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
else:
    print('Note: vGPU may still block CUDA access')
"
else
    echo
    echo "❌ The wrapper didn't fix it. Let's debug..."
    echo
    
    # Debug LD_LIBRARY_PATH
    echo "4. Checking library paths in wrapper:"
    python-gpu -c "import os; print('LD_LIBRARY_PATH:', os.environ.get('LD_LIBRARY_PATH', 'NOT SET')[:200])"
    echo
    
    # Check if the libraries exist
    echo "5. Checking if NVIDIA libraries exist:"
    VENV="/moneyball/llama-env-py39"
    NVIDIA_BASE="$VENV/lib64/python3.9/site-packages/nvidia"
    
    for lib in nvjitlink cuda_runtime cudnn; do
        if [ -d "$NVIDIA_BASE/$lib/lib" ]; then
            echo "✓ Found: $NVIDIA_BASE/$lib/lib"
            ls -la "$NVIDIA_BASE/$lib/lib/lib*.so*" 2>/dev/null | head -2
        else
            echo "✗ Missing: $NVIDIA_BASE/$lib/lib"
        fi
    done
    
    echo
    echo "6. The library issue persists. Options:"
    echo "   a) Downgrade to CUDA 11.8 (more stable)"
    echo "   b) Try the alternative fix below"
fi

# Create alternative fix
echo
echo "=== Creating Alternative Fix ==="

cat > /moneyball/fix_cuda12_alt.sh << 'EOF'
#!/bin/bash
# Alternative CUDA 12 fix using LD_PRELOAD

VENV="${VIRTUAL_ENV:-/moneyball/llama-env-py39}"
NVIDIA_BASE="$VENV/lib64/python3.9/site-packages/nvidia"

# Find the nvJitLink library
NVJITLINK=$(find "$NVIDIA_BASE" -name "libnvJitLink.so.12" 2>/dev/null | head -1)

if [ -z "$NVJITLINK" ]; then
    echo "ERROR: libnvJitLink.so.12 not found!"
    echo "This might mean CUDA 12 libraries weren't installed properly"
    exit 1
fi

echo "Found nvJitLink at: $NVJITLINK"

# Create alternative wrapper using LD_PRELOAD
cat > "$VENV/bin/python-cuda12" << WRAPPER
#!/bin/bash
# Alternative Python wrapper using LD_PRELOAD

export LD_PRELOAD="$NVJITLINK:\$LD_PRELOAD"

# Also set library paths
export LD_LIBRARY_PATH="$(dirname $NVJITLINK):\$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cuda_runtime/lib:\$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$NVIDIA_BASE/cudnn/lib:\$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$VENV/lib64/python3.9/site-packages/torch/lib:\$LD_LIBRARY_PATH"

exec "$VENV/bin/python" "\$@"
WRAPPER

chmod +x "$VENV/bin/python-cuda12"
echo "Created: $VENV/bin/python-cuda12"

# Test it
echo
echo "Testing alternative wrapper..."
"$VENV/bin/python-cuda12" -c "import torch; print(f'PyTorch {torch.__version__} loaded!')" 2>&1
EOF

chmod +x /moneyball/fix_cuda12_alt.sh

# Option to downgrade
cat > /moneyball/downgrade_cuda118.sh << 'EOF'
#!/bin/bash
# Downgrade to CUDA 11.8 for stability

echo "=== Downgrading to PyTorch with CUDA 11.8 ==="
echo "This is often more stable than CUDA 12"
echo

# Ensure venv is active
if [ -z "$VIRTUAL_ENV" ]; then
    source /moneyball/llama-env-py39/bin/activate
fi

# Uninstall current PyTorch
echo "1. Removing current PyTorch..."
pip uninstall -y torch torchvision torchaudio

# Clear pip cache
echo "2. Clearing pip cache..."
pip cache purge

# Install CUDA 11.8 version
echo "3. Installing PyTorch with CUDA 11.8..."
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118

# Test
echo
echo "4. Testing installation..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
"

echo
echo "Done! CUDA 11.8 is usually more stable with vGPUs."
EOF

chmod +x /moneyball/downgrade_cuda118.sh

echo
echo "=== Options Available ==="
echo
echo "1. If python-gpu works above, you're all set!"
echo
echo "2. Try alternative fix:"
echo "   /moneyball/fix_cuda12_alt.sh"
echo
echo "3. Downgrade to stable CUDA 11.8:"
echo "   /moneyball/downgrade_cuda118.sh"
echo
echo "The downgrade option is recommended if CUDA 12 continues to have issues."