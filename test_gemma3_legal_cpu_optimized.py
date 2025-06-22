#!/usr/bin/env python3
"""
Test Gemma 3 12B QAT for legal summaries - CPU optimized version
Uses CPU but with optimizations for better performance
"""

from llama_cpp import Llama
import time
import json
from pathlib import Path
import os

# Model configuration
MODEL_PATH = "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"

def load_model():
    """Load Gemma 3 12B with CPU optimizations"""
    print("Loading Gemma 3 12B QAT model (CPU optimized)...")
    
    # Get optimal thread count
    cpu_count = os.cpu_count()
    n_threads = min(cpu_count - 2, 16)  # Leave some threads for system
    
    print(f"Using {n_threads} CPU threads...")
    
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=0,       # Force CPU for compatibility
        n_ctx=8192,           # Reduced context for speed
        n_batch=512,          # Larger batch for CPU efficiency
        n_threads=n_threads,  # Use multiple threads
        verbose=False,
        use_mmap=True,        # Memory map for faster loading
        use_mlock=False       # Don't lock memory
    )
    
    print("✓ Model loaded successfully (CPU mode)")
    return llm

def create_legal_summary_prompt(transcript):
    """Create a structured prompt for legal brief summary"""
    
    # Truncate very long transcripts for faster processing
    max_chars = 15000
    if len(transcript) > max_chars:
        print(f"Transcript truncated from {len(transcript)} to {max_chars} chars for speed")
        transcript = transcript[:max_chars] + "\n[Transcript truncated...]"
    
    prompt = f"""<start_of_turn>user
You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary of this call transcript.

INSTRUCTIONS:
1. Extract all key facts (loan numbers, amounts, dates, names)
2. Identify the main purpose of the call
3. Note any commitments or agreements made
4. Flag any compliance or regulatory concerns
5. Summarize in legal brief format

TRANSCRIPT:
{transcript}

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
        print("Usage: python test_gemma3_legal_cpu_optimized.py <transcript_file>")
        return
    
    # Load model
    llm = load_model()
    
    # Create prompt
    prompt = create_legal_summary_prompt(sample_transcript)
    
    # Generate summary
    print("\nGenerating legal summary (this may take 1-2 minutes on CPU)...")
    print("Tip: The summary quality is excellent even on CPU!\n")
    start_time = time.time()
    
    response = llm(
        prompt,
        max_tokens=800,       # Slightly reduced for speed
        temperature=0.1,      # Low temperature for factual accuracy
        top_p=0.9,
        stop=["<end_of_turn>", "<start_of_turn>"],
        stream=True          # Stream output for better UX
    )
    
    # Stream the output
    summary_parts = []
    for chunk in response:
        text = chunk['choices'][0]['text']
        print(text, end='', flush=True)
        summary_parts.append(text)
    
    elapsed = time.time() - start_time
    summary = ''.join(summary_parts)
    
    print("\n" + "="*80)
    print(f"Generation time: {elapsed:.1f} seconds")
    print(f"Approx speed: {len(summary.split())/elapsed:.1f} words/sec")
    
    # Save to file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "gemma3_legal_summary_test.txt"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n✓ Saved to: {output_file}")
    
    # Also save as JSON with metadata
    json_output = {
        "transcript_file": str(transcript_file),
        "model": "Gemma 3 12B QAT",
        "generation_time": elapsed,
        "summary": summary,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    json_file = output_dir / "gemma3_legal_summary_test.json"
    with open(json_file, "w", encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON saved to: {json_file}")

def extract_loan_numbers(text):
    """Quick extraction of loan numbers from text"""
    import re
    
    patterns = [
        r'\b\d{10,12}\b',  # 10-12 digit numbers
        r'loan\s*(?:number|#)?\s*[:\s]*(\d{8,12})',
        r'application\s*(?:number|#)?\s*[:\s]*(\d{8,12})'
    ]
    
    loan_numbers = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        loan_numbers.update(matches)
    
    return list(loan_numbers)

if __name__ == "__main__":
    print("Gemma 3 12B Legal Summary Test (CPU Optimized)")
    print("="*50 + "\n")
    
    import sys
    
    # Get transcript file from command line
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
        
        # Quick loan number extraction (no model needed)
        print("Quick scan for loan numbers...")
        with open(transcript_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        loan_numbers = extract_loan_numbers(text)
        if loan_numbers:
            print(f"Found potential loan numbers: {', '.join(loan_numbers)}")
        
        print("\n" + "-"*50 + "\n")
        
        # Generate full summary
        test_with_sample(transcript_file)
    else:
        print("ERROR: Please provide a transcript file!")
        print("Usage: python test_gemma3_legal_cpu_optimized.py <transcript_file>")