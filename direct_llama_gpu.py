#!/usr/bin/env python3
"""
Direct GPU usage without unnecessary pulls
Uses existing models efficiently
"""
import subprocess
import time
import os

def check_existing_models():
    """Check what models we already have"""
    print("=== Checking Existing Models ===")
    
    # List models
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    print("Installed models:")
    print(result.stdout)
    
    # Check what's loaded
    result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
    print("\nModels in GPU memory:")
    print(result.stdout if result.stdout.strip() else "  None")
    
    return result.stdout

def use_existing_model(model_name="llama3-legal"):
    """Use model that's already installed"""
    print(f"\n=== Using Existing Model: {model_name} ===")
    
    # Check if model exists
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if model_name not in result.stdout:
        print(f"ERROR: {model_name} not found!")
        print("Available models:")
        print(result.stdout)
        return None
    
    print(f"✓ Model {model_name} already installed")
    
    # NO PULL - just run it!
    print("\nRunning query (NO download needed)...")
    start = time.time()
    
    result = subprocess.run(
        ["ollama", "run", model_name, "Say hello"],
        capture_output=True,
        text=True
    )
    
    elapsed = time.time() - start
    print(f"Response time: {elapsed:.2f}s")
    print(f"Response: {result.stdout.strip()[:100]}...")
    
    # Check memory
    mem = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True
    )
    print(f"GPU memory used: {mem.stdout.strip()} MiB")
    
    return model_name

def find_memory_hog():
    """Find which model is using 5.3GB"""
    print("\n=== Finding Memory Hog ===")
    
    # Get all models
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    models = []
    for line in result.stdout.strip().split('\n')[1:]:  # Skip header
        if line:
            model = line.split()[0]
            size = line.split()[1] if len(line.split()) > 1 else "?"
            models.append((model, size))
    
    print("Model sizes on disk:")
    for model, size in models:
        print(f"  {model}: {size}")
    
    # The 5.3GB culprit is likely:
    # - llama2:70b (too big)
    # - llama3:70b (too big)  
    # - mixtral (big)
    # - An fp16 non-quantized model
    
    print("\nTo free memory from large model:")
    print("1. ollama stop")
    print("2. ollama rm large-model-name")
    print("3. Restart ollama")

def optimal_setup():
    """Set up optimal configuration"""
    print("\n=== Optimal GPU Setup ===")
    
    print("For 8GB vGPU, recommended models:")
    print("  - llama3:8b-instruct-q4_0 (~4GB)")
    print("  - mistral:7b-instruct-q4_0 (~4GB)")
    print("  - phi3:mini (~2GB)")
    
    print("\nTo switch to smaller model:")
    print("  1. ollama rm current-large-model")
    print("  2. ollama pull llama3:8b-instruct-q4_0")
    print("  3. Use that for inference")

def main():
    # Check what we have
    check_existing_models()
    
    # Use existing model (no pull!)
    model = use_existing_model()
    
    # Find the memory hog
    find_memory_hog()
    
    # Show optimal setup
    optimal_setup()
    
    print("\n✓ Key insight: Don't pull models you already have!")
    print("✓ The 5.3GB is likely a large model stuck in memory")
    print("✓ Use 'ollama ps' to see what's loaded")

if __name__ == "__main__":
    main()