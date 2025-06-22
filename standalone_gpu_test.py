#!/usr/bin/env python3
"""
Standalone GPU accessibility test
Tests basic GPU access through multiple methods
No dependencies on Ollama or specific models
"""
import subprocess
import os
import sys
import json
from datetime import datetime

def run_cmd(cmd, shell=False):
    """Run command and return success, stdout, stderr"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_nvidia_smi():
    """Test basic nvidia-smi commands"""
    print("=" * 60)
    print("1. NVIDIA-SMI TESTS")
    print("=" * 60)
    
    results = {}
    
    # Basic nvidia-smi
    print("\n[1.1] Basic nvidia-smi:")
    success, stdout, stderr = run_cmd(["nvidia-smi"])
    if success:
        print("✓ nvidia-smi accessible")
        print(stdout[:500] + "..." if len(stdout) > 500 else stdout)
        results["nvidia_smi_basic"] = "success"
    else:
        print("✗ nvidia-smi failed:", stderr[:200])
        results["nvidia_smi_basic"] = f"failed: {stderr[:100]}"
    
    # List GPUs
    print("\n[1.2] List GPUs:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "-L"])
    if success:
        print(stdout)
        results["gpu_list"] = stdout.strip()
    else:
        print("Failed:", stderr[:200])
        results["gpu_list"] = "failed"
    
    # Query specific info
    print("\n[1.3] GPU Memory Info:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free,memory.used", "--format=csv"])
    if success:
        print(stdout)
        results["memory_info"] = stdout.strip()
    else:
        print("Failed:", stderr[:200])
        results["memory_info"] = "failed"
    
    # Driver version
    print("\n[1.4] Driver Version:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
    if success:
        print(f"Driver: {stdout.strip()}")
        results["driver_version"] = stdout.strip()
    else:
        results["driver_version"] = "unknown"
    
    return results

def test_cuda_devices():
    """Test CUDA device access via various methods"""
    print("\n" + "=" * 60)
    print("2. CUDA DEVICE TESTS")
    print("=" * 60)
    
    results = {}
    
    # Check CUDA environment
    print("\n[2.1] CUDA Environment:")
    cuda_vars = ["CUDA_HOME", "CUDA_PATH", "CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH"]
    for var in cuda_vars:
        value = os.environ.get(var, "not set")
        print(f"{var}: {value}")
        results[f"env_{var}"] = value
    
    # Check for CUDA libraries
    print("\n[2.2] CUDA Libraries:")
    lib_paths = [
        "/usr/local/cuda/lib64/libcudart.so",
        "/usr/lib64/libcuda.so",
        "/usr/lib/x86_64-linux-gnu/libcuda.so",
        "/usr/lib64/nvidia/libcuda.so"
    ]
    
    cuda_found = False
    for lib in lib_paths:
        if os.path.exists(lib):
            print(f"✓ Found: {lib}")
            results[f"lib_{os.path.basename(lib)}"] = "found"
            cuda_found = True
            
            # Check if readable
            try:
                os.access(lib, os.R_OK)
                print(f"  Readable: Yes")
            except:
                print(f"  Readable: No")
        else:
            results[f"lib_{os.path.basename(lib)}"] = "not found"
    
    if not cuda_found:
        print("✗ No CUDA libraries found")
    
    # Try to check vGPU status
    print("\n[2.3] vGPU Status:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "vgpu", "-q"], shell=False)
    if success and stdout:
        print("vGPU Mode: Yes")
        print(stdout[:300])
        results["vgpu_mode"] = "yes"
    else:
        print("vGPU Mode: No (standard GPU)")
        results["vgpu_mode"] = "no"
    
    return results

def test_pytorch_cuda():
    """Test PyTorch CUDA access"""
    print("\n" + "=" * 60)
    print("3. PYTORCH CUDA TEST")
    print("=" * 60)
    
    results = {}
    
    try:
        import torch
        print(f"\n[3.1] PyTorch Version: {torch.__version__}")
        results["pytorch_version"] = torch.__version__
        
        print(f"\n[3.2] CUDA Available: {torch.cuda.is_available()}")
        results["cuda_available"] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            print(f"[3.3] CUDA Device Count: {torch.cuda.device_count()}")
            results["cuda_device_count"] = torch.cuda.device_count()
            
            print(f"[3.4] Current Device: {torch.cuda.current_device()}")
            results["current_device"] = torch.cuda.current_device()
            
            print(f"[3.5] Device Name: {torch.cuda.get_device_name(0)}")
            results["device_name"] = torch.cuda.get_device_name(0)
            
            print(f"[3.6] Device Capability: {torch.cuda.get_device_capability(0)}")
            results["device_capability"] = str(torch.cuda.get_device_capability(0))
            
            # Try simple operation
            print("\n[3.7] Testing GPU Operation:")
            try:
                x = torch.randn(100, 100).cuda()
                y = torch.randn(100, 100).cuda()
                z = x @ y
                torch.cuda.synchronize()
                print("✓ GPU tensor operation successful")
                results["gpu_operation"] = "success"
            except Exception as e:
                print(f"✗ GPU operation failed: {e}")
                results["gpu_operation"] = f"failed: {str(e)[:100]}"
        else:
            print("\n✗ CUDA not available in PyTorch")
            
            # Try to understand why
            print("\n[3.8] Debugging CUDA availability:")
            if hasattr(torch.cuda, "_initialized"):
                print(f"CUDA initialized: {torch.cuda._initialized}")
            
            try:
                torch.cuda.init()
                print("Manual CUDA init attempted")
            except Exception as e:
                print(f"Manual init failed: {e}")
                results["cuda_init_error"] = str(e)[:200]
                
    except ImportError:
        print("✗ PyTorch not installed")
        results["pytorch"] = "not installed"
    except Exception as e:
        print(f"✗ PyTorch test error: {e}")
        results["pytorch_error"] = str(e)[:200]
    
    return results

def test_simple_cuda_binary():
    """Test with simple CUDA binary if available"""
    print("\n" + "=" * 60)
    print("4. CUDA BINARY TESTS")
    print("=" * 60)
    
    results = {}
    
    # Look for deviceQuery
    print("\n[4.1] Looking for CUDA samples:")
    success, stdout, stderr = run_cmd(["which", "deviceQuery"])
    if success:
        print(f"Found deviceQuery: {stdout.strip()}")
        print("\nRunning deviceQuery:")
        success, stdout, stderr = run_cmd(["deviceQuery"])
        if success:
            print(stdout[:500])
            results["deviceQuery"] = "success"
        else:
            print(f"Failed: {stderr[:200]}")
            results["deviceQuery"] = f"failed: {stderr[:100]}"
    else:
        print("deviceQuery not found in PATH")
        results["deviceQuery"] = "not found"
    
    # Try nvidia-ml-py if available
    print("\n[4.2] Testing nvidia-ml-py:")
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        print(f"✓ NVML device count: {device_count}")
        results["nvml_device_count"] = device_count
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            print(f"  Device {i}: {name}")
            
        pynvml.nvmlShutdown()
    except ImportError:
        print("pynvml not installed (pip install nvidia-ml-py)")
        results["nvml"] = "not installed"
    except Exception as e:
        print(f"NVML error: {e}")
        results["nvml_error"] = str(e)[:100]
    
    return results

def test_compute_mode():
    """Check GPU compute mode and permissions"""
    print("\n" + "=" * 60)
    print("5. COMPUTE MODE AND PERMISSIONS")
    print("=" * 60)
    
    results = {}
    
    # Check compute mode
    print("\n[5.1] GPU Compute Mode:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "--query-gpu=compute_mode", "--format=csv,noheader"])
    if success:
        mode = stdout.strip()
        print(f"Mode: {mode}")
        results["compute_mode"] = mode
        
        if "Exclusive" in mode:
            print("⚠️  WARNING: GPU in exclusive mode - only one process can use it")
        elif "Prohibited" in mode:
            print("⚠️  ERROR: GPU compute prohibited!")
    
    # Check persistence mode
    print("\n[5.2] Persistence Mode:")
    success, stdout, stderr = run_cmd(["nvidia-smi", "--query-gpu=persistence_mode", "--format=csv,noheader"])
    if success:
        print(f"Persistence: {stdout.strip()}")
        results["persistence_mode"] = stdout.strip()
    
    # Check current user permissions
    print("\n[5.3] User Permissions:")
    print(f"Current user: {os.environ.get('USER', 'unknown')}")
    print(f"User ID: {os.getuid()}")
    print(f"Group ID: {os.getgid()}")
    
    # Check device permissions
    print("\n[5.4] Device Permissions:")
    devices = ["/dev/nvidia0", "/dev/nvidiactl", "/dev/nvidia-uvm"]
    for dev in devices:
        if os.path.exists(dev):
            stat = os.stat(dev)
            mode = oct(stat.st_mode)[-3:]
            print(f"{dev}: mode={mode}, uid={stat.st_uid}, gid={stat.st_gid}")
            results[f"perm_{os.path.basename(dev)}"] = mode
        else:
            print(f"{dev}: not found")
    
    return results

def create_summary(all_results):
    """Create summary and diagnosis"""
    print("\n" + "=" * 60)
    print("SUMMARY AND DIAGNOSIS")
    print("=" * 60)
    
    # Check if GPU is visible
    gpu_visible = all_results.get("nvidia_smi", {}).get("nvidia_smi_basic") == "success"
    cuda_available = all_results.get("pytorch", {}).get("cuda_available", False)
    
    print(f"\nGPU Visible to System: {'Yes' if gpu_visible else 'No'}")
    print(f"CUDA Available to PyTorch: {'Yes' if cuda_available else 'No'}")
    
    if gpu_visible and not cuda_available:
        print("\n⚠️  GPU is visible but CUDA is not accessible!")
        print("\nPossible causes:")
        print("1. vGPU licensing issue")
        print("2. CUDA context creation blocked")
        print("3. Driver/CUDA version mismatch")
        print("4. Exclusive compute mode with another process using GPU")
        print("5. Container/VM restrictions")
        
        # Check for specific vGPU error
        if "801" in str(all_results.get("pytorch", {}).get("cuda_init_error", "")):
            print("\n🔴 Error 801 detected: This is a vGPU-specific error")
            print("   The vGPU may require a license for CUDA operations")
    
    elif not gpu_visible:
        print("\n🔴 No GPU detected by nvidia-smi")
    
    else:
        print("\n✅ GPU is accessible!")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/moneyball/gpu_test_results_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return all_results

def main():
    """Run all GPU tests"""
    print("STANDALONE GPU ACCESSIBILITY TEST")
    print("=" * 60)
    print(f"Date: {datetime.now()}")
    print(f"Host: {subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()}")
    print(f"User: {os.environ.get('USER', 'unknown')}")
    print()
    
    all_results = {}
    
    # Run all tests
    all_results["nvidia_smi"] = test_nvidia_smi()
    all_results["cuda_devices"] = test_cuda_devices()
    all_results["pytorch"] = test_pytorch_cuda()
    all_results["cuda_binary"] = test_simple_cuda_binary()
    all_results["compute_mode"] = test_compute_mode()
    
    # Create summary
    create_summary(all_results)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()