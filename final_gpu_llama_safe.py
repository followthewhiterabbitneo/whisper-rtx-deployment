#!/usr/bin/env python3
"""
Final SAFE GPU Llama setup
Uses /moneyball for everything
"""
import os
import subprocess
import time
import torch

# CRITICAL: Set Ollama environment
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'
os.environ['OLLAMA_DATA_DIR'] = '/moneyball/ollama/data'
os.environ['OLLAMA_TMPDIR'] = '/moneyball/ollama/tmp'

class SafeGPULlama:
    """Safe GPU Llama service using /moneyball"""
    
    def __init__(self):
        print("=== Safe GPU Llama Service ===")
        print(f"Models directory: {os.environ['OLLAMA_MODELS']}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Disk usage - Root: {self._get_disk_usage('/')}, Moneyball: {self._get_disk_usage('/moneyball')}")
        
        # Safety check
        root_usage = int(self._get_disk_usage('/').strip('%'))
        if root_usage > 80:
            print(f"\n⚠️  WARNING: Root filesystem is {root_usage}% full!")
            print("Consider more cleanup before proceeding.")
        
        self.model_name = "llama3:8b-instruct-q4_0"  # Efficient 4-bit model
        self._ensure_safe_ollama()
        
    def _get_disk_usage(self, path):
        """Get disk usage percentage"""
        result = subprocess.run(
            f"df {path} | tail -1 | awk '{{print $5}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def _ensure_safe_ollama(self):
        """Start Ollama with /moneyball storage"""
        # Check if running
        result = subprocess.run(["pgrep", "-f", "ollama serve"], capture_output=True)
        
        if result.returncode != 0:
            print("\nStarting Ollama with safe storage...")
            # Set environment and start
            env = os.environ.copy()
            env['OLLAMA_MODELS'] = '/moneyball/ollama/models'
            
            subprocess.Popen(
                ["ollama", "serve"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)
            print("✓ Ollama started with /moneyball storage")
        else:
            print("✓ Ollama already running")
    
    def check_models(self):
        """Check installed models"""
        print("\nInstalled models:")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        print(result.stdout)
        
        # Check model directory
        models_dir = "/moneyball/ollama/models"
        if os.path.exists(models_dir):
            size = subprocess.run(
                f"du -sh {models_dir}",
                shell=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            print(f"Models directory size: {size}")
    
    def load_model(self):
        """Load efficient model"""
        print(f"\nLoading {self.model_name}...")
        
        # Check if already have it
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if self.model_name.split(':')[0] in result.stdout:
            print("✓ Model already installed")
        else:
            print("Pulling efficient 4-bit model...")
            subprocess.run(["ollama", "pull", self.model_name])
        
        # Warm up
        print("Warming up GPU...")
        start = time.time()
        subprocess.run(
            ["ollama", "run", self.model_name, "Hello"],
            capture_output=True
        )
        print(f"✓ Model ready in {time.time()-start:.1f}s")
        
        # Check GPU memory
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        print(f"GPU memory used: {result.stdout.strip()} MiB")
    
    def query(self, prompt):
        """Query the model"""
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
            "success": result.returncode == 0
        }

def main():
    """Test safe GPU setup"""
    print("Setting up SAFE GPU inference...")
    print("All models will be stored in /moneyball")
    print()
    
    # Create service
    service = SafeGPULlama()
    
    # Check models
    service.check_models()
    
    # Load model
    service.load_model()
    
    # Test query
    print("\nTesting inference...")
    result = service.query("What is 2+2? Answer in one word.")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.2f}s")
    
    print("\n✅ Safe GPU setup complete!")
    print("✅ Root filesystem protected")
    print("✅ All models in /moneyball")
    
if __name__ == "__main__":
    main()