#!/usr/bin/env python3
"""
Comprehensive GPU benchmark to test vGPU accessibility
Tests various GPU operations to diagnose access issues
"""
import subprocess
import sys
import os
import time

def run_command(cmd, check=False):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_nvidia_smi():
    """Test basic nvidia-smi access"""
    print("=== 1. Testing nvidia-smi ===")
    
    tests = [
        ("Basic query", "nvidia-smi"),
        ("List GPUs", "nvidia-smi -L"),
        ("Query specific", "nvidia-smi -q"),
        ("Memory info", "nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv"),
        ("Compute mode", "nvidia-smi --query-gpu=compute_mode --format=csv"),
        ("Persistence", "nvidia-smi --query-gpu=persistence_mode --format=csv"),
    ]
    
    for test_name, cmd in tests:
        print(f"\n{test_name}:")
        success, stdout, stderr = run_command(cmd)
        if success:
            print(stdout[:200])
        else:
            print(f"Failed: {stderr[:200]}")

def test_cuda_samples():
    """Test CUDA sample programs"""
    print("\n=== 2. Testing CUDA Samples ===")
    
    # Find CUDA samples
    cuda_paths = [
        "/usr/local/cuda/samples",
        "/opt/cuda/samples",
        "/usr/share/cuda/samples"
    ]
    
    samples_found = False
    for path in cuda_paths:
        if os.path.exists(path):
            print(f"Found CUDA samples at: {path}")
            samples_found = True
            break
    
    if not samples_found:
        print("No CUDA samples found. Trying deviceQuery...")
    
    # Try to run deviceQuery
    success, stdout, stderr = run_command("which deviceQuery")
    if success:
        print("\nRunning deviceQuery:")
        success, stdout, stderr = run_command("deviceQuery")
        print(stdout if success else f"Failed: {stderr}")
    else:
        print("deviceQuery not found in PATH")

def test_pytorch_gpu():
    """Test PyTorch GPU access"""
    print("\n=== 3. Testing PyTorch GPU Access ===")
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
            print(f"CUDA capability: {torch.cuda.get_device_capability(0)}")
            
            # Try a simple operation
            print("\nTesting tensor operation on GPU...")
            try:
                x = torch.randn(1000, 1000).cuda()
                y = torch.randn(1000, 1000).cuda()
                start = time.time()
                z = torch.matmul(x, y)
                torch.cuda.synchronize()
                elapsed = time.time() - start
                print(f"✓ Matrix multiplication successful in {elapsed:.3f}s")
            except Exception as e:
                print(f"✗ GPU operation failed: {e}")
        else:
            print("PyTorch cannot access CUDA")
            
    except ImportError:
        print("PyTorch not installed")
        print("Install with: pip install torch")

def test_tensorflow_gpu():
    """Test TensorFlow GPU access"""
    print("\n=== 4. Testing TensorFlow GPU Access ===")
    
    try:
        import tensorflow as tf
        print(f"TensorFlow version: {tf.__version__}")
        
        gpus = tf.config.list_physical_devices('GPU')
        print(f"GPUs found: {len(gpus)}")
        for gpu in gpus:
            print(f"  - {gpu}")
        
        if gpus:
            # Try a simple operation
            print("\nTesting GPU operation...")
            try:
                with tf.device('/GPU:0'):
                    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
                    b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
                    c = tf.matmul(a, b)
                print(f"✓ GPU operation successful: {c}")
            except Exception as e:
                print(f"✗ GPU operation failed: {e}")
                
    except ImportError:
        print("TensorFlow not installed")

def test_cuda_runtime():
    """Test CUDA runtime directly"""
    print("\n=== 5. Testing CUDA Runtime ===")
    
    # Check for CUDA libraries
    cuda_libs = [
        "/usr/local/cuda/lib64/libcudart.so",
        "/usr/lib/x86_64-linux-gnu/libcuda.so",
        "/usr/lib64/libcuda.so"
    ]
    
    for lib in cuda_libs:
        if os.path.exists(lib):
            print(f"✓ Found: {lib}")
            # Check if we can read it
            success, stdout, stderr = run_command(f"ldd {lib} | head -5")
            if success:
                print(f"  Dependencies: {stdout[:100]}...")
        else:
            print(f"✗ Not found: {lib}")

