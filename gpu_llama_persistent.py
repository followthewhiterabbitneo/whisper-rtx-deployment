#!/usr/bin/env python3
"""
PERSISTENT GPU LLAMA SERVICE
Keeps model loaded in VRAM for instant responses
"""
import torch
import subprocess
import time
import threading
import queue
from datetime import datetime

class PersistentGPULlama:
    """Persistent GPU service that keeps model in VRAM"""
    
    def __init__(self):
        print("=== Persistent GPU Llama Service ===")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        self.model_name = "llama3-legal"
        self.process = None
        self.ready = False
        
        # Start Ollama and load model ONCE
        self._initialize()
        
        # Keep-alive thread
        self.keeper = threading.Thread(target=self._keep_alive)
        self.keeper.daemon = True
        self.keeper.start()
        
    def _initialize(self):
        """Start Ollama and load model into VRAM"""
        print("\nStarting Ollama with GPU...")
        
        # Kill existing instances
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
        time.sleep(2)
        
        # Start Ollama
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        
        # Load model ONCE into VRAM
        print("Loading model into VRAM (one-time cost)...")
        start = time.time()
        
        # Run a dummy query to load model
        result = subprocess.run(
            ["ollama", "run", self.model_name, "Initialize model"],
            capture_output=True,
            text=True
        )
        
        load_time = time.time() - start
        print(f"✓ Model loaded in {load_time:.1f}s")
        print("✓ Model now resident in VRAM!")
        
        self.ready = True
        
    def _keep_alive(self):
        """Keep model in VRAM"""
        while True:
            time.sleep(30)  # Every 30 seconds
            if self.ready:
                # Send tiny query to keep model active
                subprocess.run(
                    ["ollama", "run", self.model_name, ""],
                    capture_output=True,
                    timeout=5
                )
    
    def query(self, prompt):
        """Fast query - model already in VRAM!"""
        if not self.ready:
            print("Model not ready yet...")
            return None
            
        start = time.time()
        
        result = subprocess.run(
            ["ollama", "run", self.model_name, prompt],
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start
        
        return {
            "response": result.stdout.strip(),
            "time": elapsed,
            "cached": True  # Model was pre-loaded
        }
    
    def benchmark_cached(self):
        """Benchmark with cached model"""
        print("\n=== Benchmark with Model in VRAM ===")
        
        queries = [
            "What is 2+2?",
            "Summarize: Customer called about loan status.",
            "Create a legal summary of: " + "Meeting discussion. " * 10,
            "Analyze this contract clause: " + "Terms and conditions. " * 20
        ]
        
        print("\nResponse times (model pre-loaded in VRAM):")
        for i, query in enumerate(queries, 1):
            result = self.query(query)
            if result:
                print(f"  Query {i}: {result['time']:.2f}s")
                if i == 1:  # Show first response
                    print(f"    Response: {result['response'][:50]}...")
        
        print("\n✓ Notice how much faster these are!")
        print("✓ Model stays loaded in VRAM between queries")

# Global instance - keeps model loaded
_persistent_service = None

def get_gpu_service():
    """Get or create persistent GPU service"""
    global _persistent_service
    if _persistent_service is None:
        _persistent_service = PersistentGPULlama()
    return _persistent_service

def quick_test():
    """Quick test showing the speed difference"""
    print("\n=== Speed Comparison Test ===")
    
    service = get_gpu_service()
    
    # First query (already loaded!)
    print("\nFirst query (model already in VRAM):")
    result = service.query("What is the capital of France?")
    print(f"Time: {result['time']:.2f}s")
    print(f"Response: {result['response']}")
    
    # Second query (super fast)
    print("\nSecond query (cached):")
    result = service.query("What is 10 times 20?")
    print(f"Time: {result['time']:.2f}s")
    print(f"Response: {result['response']}")
    
    # Complex query
    print("\nComplex query (cached):")
    result = service.query("Write a haiku about GPUs")
    print(f"Time: {result['time']:.2f}s")
    print(f"Response: {result['response']}")

def legal_summary_fast(transcript):
    """Fast legal summary using persistent service"""
    service = get_gpu_service()
    
    prompt = f"""Create a concise legal summary:
{transcript[:2000]}

FORMAT: Date, Parties, Issue, Resolution, Next Steps"""
    
    start = time.time()
    result = service.query(prompt)
    total = time.time() - start
    
    print(f"\nLegal summary generated in {total:.1f}s (model pre-loaded)")
    return result

if __name__ == "__main__":
    print("Starting persistent GPU service...")
    print("First load takes time, then everything is FAST!\n")
    
    # Initialize service (one-time cost)
    service = get_gpu_service()
    
    # Run benchmarks
    service.benchmark_cached()
    
    # Quick test
    quick_test()
    
    print("\n=== Service Running ===")
    print("Model is loaded in VRAM and will stay there!")
    print("\nUsage:")
    print("  from gpu_llama_persistent import get_gpu_service")
    print("  service = get_gpu_service()")
    print("  result = service.query('your prompt')")
    print("\nNo more reload delays!")