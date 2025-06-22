#!/usr/bin/env python3
"""Check if GPU is actually computing"""
import subprocess
import threading
import time

def monitor_gpu():
    """Monitor GPU usage"""
    print("Monitoring GPU usage during inference...")
    for i in range(10):
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        print(f"  {result.stdout.strip()}")
        time.sleep(1)

# Start monitoring in background
monitor_thread = threading.Thread(target=monitor_gpu)
monitor_thread.start()

# Try a simple query
print("\nSending query to Ollama...")
result = subprocess.run(
    ["timeout", "20", "ollama", "run", "llama3", "Hi"],
    capture_output=True,
    text=True
)

monitor_thread.join()

print(f"\nResult: {result.stdout}")
print(f"Return code: {result.returncode}")

if result.returncode == 124:
    print("\n❌ TIMEOUT! Model is loaded but not generating")
    print("\nPossible issues:")
    print("1. Model loaded to GPU memory but compute is on CPU")
    print("2. GPU compute blocked")
    print("3. Model corruption")
    
    print("\nTry forcing CPU mode:")
    print("  CUDA_VISIBLE_DEVICES='' ollama run llama3 'Hi'")
else:
    print("\n✅ Model responded!")