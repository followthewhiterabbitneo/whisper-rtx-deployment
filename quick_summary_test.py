#!/usr/bin/env python3
"""
Quick summary test with shorter timeout and simpler prompts
"""
import subprocess
import time

def quick_test():
    """Test with very short prompt and extended timeout"""
    print("=== Quick Gemma Test ===")
    
    # First check if Ollama is running
    print("1. Checking Ollama status...")
    result = subprocess.run(
        ["pgrep", "-f", "ollama"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        print("Ollama not running! Starting it...")
        subprocess.Popen(["ollama", "serve"])
        time.sleep(5)
    
    # Very simple test
    print("\n2. Testing with minimal prompt...")
    start = time.time()
    
    try:
        result = subprocess.run(
            ["ollama", "run", "gemma2-legal", "Say hello"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=60  # 60 second timeout
        )
        
        elapsed = time.time() - start
        print(f"Response time: {elapsed:.1f} seconds")
        
        if result.returncode == 0:
            print(f"Response: {result.stdout}")
            if elapsed > 10:
                print("\n⚠️  Response is slow - likely using CPU")
                print("GPU would respond in 1-3 seconds")
        else:
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT after 60 seconds - definitely using CPU!")
    
    # Check GPU
    print("\n3. Checking GPU usage...")
    subprocess.run(["nvidia-smi"])
    
    print("\n=== Solutions ===")
    print("1. Restart Ollama with GPU:")
    print("   pkill ollama")
    print("   CUDA_VISIBLE_DEVICES=0 ollama serve &")
    print("\n2. Or use a smaller model:")
    print("   ollama pull gemma:2b")
    print("   ollama run gemma:2b 'test'")

if __name__ == "__main__":
    quick_test()