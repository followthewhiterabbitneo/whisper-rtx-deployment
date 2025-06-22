#!/bin/bash
# Install PyTorch with GPU support

echo "=== PyTorch GPU Installation ==="
echo "This script installs PyTorch with CUDA support"
echo

# 1. Check Python environment
echo "1. Checking Python environment:"
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment active!"
    echo "   Activate with: source /moneyball/llama-env-py39/bin/activate"
    echo "   Or: source /moneyball/gemma-env/bin/activate"
    exit 1
fi

echo "✓ Using virtual environment: $VIRTUAL_ENV"
python --version

# 2. Check current PyTorch
echo
echo "2. Current PyTorch status:"
python -c "import torch; print(f'Version: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "PyTorch not installed"

# 3. Detect CUDA version
echo
echo "3. Detecting CUDA version:"
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/p')
    echo "CUDA version: $CUDA_VERSION"
else
    echo "nvcc not found, checking nvidia-smi..."
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | sed -n 's/.*CUDA Version: \([0-9]\+\.[0-9]\+\).*/\1/p')
    echo "CUDA version from nvidia-smi: $CUDA_VERSION"
fi

# 4. Determine PyTorch version to install
echo
echo "4. Selecting PyTorch version:"

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

# 5. Uninstall CPU-only PyTorch if present
echo
echo "5. Removing existing PyTorch (if any):"
pip uninstall -y torch torchvision torchaudio 2>/dev/null || echo "No existing PyTorch"

# 6. Install PyTorch with CUDA
echo
echo "6. Installing PyTorch with CUDA support..."
echo "This may take a few minutes..."

pip install --no-cache-dir torch torchvision torchaudio --index-url $TORCH_INDEX

# 7. Verify installation
echo
echo "7. Verifying PyTorch GPU installation:"

python << 'EOF'
import sys
try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ cuDNN version: {torch.backends.cudnn.version()}")
        print(f"✓ Device count: {torch.cuda.device_count()}")
        print(f"✓ Current device: {torch.cuda.current_device()}")
        
        try:
            # Test tensor creation
            x = torch.randn(10, 10).cuda()
            print("✓ GPU tensor creation successful")
        except Exception as e:
            print(f"✗ GPU tensor creation failed: {e}")
    else:
        print("✗ CUDA not available - troubleshooting:")
        print(f"  - Torch built with CUDA: {torch.version.cuda}")
        
        # Check if this is actually a CPU build
        if torch.version.cuda is None:
            print("  ⚠️  This appears to be a CPU-only build!")
            print("  The installation may have failed.")
        
        # Try to force init
        try:
            torch.cuda.init()
        except Exception as e:
            print(f"  - CUDA init error: {e}")
            
except ImportError as e:
    print(f"✗ PyTorch import failed: {e}")
    sys.exit(1)
EOF

# 8. Create test script
cat > /moneyball/test_pytorch_gpu.py << 'TEST'
#!/usr/bin/env python3
"""Test PyTorch GPU functionality"""
import torch
import time

print("=== PyTorch GPU Test ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"\nGPU Information:")
    print(f"  Device count: {torch.cuda.device_count()}")
    print(f"  Current device: {torch.cuda.current_device()}")
    print(f"  Device name: {torch.cuda.get_device_name(0)}")
    print(f"  Device capability: {torch.cuda.get_device_capability(0)}")
    
    print(f"\nMemory Information:")
    print(f"  Total memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"  Reserved memory: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")
    print(f"  Allocated memory: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    
    print("\nRunning GPU benchmark...")
    
    # Warmup
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    torch.cuda.synchronize()
    
    # Benchmark
    sizes = [1000, 2000, 4000]
    for size in sizes:
        x = torch.randn(size, size).cuda()
        y = torch.randn(size, size).cuda()
        
        torch.cuda.synchronize()
        start = time.time()
        
        z = torch.matmul(x, y)
        
        torch.cuda.synchronize()
        elapsed = time.time() - start
        
        gflops = (2 * size**3) / (elapsed * 1e9)
        print(f"  Matrix multiply {size}x{size}: {elapsed:.3f}s ({gflops:.1f} GFLOPS)")
    
    print("\n✓ GPU is working properly!")
    
else:
    print("\n✗ CUDA is not available")
    print("\nTroubleshooting steps:")
    print("1. Make sure CUDA environment is set:")
    print("   source /moneyball/setup_cuda_env.sh")
    print("2. Check GPU visibility:")
    print("   nvidia-smi")
    print("3. Check PyTorch CUDA version:")
    print(f"   PyTorch built with CUDA: {torch.version.cuda}")
    
    if torch.version.cuda is None:
        print("\n⚠️  This is a CPU-only PyTorch build!")
        print("   Re-run the installation script.")
TEST

chmod +x /moneyball/test_pytorch_gpu.py

# 9. Summary
echo
echo "=== INSTALLATION COMPLETE ==="
echo
echo "Test PyTorch GPU support:"
echo "  python /moneyball/test_pytorch_gpu.py"
echo
echo "If CUDA is still not available:"
echo "1. Make sure CUDA environment is set:"
echo "   source /moneyball/setup_cuda_env.sh"
echo "2. Check LD_LIBRARY_PATH includes CUDA libraries"
echo "3. Try setting CUDA_VISIBLE_DEVICES=0"
echo
echo "Note: vGPU may still block CUDA operations even with proper installation."