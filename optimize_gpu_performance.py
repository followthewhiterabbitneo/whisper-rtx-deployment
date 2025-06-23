#!/usr/bin/env python3
"""
Test different llama.cpp settings to optimize RTX 4090 performance
Find out why we're only getting 16-21 tokens/sec instead of 50-100+
"""

import os
import time
import subprocess
from llama_cpp import Llama

MODEL_PATH = "C:/Users/estillmane/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

def check_gpu():
    """Quick GPU check"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            mem, util, temp = result.stdout.strip().split(', ')
            return f"Memory: {mem}MB, Util: {util}%, Temp: {temp}C"
    except:
        pass
    return "N/A"

def test_configuration(name, **kwargs):
    """Test a specific configuration"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Config: {kwargs}")
    print(f"GPU before: {check_gpu()}")
    
    try:
        # Load model
        start = time.time()
        llm = Llama(
            model_path=MODEL_PATH,
            verbose=False,
            **kwargs
        )
        load_time = time.time() - start
        print(f"Load time: {load_time:.1f}s")
        print(f"GPU after load: {check_gpu()}")
        
        # Test generation
        prompt = "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\nWrite a 100 word summary about mortgage loans.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        
        start = time.time()
        response = llm(
            prompt,
            max_tokens=200,
            temperature=0.1,
            echo=False
        )
        gen_time = time.time() - start
        
        tokens = response['usage']['completion_tokens']
        speed = tokens / gen_time
        
        print(f"GPU during gen: {check_gpu()}")
        print(f"Generated: {tokens} tokens in {gen_time:.1f}s = {speed:.1f} tok/s")
        
        # Detailed timings
        if 'timings' in response:
            t = response['timings']
            print(f"Prompt eval: {t.get('prompt_ms', 0)/t.get('prompt_n', 1):.2f} ms/tok")
            print(f"Token gen: {t.get('predicted_ms', 0)/t.get('predicted_n', 1):.2f} ms/tok")
        
        del llm  # Free memory
        time.sleep(2)  # Let GPU cool down
        
        return speed
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 0

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          RTX 4090 PERFORMANCE OPTIMIZATION TEST              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    if not os.path.exists(MODEL_PATH):
        MODEL_PATH = "../../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
        if not os.path.exists(MODEL_PATH):
            print("Model not found!")
            return
    
    print(f"Model: {MODEL_PATH}")
    print(f"Initial GPU: {check_gpu()}\n")
    
    # Test configurations
    configs = [
        # Default (what you're using now)
        ("Default (n_gpu_layers=-1)", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 512,
            "n_threads": 8
        }),
        
        # Smaller context (less memory pressure)
        ("Smaller context (4K)", {
            "n_gpu_layers": -1,
            "n_ctx": 4096,
            "n_batch": 512,
            "n_threads": 8
        }),
        
        # Smaller batch size
        ("Smaller batch (256)", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 256,
            "n_threads": 8
        }),
        
        # Larger batch size
        ("Larger batch (1024)", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 1024,
            "n_threads": 8
        }),
        
        # Fewer CPU threads
        ("Fewer threads (4)", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 512,
            "n_threads": 4
        }),
        
        # Single thread (minimize CPU overhead)
        ("Single thread", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 512,
            "n_threads": 1
        }),
        
        # Flash attention (if supported)
        ("Flash Attention", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 512,
            "n_threads": 8,
            "use_mmap": False,
            "use_mlock": True
        }),
        
        # Tensor cores (if supported)
        ("Force MMQ off", {
            "n_gpu_layers": -1,
            "n_ctx": 8192,
            "n_batch": 512,
            "n_threads": 8,
            "tensor_split": None,
            "mul_mat_q": False
        })
    ]
    
    results = []
    for name, config in configs:
        speed = test_configuration(name, **config)
        results.append((name, speed))
        print(f"\nResult: {speed:.1f} tokens/sec")
    
    # Summary
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    
    results.sort(key=lambda x: x[1], reverse=True)
    for name, speed in results:
        bar = "█" * int(speed / 2)
        print(f"{name:30} {speed:6.1f} tok/s {bar}")
    
    best = results[0]
    print(f"\n🏆 BEST: {best[0]} at {best[1]:.1f} tokens/sec")
    
    if best[1] < 50:
        print("\n⚠️  PERFORMANCE ISSUE DETECTED!")
        print("Expected: 50-100+ tokens/sec on RTX 4090")
        print("Actual: {:.1f} tokens/sec".format(best[1]))
        print("\nPossible causes:")
        print("- Power limit throttling (check nvidia-smi -pl)")
        print("- Thermal throttling (check GPU temperature)")
        print("- PCIe bandwidth (check if GPU is in x16 slot)")
        print("- Windows GPU scheduling issues")
        print("- Old llama-cpp-python version")

if __name__ == "__main__":
    main()