def test_gpu_memory_allocation():
    """Test direct GPU memory allocation"""
    print("\n=== 6. Testing GPU Memory Allocation ===")
    
    # Create a simple CUDA test program
    cuda_test = """
#include <stdio.h>
#include <cuda_runtime.h>

int main() {
    int deviceCount;
    cudaError_t error = cudaGetDeviceCount(&deviceCount);
    
    if (error != cudaSuccess) {
        printf("CUDA Error getting device count: %s\\n", cudaGetErrorString(error));
        return 1;
    }
    
    printf("CUDA device count: %d\\n", deviceCount);
    
    if (deviceCount > 0) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, 0);
        printf("Device 0: %s\\n", prop.name);
        printf("Memory: %zu MB\\n", prop.totalGlobalMem / 1048576);
        
        // Try to allocate memory
        void* d_mem;
        size_t size = 100 * 1024 * 1024; // 100MB
        error = cudaMalloc(&d_mem, size);
        
        if (error == cudaSuccess) {
            printf("✓ Successfully allocated 100MB on GPU\\n");
            cudaFree(d_mem);
        } else {
            printf("✗ Failed to allocate GPU memory: %s\\n", cudaGetErrorString(error));
        }
    }
    
    return 0;
}
"""
    
    # Try to compile and run
    with open("/tmp/cuda_test.cu", "w") as f:
        f.write(cuda_test)
    
    print("Attempting to compile CUDA test...")
    success, stdout, stderr = run_command("nvcc -o /tmp/cuda_test /tmp/cuda_test.cu 2>&1")
    
    if success:
        print("✓ Compilation successful")
        print("\nRunning CUDA test:")
        success, stdout, stderr = run_command("/tmp/cuda_test")
        print(stdout if success else f"Failed: {stderr}")
    else:
        print(f"✗ Compilation failed: {stderr[:200]}")
        print("\nnvcc might not be installed or in PATH")

def diagnose_vgpu():
    """Specific vGPU diagnostics"""
    print("\n=== 7. vGPU Specific Diagnostics ===")
    
    # Check vGPU specific settings
    success, stdout, stderr = run_command("nvidia-smi vgpu -q")
    if success:
        print("vGPU Query output:")
        print(stdout[:500])
    else:
        print("Standard GPU (not vGPU) or command failed")
    
    # Check for vGPU licensing
    print("\nChecking for licensing issues:")
    success, stdout, stderr = run_command("nvidia-smi -q | grep -i license")
    if stdout:
        print(stdout)
    
    # Check compute mode
    print("\nChecking compute mode:")
    success, stdout, stderr = run_command("nvidia-smi --query-gpu=compute_mode --format=csv,noheader")
    if success:
        print(f"Compute mode: {stdout.strip()}")
        if "Exclusive" in stdout:
            print("⚠️  GPU is in exclusive mode - might prevent multi-process access")

def create_summary():
    """Create summary and recommendations"""
    print("\n=== SUMMARY & RECOMMENDATIONS ===")
    
    print("""
Based on the error "nvcuda failed to get primary device context 801", this is likely:

1. **vGPU Licensing Issue**: The vGPU might need a license for CUDA operations
2. **Compute Mode Restriction**: vGPU might be in exclusive process mode
3. **Driver Mismatch**: Guest driver might not match vGPU version
4. **Resource Limit**: vGPU might have CUDA context limits

Workarounds:
1. Use CPU-based inference (already set up)
2. Try OpenCL instead of CUDA
3. Use cloud GPU services for heavy inference
4. Run inference on your RTX machine and transfer results
""")

def main():
    print("=== GPU BENCHMARK AND DIAGNOSTIC ===")
    print(f"Running as: {os.environ.get('USER', 'unknown')}")
    print(f"Hostname: {subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()}")
    print("")
    
    test_nvidia_smi()
    test_cuda_samples()
    test_pytorch_gpu()
    test_tensorflow_gpu()
    test_cuda_runtime()
    test_gpu_memory_allocation()
    diagnose_vgpu()
    create_summary()

if __name__ == "__main__":
    main()