#!/usr/bin/env python3
"""
Generate legal summaries using available Gemma/Llama models on RTX 4090
Works with multiple model formats and auto-detects the best one
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime

def find_best_model():
    """Find the best available model that works with current llama-cpp-python"""
    model_paths = [
        # YOUR ACTUAL MODELS - in order of preference
        # Llama 3 - MOST COMPATIBLE AND WILL WORK!
        "C:/Users/estillmane/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf",
        "../../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf",
        
        # Smaller Gemma models that might work
        "C:/Users/estillmane/models/gemma3-1b-mortgage-v2.gguf",
        "../../models/gemma3-1b-mortgage-v2.gguf",
        "C:/Users/estillmane/models/gemma3-1b-mortgage.gguf",
        "../../models/gemma3-1b-mortgage.gguf",
        "C:/Users/estillmane/models/gemma3-1b.gguf",
        "../../models/gemma3-1b.gguf",
        "C:/Users/estillmane/models/nekoprb-gemma-2b.gguf",
        "../../models/nekoprb-gemma-2b.gguf",
        
        # The gemma3 12B (probably won't work but worth trying)
        "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"
    ]
    
    for path in model_paths:
        if os.path.exists(path):
            print(f"Found model: {path}")
            return path
    
    # If no model found, list what's actually there
    print("\nNo compatible model found. Available models:")
    for root, dirs, files in os.walk("models"):
        for file in files:
            if file.endswith('.gguf'):
                print(f"  - {os.path.join(root, file)}")
    
    return None

def create_legal_prompt(transcript, model_type="gemma"):
    """Create legal summary prompt based on model type"""
    
    if "llama" in model_type.lower():
        # Llama format
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary.<|eot_id|><|start_header_id|>user<|end_header_id|>

Create a legal brief summary of this call transcript with these sections:

1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FACTS (bullet points with loan amounts, rates, dates, names)
3. PARTIES INVOLVED
4. MAIN DISCUSSION POINTS
5. ACTION ITEMS/AGREEMENTS
6. COMPLIANCE NOTES

TRANSCRIPT:
{transcript[:15000]}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
    else:
        # Gemma format
        return f"""<start_of_turn>user
You are a legal assistant specializing in mortgage and loan documentation. Create a professional legal brief summary of this call transcript.

Format your response EXACTLY like this:

**1. EXECUTIVE SUMMARY:**
[2-3 sentences summarizing the entire call]

**2. KEY FACTS:**
* **Loan Amount:** $XXX,XXX
* **Interest Rate:** X.XX%
* **Loan Number:** [if mentioned]
* **Property Address:** [if mentioned]
* **Key Dates:** [any important dates]
* [other critical facts]

**3. PARTIES INVOLVED:**
* **[Party 1]:** [Role and details]
* **[Party 2]:** [Role and details]

**4. MAIN DISCUSSION POINTS:**
* [Main topic 1]
* [Main topic 2]
* [Main topic 3]

**5. ACTION ITEMS/AGREEMENTS:**
* [Action 1]
* [Action 2]

**6. COMPLIANCE NOTES:**
* [Any regulatory concerns]
* [Documentation requirements]
* [Timing issues]

