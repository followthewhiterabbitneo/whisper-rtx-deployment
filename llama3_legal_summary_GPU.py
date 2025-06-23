#!/usr/bin/env python3
"""
GPU VERSION - Force proper GPU usage for 50-100+ tokens/sec
Uses different settings to ensure GPU acceleration works properly
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime
import subprocess

# Set environment variables BEFORE importing llama_cpp
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Force GPU 0
os.environ['LLAMA_CUBLAS'] = '1'  # Force cuBLAS

# YOUR WORKING MODEL PATH
MODEL_PATH = "C:/Users/estillmane/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

def check_gpu():
    """Check GPU status"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "GPU check failed"

def create_legal_prompt(transcript):
    """Create legal summary prompt for Llama 3"""
    
    return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a legal assistant specializing in mortgage and loan documentation.<|eot_id|><|start_header_id|>user<|end_header_id|>

Create a legal brief summary with these exact sections:

**1. EXECUTIVE SUMMARY:** (2-3 sentences)
**2. KEY FACTS:** (bullet points)
**3. PARTIES INVOLVED:**
**4. MAIN DISCUSSION POINTS:**
**5. ACTION ITEMS/AGREEMENTS:**
**6. COMPLIANCE NOTES:**

TRANSCRIPT:
{transcript[:12000]}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

**1. EXECUTIVE SUMMARY:**"""

def generate_summary(transcript_path):
    """Generate legal summary with forced GPU usage"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        LLAMA 3 8B LEGAL SUMMARY GENERATOR (GPU VERSION)      ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print(f"🔧 GPU Settings:")
    print(f"   CUDA_VISIBLE_DEVICES = {os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')}")
    print(f"   LLAMA_CUBLAS = {os.environ.get('LLAMA_CUBLAS', 'not set')}")
    print(f"   Current GPU: {check_gpu()}\n")
    
    # Check model exists
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        alt_path = "../../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
        if os.path.exists(alt_path):
            model_path = alt_path
        else:
            print(f"❌ Model not found!")
            return
    
    print(f"✅ Found model: {model_path}")
    print(f"📄 Processing: {transcript_path}\n")
    
    # Read transcript
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            transcript = f.read()
        print(f"✓ Read transcript: {len(transcript)} characters")
    except Exception as e:
        print(f"❌ Error reading transcript: {e}")
        return
    
    # Load model with GPU-optimized settings
    try:
        from llama_cpp import Llama
        
        print("\n🚀 Loading with GPU-optimized settings...")
        print("   Target: 50-100+ tokens/sec on RTX 4090")
        
        # Try different settings for better GPU performance
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=35,         # Specific layer count instead of -1
            n_ctx=8192,              # 8K context
            n_batch=256,             # Smaller batch for faster generation
            n_threads=1,             # Minimal CPU threads to force GPU
            use_mmap=True,           # Memory mapping
            use_mlock=False,         # Don't lock memory
            seed=42,                 # Deterministic
            f16_kv=True,             # Use float16 for KV cache
            logits_all=False,        # Don't store all logits
            vocab_only=False,        # Load full model
            n_gpu_layers_draft=35,   # Draft model layers if applicable
            verbose=True             # Show what's happening
        )
        
        print("✅ Model loaded with GPU optimization!\n")
        print(f"GPU after load: {check_gpu()}")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nTrying fallback configuration...")
        
        try:
            from llama_cpp import Llama
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=32,      # All layers for 8B model
                n_ctx=4096,           # Smaller context
                n_batch=128,          # Even smaller batch
                n_threads=1,          # Single thread
                verbose=False
            )
            print("✅ Loaded with fallback config")
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return
    
    # Create prompt
    prompt = create_legal_prompt(transcript)
    
    # Generate
    print("\n🤖 Generating legal brief summary...")
    print(f"GPU before generation: {check_gpu()}")
    
    start_time = time.time()
    
    try:
        # Generation settings optimized for speed
        response = llm(
            prompt,
            max_tokens=1500,          # Reasonable limit
            temperature=0.1,          # Low for consistency
            top_p=0.9,
            top_k=40,                 # Limit choices
            repeat_penalty=1.1,       # Avoid repetition
            stop=["<|eot_id|>", "<|end_of_text|>"],
            echo=False,
            stream=False              # No streaming
        )
        
        elapsed = time.time() - start_time
        
        print(f"GPU after generation: {check_gpu()}")
        
        # Get the generated text
        generated = response['choices'][0]['text'].strip()
        
        # Complete summary
        full_summary = "**1. EXECUTIVE SUMMARY:**\n" + generated
        
        # Display
        print("\n" + "="*80)
        print("LEGAL BRIEF SUMMARY")
        print("="*80)
        print(full_summary)
        print("="*80)
        
        tokens = response['usage']['completion_tokens']
        speed = tokens/elapsed
        
        print(f"\n📊 PERFORMANCE:")
        print(f"   Generation time: {elapsed:.1f} seconds")
        print(f"   Tokens: {tokens}")
        print(f"   Speed: {speed:.1f} tokens/sec")
        
        if speed > 50:
            print(f"   ✅ GPU ACCELERATION WORKING! ({speed:.0f} tok/s)")
        elif speed > 30:
            print(f"   ⚠️  Partial GPU usage ({speed:.0f} tok/s)")
        else:
            print(f"   ❌ Still running at CPU speeds ({speed:.0f} tok/s)")
        
        # Save outputs
        output_dir = Path("legal_summaries")
        output_dir.mkdir(exist_ok=True)
        
        base_name = Path(transcript_path).stem
        
        # Text version
        output_file = output_dir / f"{base_name}_llama3_legal_summary_GPU.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Legal Brief Summary - Llama 3 8B (GPU Version)\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Speed: {speed:.1f} tokens/sec\n")
            f.write(f"Transcript: {transcript_path}\n")
            f.write("="*80 + "\n\n")
            f.write(full_summary)
        
        print(f"\n✅ Saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Quick GPU check
    print("Initial GPU check:")
    os.system("nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv,noheader")
    
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    else:
        print("\nUsage: python llama3_legal_summary_GPU.py <transcript_path>")
        return
    
    transcript_path = transcript_path.strip('"')
    
    if not os.path.exists(transcript_path):
        print(f"❌ Transcript not found: {transcript_path}")
        return
    
    generate_summary(transcript_path)

if __name__ == "__main__":
    main()