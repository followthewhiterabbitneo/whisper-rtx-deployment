#!/usr/bin/env python3
"""
Legal Summary with GPU monitoring to verify it's actually using the RTX 4090
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# YOUR WORKING MODEL PATH
MODEL_PATH = "C:/Users/estillmane/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

def check_gpu_usage():
    """Check GPU memory and utilization"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            memory, util = result.stdout.strip().split(', ')
            return f"GPU Memory: {memory}MB, Utilization: {util}%"
    except:
        return "GPU monitoring unavailable"
    return "GPU check failed"

def create_legal_prompt(transcript):
    """Create legal summary prompt for Llama 3"""
    
    return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a legal assistant creating professional legal briefs for mortgage loans.<|eot_id|><|start_header_id|>user<|end_header_id|>

Create a legal brief summary with these sections:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FACTS (loan amounts, rates, dates)
3. PARTIES INVOLVED
4. MAIN DISCUSSION POINTS
5. ACTION ITEMS/AGREEMENTS
6. COMPLIANCE NOTES

TRANSCRIPT:
{transcript[:10000]}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

def test_gpu_loading(model_path):
    """Test if GPU is actually being used"""
    print("\n🔍 GPU VERIFICATION TEST")
    print("-" * 60)
    
    # Check before loading
    print(f"Before loading model: {check_gpu_usage()}")
    
    try:
        from llama_cpp import Llama
        
        # Try loading with explicit GPU layers
        print("\nAttempting GPU load with n_gpu_layers=-1...")
        
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,      # All layers on GPU
            n_ctx=8192,
            n_batch=512,
            n_threads=8,
            verbose=True          # VERBOSE to see what's happening!
        )
        
        # Check after loading
        print(f"\nAfter loading model: {check_gpu_usage()}")
        
        # Do a small test generation
        print("\nTesting generation...")
        start = time.time()
        response = llm("Testing GPU acceleration", max_tokens=50)
        elapsed = time.time() - start
        tokens = response['usage']['completion_tokens']
        
        print(f"Generated {tokens} tokens in {elapsed:.2f}s = {tokens/elapsed:.1f} tokens/sec")
        print(f"During generation: {check_gpu_usage()}")
        
        return llm, True
        
    except Exception as e:
        print(f"\n❌ GPU loading failed: {e}")
        print("\nTrying CPU fallback...")
        
        try:
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=0,       # Force CPU
                n_ctx=4096,          # Smaller context for CPU
                n_threads=16,        # More threads for CPU
                verbose=True
            )
            print("✅ Loaded in CPU mode")
            return llm, False
        except Exception as e2:
            print(f"❌ CPU loading also failed: {e2}")
            return None, False

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     LLAMA 3 LEGAL SUMMARY WITH GPU MONITORING               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) < 2:
        print("Usage: python llama3_legal_gpu_monitor.py <transcript_path>")
        return
    
    transcript_path = sys.argv[1].strip('"')
    
    # Check if model exists and determine path
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        alt_path = "../../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
        if os.path.exists(alt_path):
            model_path = alt_path
        else:
            print(f"❌ Model not found at {MODEL_PATH} or {alt_path}!")
            return
    
    print(f"📂 Model: {model_path}")
    print(f"📄 Transcript: {transcript_path}")
    
    # Test GPU loading
    llm, using_gpu = test_gpu_loading(model_path)
    if not llm:
        return
    
    print(f"\n{'🚀 GPU ACCELERATION ACTIVE' if using_gpu else '🐌 CPU MODE (SLOW)'}")
    print("-" * 60)
    
    # Read transcript
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            transcript = f.read()
        print(f"\n✓ Read transcript: {len(transcript)} characters")
    except Exception as e:
        print(f"❌ Error reading transcript: {e}")
        return
    
    # Generate summary
    prompt = create_legal_prompt(transcript)
    
    print("\n🤖 Generating legal brief...")
    print(f"Starting GPU state: {check_gpu_usage()}")
    
    start_time = time.time()
    
    # Monitor GPU during generation
    response = llm(
        prompt,
        max_tokens=1500,
        temperature=0.1,
        top_p=0.9,
        stop=["<|eot_id|>"],
        echo=False
    )
    
    elapsed = time.time() - start_time
    
    print(f"Final GPU state: {check_gpu_usage()}")
    
    # Display results
    summary = response['choices'][0]['text'].strip()
    
    print("\n" + "="*80)
    print("LEGAL BRIEF SUMMARY")
    print("="*80)
    print(summary)
    print("="*80)
    
    tokens = response['usage']['completion_tokens']
    speed = tokens/elapsed
    
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   Generation time: {elapsed:.1f} seconds")
    print(f"   Tokens generated: {tokens}")
    print(f"   Speed: {speed:.1f} tokens/sec")
    
    if using_gpu:
        if speed > 50:
            print(f"   ✅ GPU acceleration confirmed! (>50 tok/s)")
        elif speed > 20:
            print(f"   ⚠️  Partial GPU usage (20-50 tok/s)")
        else:
            print(f"   ❌ GPU might not be working properly (<20 tok/s)")
    else:
        print(f"   🐌 CPU mode (expected ~5-15 tok/s)")
    
    # Save output
    output_dir = Path("legal_summaries")
    output_dir.mkdir(exist_ok=True)
    
    base_name = Path(transcript_path).stem
    output_file = output_dir / f"{base_name}_legal_summary_monitored.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Legal Brief Summary\n")
        f.write(f"Model: Llama 3 8B Instruct\n")
        f.write(f"GPU Mode: {'Yes' if using_gpu else 'No'}\n")
        f.write(f"Speed: {speed:.1f} tokens/sec\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("="*80 + "\n\n")
        f.write(summary)
    
    print(f"\n✅ Saved to: {output_file}")

if __name__ == "__main__":
    main()