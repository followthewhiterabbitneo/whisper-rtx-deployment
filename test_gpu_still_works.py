#!/usr/bin/env python3
"""Test if GPU still works with PyTorch"""
import torch
import time

print("=== TESTING GPU DIRECTLY ===")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # Test tensor operation
    print("\nTesting GPU operation:")
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    
    start = time.time()
    z = torch.matmul(x, y)
    torch.cuda.synchronize()
    elapsed = time.time() - start
    
    print(f"✅ GPU matrix multiply: {elapsed:.3f}s")
    print("✅ GPU IS WORKING FINE!")
    
    # Check memory
    print(f"\nGPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f} GB allocated")
    print(f"GPU Memory: {torch.cuda.memory_reserved()/1024**3:.2f} GB reserved")
else:
    print("❌ CUDA not available!")
    
# Test Ollama again
print("\n=== TESTING OLLAMA ===")
import subprocess

# Kill any stuck processes first
subprocess.run(["pkill", "-f", "ollama run"], capture_output=True)
time.sleep(2)

# Try a simple query with timeout
print("Testing Ollama with timeout:")
try:
    result = subprocess.run(
        ["timeout", "10", "ollama", "run", "llama3", "Say hello"],
        capture_output=True,
        text=True
    )
    if result.returncode == 124:  # timeout exit code
        print("❌ Ollama timed out after 10 seconds")
    else:
        print(f"✅ Ollama responded: {result.stdout}")
except Exception as e:
    print(f"Error: {e}")

# Check what's using GPU memory
print("\n=== GPU PROCESSES ===")
result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
print(result.stdout)