#!/usr/bin/env python3
"""
Test Gemma 2 9B with GPU on RHEL8
Run this after setup_gemma2_rhel8.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/moneyball/whisper-rtx-deployment')

try:
    from llama_cpp import Llama
except ImportError:
    print("ERROR: llama-cpp-python not installed")
    print("Run: source /moneyball/gemma-env/bin/activate")
    sys.exit(1)

def test_gemma2():
    print("=== Testing Gemma 2 9B with GPU ===")
    
    # Find the GGUF model
    models_dir = Path("/moneyball/whisper-rtx-deployment/models")
    gguf_files = list(models_dir.rglob("*.gguf"))
    
    if not gguf_files:
        print("ERROR: No GGUF model found!")
        print("Run setup_gemma2_rhel8.py first")
        sys.exit(1)
    
    model_path = str(gguf_files[0])
    print(f"Loading model: {model_path}")
    
    # Initialize with GPU
    try:
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,  # Use all layers on GPU
            n_ctx=4096,
            n_threads=8,
            verbose=True
        )
        print("✓ Model loaded successfully with GPU!")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        print("\nTrying CPU fallback...")
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=0,  # CPU only
            n_ctx=2048,
            n_threads=8
        )
        print("✓ Model loaded on CPU")
    
    # Test generation
    print("\n=== Testing Legal Summary Generation ===")
    
    test_transcript = """
    Attorney: Good morning, Mr. Rawlins. Can you state your name for the record?
    Eric Rawlins: Eric Rawlins.
    Attorney: And you understand you're here regarding the incident on June 15th?
    Eric Rawlins: Yes, I understand.
    Attorney: Can you describe what happened that day?
    Eric Rawlins: I was driving northbound on Highway 101 when another vehicle ran a red light and struck my car.
    Attorney: Were there any witnesses?
    Eric Rawlins: Yes, two people stopped and gave statements to the police.
    """
    
    prompt = f"""<start_of_turn>user
Please provide a concise legal summary of this transcript:

{test_transcript}

Focus on: parties involved, key facts, and any legal issues mentioned.<end_of_turn>
<start_of_turn>model
"""
    
    print("Generating summary...")
    response = llm(
        prompt,
        max_tokens=256,
        temperature=0.7,
        stop=["<end_of_turn>"]
    )
    
    summary = response['choices'][0]['text'].strip()
    print(f"\n=== Generated Summary ===\n{summary}")
    
    # Performance stats
    if 'usage' in response:
        tokens = response['usage']['total_tokens']
        print(f"\n=== Performance ===")
        print(f"Total tokens: {tokens}")
    
    print("\n✓ Test complete!")
    
if __name__ == "__main__":
    test_gemma2()