#!/usr/bin/env python3
"""
Check if Ollama is using GPU
"""
import subprocess
import os

def check_gpu_usage():
    """Check if Ollama/Gemma is using GPU"""
    print("=== Checking Ollama GPU Usage ===")
    
    # Check Ollama version and capabilities
    print("\n1. Ollama info:")
    subprocess.run(["ollama", "--version"])
    
    # Check GPU availability
    print("\n2. NVIDIA GPU Status:")
    result = subprocess.run(
        ["nvidia-smi"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    print(result.stdout)
    
    # Check running processes on GPU
    print("\n3. GPU Processes:")
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,name,used_memory", "--format=csv"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    print(result.stdout)
    
    # Run a test and monitor GPU
    print("\n4. Testing Gemma with GPU monitoring...")
    print("Running inference and checking GPU memory...")
    
    # Get GPU memory before
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    mem_before = result.stdout.strip()
    
    # Run Gemma
    print("Running Gemma...")
    result = subprocess.run(
        ["ollama", "run", "gemma2-legal", "Test prompt for GPU check"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Get GPU memory after
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    mem_after = result.stdout.strip()
    
    print(f"\nGPU Memory before: {mem_before} MB")
    print(f"GPU Memory after: {mem_after} MB")
    
    try:
        diff = int(mem_after) - int(mem_before)
        if diff > 100:
            print(f"✓ GPU is being used! Memory increased by {diff} MB")
        else:
            print("✗ GPU might not be used (no significant memory change)")
    except:
        pass
    
    # Check Ollama logs
    print("\n5. Checking Ollama logs for GPU info:")
    log_file = "/moneyball/ollama/ollama.log"
    if os.path.exists(log_file):
        subprocess.run(["tail", "-20", log_file])
    else:
        print("Log file not found at", log_file)
    
    print("\n=== To force GPU usage ===")
    print("1. Set environment: export CUDA_VISIBLE_DEVICES=0")
    print("2. Restart Ollama: pkill ollama && ollama serve")
    print("3. Check model info: ollama show gemma2-legal")

if __name__ == "__main__":
    check_gpu_usage()