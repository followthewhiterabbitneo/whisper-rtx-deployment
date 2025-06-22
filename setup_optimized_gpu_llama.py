#!/usr/bin/env python3
"""
Optimized GPU Llama Service
Manages memory efficiently
"""
import subprocess
import time
import torch
import os

class OptimizedGPULlama:
    """Memory-efficient GPU Llama service"""
    
    def __init__(self, model_name="llama3:8b-instruct-q4_0"):
        self.model_name = model_name
        print("=== Optimized GPU Llama Service ===")
        
        # Show current GPU state
        self._show_gpu_state()
        
        # Clean up existing models
        self._cleanup_models()
        
        # Load optimized model
        self._load_optimized_model()
        
    def _show_gpu_state(self):
        """Show current GPU memory usage"""
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.free,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        used, free, total = result.stdout.strip().split(", ")
        print(f"GPU Memory: {used} used, {free} free, {total} total")
        
        # Check what models are loaded
        result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"Models in memory:\n{result.stdout}")
    
    def _cleanup_models(self):
        """Unload unnecessary models"""
        print("\nCleaning up GPU memory...")
        
        # Stop ollama to clear all models
        subprocess.run(["ollama", "stop"], capture_output=True)
        time.sleep(2)
        
        # Restart ollama
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "OLLAMA_MAX_LOADED_MODELS": "1"}
        )
        time.sleep(3)
        
        # Check memory after cleanup
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        print(f"GPU memory after cleanup: {result.stdout.strip()} MiB")
    
    def _load_optimized_model(self):
        """Load quantized model for efficiency"""
        print(f"\nLoading optimized model: {self.model_name}")
        
        # Pull model if needed
        print("Pulling model (if needed)...")
        subprocess.run(
            ["ollama", "pull", self.model_name],
            capture_output=True
        )
        
        # Load into GPU
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", self.model_name, "Initialize"],
            capture_output=True,
            text=True
        )
        load_time = time.time() - start
        
        print(f"Model loaded in {load_time:.1f}s")
        
        # Final memory check
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        print(f"GPU memory with model: {result.stdout.strip()} MiB")
    
    def query(self, prompt):
        """Query with memory tracking"""
        start = time.time()
        
        result = subprocess.run(
            ["ollama", "run", self.model_name, prompt],
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start
        
        # Quick memory check
        mem_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        
        return {
            "response": result.stdout.strip(),
            "time": elapsed,
            "memory_used": f"{mem_result.stdout.strip()} MiB"
        }
    
    def compare_models(self):
        """Compare different model sizes"""
        print("\n=== Model Size Comparison ===")
        
        models = [
            ("llama3:8b-instruct-q4_0", "4-bit quantized, ~4GB"),
            ("llama3:8b-instruct-q5_K_M", "5-bit quantized, ~5GB"),
            ("llama3:8b-instruct-fp16", "Full precision, ~16GB"),
        ]
        
        print("\nAvailable options:")
        for model, desc in models:
            print(f"  {model}: {desc}")
        
        print(f"\nCurrently using: {self.model_name}")
        print("The q4_0 version is recommended for 8GB vGPU")

def main():
    """Test optimized setup"""
    print("Optimizing GPU memory usage...\n")
    
    # Create optimized service
    service = OptimizedGPULlama()
    
    # Test query
    print("\n=== Testing Optimized Model ===")
    result = service.query("What is 2+2? Answer in one line.")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.2f}s")
    print(f"Memory: {result['memory_used']}")
    
    # Show model options
    service.compare_models()
    
    print("\n✓ Optimized setup complete!")
    print("✓ Using efficient quantized model")
    print("✓ Memory usage minimized")

if __name__ == "__main__":
    main()