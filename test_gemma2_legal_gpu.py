#!/usr/bin/env python3
"""
Test Gemma 2 9B for legal summaries - GPU version
Should work with current CUDA llama-cpp-python
"""

from llama_cpp import Llama
import time
import json
from pathlib import Path

# Model configuration - update path after extraction
# Common GGUF variants: Q4_0, Q4_K_M, Q5_K_M, Q8_0
# Update this to match your actual file:
MODEL_PATH = "models/gemma2-9b-it-v1/gemma-2-9b-it-Q5_K_M.gguf"

def load_model():
    """Load Gemma 2 9B with GPU acceleration"""
    print("Loading Gemma 2 9B model...")
    print("This should use GPU acceleration!")
    
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=-1,      # Use all GPU layers
        n_ctx=8192,           # Gemma 2 context window
        n_batch=512,          # Batch size
        n_threads=8,          # CPU threads for non-GPU ops
        verbose=True          # Show GPU usage
    )
    
    print("✓ Model loaded successfully")
    return llm

def create_legal_summary_prompt(transcript):
    """Create a structured prompt for legal brief summary - Gemma 2 format"""
    
    # Gemma 2 uses different prompt format
    prompt = f"""<bos><start_of_turn>user
You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary of this call transcript.

INSTRUCTIONS:
1. Extract all key facts (loan numbers, amounts, dates, names)
2. Identify the main purpose of the call
3. Note any commitments or agreements made
4. Flag any compliance or regulatory concerns
5. Summarize in legal brief format

TRANSCRIPT:
{transcript[:15000]}

Please provide:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FACTS (bullet points)
3. PARTIES INVOLVED
4. MAIN DISCUSSION POINTS
5. ACTION ITEMS/AGREEMENTS
6. COMPLIANCE NOTES (if any)
<end_of_turn>
<start_of_turn>model
"""
    
    return prompt

def test_with_sample(transcript_file=None):
    """Test with a real transcript"""
    
    if transcript_file and Path(transcript_file).exists():
        print(f"Loading transcript from: {transcript_file}")
        with open(transcript_file, 'r', encoding='utf-8') as f:
            sample_transcript = f.read()
    else:
        print("ERROR: No transcript file provided!")
        return
    
    # Load model
    llm = load_model()
    
    # Create prompt
    prompt = create_legal_summary_prompt(sample_transcript)
    
    # Generate summary
    print("\nGenerating legal summary with GPU acceleration...")
    start_time = time.time()
    
    response = llm(
        prompt,
        max_tokens=1024,
        temperature=0.1,
        top_p=0.9,
        stop=["<end_of_turn>", "<start_of_turn>"]
    )
    
    elapsed = time.time() - start_time
    
    # Extract and display results
    summary = response['choices'][0]['text'].strip()
    
    print("\n" + "="*80)
    print("GEMMA 2 9B LEGAL BRIEF SUMMARY")
    print("="*80)
    print(summary)
    print("\n" + "="*80)
    print(f"Generation time: {elapsed:.1f} seconds")
    print(f"Tokens generated: {response['usage']['completion_tokens']}")
    print(f"Speed: {response['usage']['completion_tokens']/elapsed:.1f} tokens/sec")
    
    # Save to file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "gemma2_legal_summary_test.txt", "w", encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n✓ Saved to: {output_dir / 'gemma2_legal_summary_test.txt'}")
    
    # Save comparison file
    comparison = {
        "model": "Gemma 2 9B",
        "gpu_enabled": True,
        "generation_time": elapsed,
        "tokens_per_second": response['usage']['completion_tokens']/elapsed,
        "summary_length": len(summary.split()),
        "summary": summary
    }
    
    with open(output_dir / "gemma2_performance.json", "w", encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

def compare_summaries():
    """Compare Gemma 3 and Gemma 2 summaries"""
    output_dir = Path("test_output")
    
    files = {
        "Gemma 3 12B": output_dir / "gemma3_legal_summary_test.txt",
        "Gemma 2 9B": output_dir / "gemma2_legal_summary_test.txt"
    }
    
    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    
    for model, file in files.items():
        if file.exists():
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"\n{model} - Length: {len(content.split())} words")
            print("-" * 40)
            print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    print("Gemma 2 9B Legal Summary Test (GPU)")
    print("="*40 + "\n")
    
    import sys
    
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
        test_with_sample(transcript_file)
        
        # If both summaries exist, compare them
        if Path("test_output/gemma3_legal_summary_test.txt").exists():
            compare_summaries()
    else:
        print("ERROR: Please provide a transcript file!")
        print("Usage: python test_gemma2_legal_gpu.py <transcript_file>")