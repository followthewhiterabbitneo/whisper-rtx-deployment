#!/usr/bin/env python3
"""
Test Gemma 3 12B QAT for legal summaries
First principles approach to transcript summarization
"""

from llama_cpp import Llama
import time
import json
from pathlib import Path

# Model configuration
MODEL_PATH = "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"

def load_model():
    """Load Gemma 3 12B with optimal settings for RTX 4090"""
    print("Loading Gemma 3 12B QAT model...")
    print("Attempting to use GPU...")
    
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=-1,      # Use all GPU layers
        n_ctx=32768,          # 32K context (can go up to 128K)
        n_batch=512,          # Batch size for prompt processing
        n_threads=8,          # CPU threads
        verbose=True          # Show loading details to debug GPU
    )
    
    print("✓ Model loaded successfully")
    return llm

def create_legal_summary_prompt(transcript):
    """Create a structured prompt for legal brief summary"""
    
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
        print("Usage: python test_gemma3_legal.py <transcript_file>")
        print("Example: python test_gemma3_legal.py transcriptions/call_12345.txt")
        return
    
    # Load model
    llm = load_model()
    
    # Create prompt
    prompt = create_legal_summary_prompt(sample_transcript)
    
    # Generate summary
    print("\nGenerating legal summary...")
    start_time = time.time()
    
    response = llm(
        prompt,
        max_tokens=1024,
        temperature=0.1,  # Low temperature for factual accuracy
        top_p=0.9,
        stop=["<end_of_turn>", "<start_of_turn>"]
    )
    
    elapsed = time.time() - start_time
    
    # Extract and display results
    summary = response['choices'][0]['text'].strip()
    
    print("\n" + "="*80)
    print("LEGAL BRIEF SUMMARY")
    print("="*80)
    print(summary)
    print("\n" + "="*80)
    print(f"Generation time: {elapsed:.1f} seconds")
    print(f"Tokens generated: {response['usage']['completion_tokens']}")
    print(f"Speed: {response['usage']['completion_tokens']/elapsed:.1f} tokens/sec")
    
    # Save to file
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "gemma3_legal_summary_test.txt", "w") as f:
        f.write(summary)
    
    print(f"\n✓ Saved to: {output_dir / 'gemma3_legal_summary_test.txt'}")

def extract_facts_test():
    """Test structured fact extraction"""
    
    llm = load_model()
    
    prompt = """<start_of_turn>user
Extract the following information from this text and return as JSON:
- loan_number
- customer_name  
- current_rate
- new_rate
- loan_balance
- monthly_savings
- closing_costs

Text: "Mr. Johnson called about loan 123456789012. His current rate is 6.5% with a balance of $425,000. We offered a refinance at 5.25% which saves $312 monthly with $3,500 in closing costs."

Return only valid JSON.
<end_of_turn>
<start_of_turn>model
"""
    
    print("\nTesting structured fact extraction...")
    
    response = llm(
        prompt,
        max_tokens=256,
        temperature=0.1,
        stop=["<end_of_turn>", "<start_of_turn>"]
    )
    
    facts = response['choices'][0]['text'].strip()
    print("\nExtracted facts:")
    print(facts)
    
    # Try to parse as JSON
    try:
        parsed = json.loads(facts)
        print("\n✓ Valid JSON extracted:")
        print(json.dumps(parsed, indent=2))
    except:
        print("\n✗ Failed to parse JSON")

if __name__ == "__main__":
    print("Gemma 3 12B Legal Summary Test")
    print("==============================\n")
    
    import sys
    
    # Get transcript file from command line
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
        test_with_sample(transcript_file)
        
        print("\n" + "="*80 + "\n")
        
        extract_facts_test()
    else:
        print("ERROR: Please provide a transcript file!")
        print("Usage: python test_gemma3_legal.py <transcript_file>")
        print("\nFirst, you need to:")
        print("1. Run: python process_one_recording.py")
        print("2. Or place a transcript in transcriptions/ folder")
        print("3. Then run: python test_gemma3_legal.py transcriptions/your_transcript.txt")