TRANSCRIPT:
{transcript[:15000]}
<end_of_turn>
<start_of_turn>model"""

def generate_summary(transcript_path):
    """Generate legal summary for a transcript"""
    
    # Read transcript
    print(f"\nReading transcript: {transcript_path}")
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            transcript = f.read()
        print(f"✓ Read {len(transcript)} characters")
    except Exception as e:
        print(f"❌ Error reading transcript: {e}")
        return
    
    # Find best model
    model_path = find_best_model()
    if not model_path:
        print("\n❌ No compatible model found!")
        print("Please ensure you have a Gemma 2 or Llama 3 model in the models/ directory")
        return
    
    # Determine model type
    model_type = "llama" if "llama" in model_path.lower() else "gemma"
    
    # Load model
    try:
        from llama_cpp import Llama
        
        print(f"\nLoading {model_type} model...")
        print("Using GPU acceleration on RTX 4090...")
        
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,      # Use all GPU layers
            n_ctx=16384,          # 16K context
            n_batch=512,
            n_threads=8,
            verbose=False         # Less verbose output
        )
        
        print("✓ Model loaded successfully!")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nTrying CPU-only mode...")
        
        try:
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=0,   # CPU only
                n_ctx=8192,       # Smaller context for CPU
                n_threads=16,     # More CPU threads
                verbose=False
            )
            print("✓ Model loaded in CPU mode")
        except Exception as e2:
            print(f"❌ Failed to load model: {e2}")
            return
    
    # Create prompt
    prompt = create_legal_prompt(transcript, model_type)
    
    # Generate summary
    print("\n🤖 Generating legal summary...")
    print("This may take 30-60 seconds...\n")
    
    start_time = time.time()
    
    try:
        # Set stop tokens based on model type
        if model_type == "llama":
            stop_tokens = ["<|eot_id|>", "<|end_of_text|>"]
        else:
            stop_tokens = ["<end_of_turn>", "<start_of_turn>"]
        
        response = llm(
            prompt,
            max_tokens=2048,
            temperature=0.1,      # Low temp for accuracy
            top_p=0.9,
            stop=stop_tokens,
            echo=False
        )
        
        elapsed = time.time() - start_time
        summary = response['choices'][0]['text'].strip()
        
        # Display results
        print("="*80)
        print("LEGAL BRIEF SUMMARY")
        print("="*80)
        print(summary)
        print("="*80)
        print(f"\n⏱️  Generation time: {elapsed:.1f} seconds")
        print(f"📊 Tokens generated: {response['usage']['completion_tokens']}")
        print(f"⚡ Speed: {response['usage']['completion_tokens']/elapsed:.1f} tokens/sec")
        
        # Save output
        output_dir = Path("legal_summaries")
        output_dir.mkdir(exist_ok=True)
        
        # Create filename from input
        base_name = Path(transcript_path).stem
        output_file = output_dir / f"{base_name}_legal_summary.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Legal Brief Summary - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Model: {Path(model_path).name}\n")
            f.write(f"Transcript: {transcript_path}\n")
            f.write("="*80 + "\n\n")
            f.write(summary)
        
        print(f"\n✅ Saved to: {output_file}")
        
        # Also create HTML version
        html_file = output_dir / f"{base_name}_legal_summary.html"
        
        # Format summary for HTML outside f-string
        html_summary = summary.replace('**', '<strong>').replace('\n', '<br>\n')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Legal Brief - {base_name}</title>
    <style>
        body {{ font-family: 'Times New Roman', serif; max-width: 800px; margin: 40px auto; line-height: 1.6; }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #1a1a1a; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        strong {{ color: #2c3e50; }}
        ul {{ margin: 10px 0; padding-left: 30px; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>Legal Brief Summary</h1>
    <div class="meta">
        Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
        Transcript: {Path(transcript_path).name}
    </div>
    {html_summary}
</body>
</html>""")
        
        print(f"✅ HTML version: {html_file}")
        
    except Exception as e:
        print(f"\n❌ Error generating summary: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        GEMMA/LLAMA LEGAL SUMMARY GENERATOR FOR RTX 4090      ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    else:
        # Try to find a transcript
        print("No transcript specified. Looking for transcripts...")
        
        # Check common locations
        possible_paths = [
            "C:\\transcripts\\2025\\06\\02\\20250602_115752_IPBU.txt",
            "transcriptions\\*.txt",
            "test_output\\*.txt"
        ]
        
        transcript_path = input("\nEnter transcript path: ").strip()
        if not transcript_path:
            print("❌ No transcript path provided!")
            return
    
    # Clean up path
    transcript_path = transcript_path.strip('"')
    
    if not os.path.exists(transcript_path):
        print(f"❌ Transcript not found: {transcript_path}")
        return
    
    generate_summary(transcript_path)

if __name__ == "__main__":
    main()