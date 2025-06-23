#!/usr/bin/env python3
"""
WORKING CPU VERSION - Generates excellent legal summaries at 14-21 tokens/sec
This is the version that works perfectly, just renamed to indicate it's using CPU
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime

# YOUR WORKING MODEL PATH
MODEL_PATH = "C:/Users/estillmane/models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

def create_legal_prompt(transcript):
    """Create legal summary prompt for Llama 3"""
    
    return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a legal assistant specializing in mortgage and loan documentation. You create professional legal briefs.<|eot_id|><|start_header_id|>user<|end_header_id|>

Create a legal brief summary of this call transcript. Use this EXACT format:

**1. EXECUTIVE SUMMARY:**
Write 2-3 sentences summarizing the entire call, including the main purpose and outcome.

**2. KEY FACTS:**
• **Loan Amount:** $XXX,XXX (if mentioned)
• **Interest Rate:** X.XX% (if mentioned)
• **Loan Number:** [number] (if mentioned)
• **Property Address:** [address] (if mentioned)
• **Important Dates:** [dates] (if mentioned)
• **Other Key Numbers:** [any other important numbers]

**3. PARTIES INVOLVED:**
• **[Name/Company]:** [Their role] (e.g., UWM Representative, Broker, Borrower)
• **[Name/Company]:** [Their role]

**4. MAIN DISCUSSION POINTS:**
• [First main topic discussed]
• [Second main topic discussed]
• [Third main topic discussed]
• [Additional topics as needed]

**5. ACTION ITEMS/AGREEMENTS:**
• [What was agreed to be done]
• [Who will do what]
• [Any deadlines mentioned]

**6. COMPLIANCE NOTES:**
• **[Compliance Issue]:** [Details about any regulatory concerns]
• **Documentation Requirements:** [What documents are needed]
• **Timing Requirements:** [Any critical dates or deadlines]
• **Risk Factors:** [Any potential issues identified]

TRANSCRIPT:
{transcript[:15000]}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

I'll analyze this transcript and create a professional legal brief summary.

**1. EXECUTIVE SUMMARY:**"""

def generate_summary(transcript_path):
    """Generate legal summary using Llama 3"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        LLAMA 3 8B LEGAL SUMMARY GENERATOR (CPU VERSION)      ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Check model exists
    if not os.path.exists(MODEL_PATH):
        alt_path = "../../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
        if os.path.exists(alt_path):
            model_path = alt_path
        else:
            print(f"❌ Model not found at: {MODEL_PATH}")
            print(f"❌ Also checked: {alt_path}")
            return
    else:
        model_path = MODEL_PATH
    
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
    
    # Load model
    try:
        from llama_cpp import Llama
        
        print("\n🚀 Loading Llama 3 8B Instruct model...")
        print("   Note: This appears to be using CPU (14-21 tokens/sec)")
        
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,      # Still trying to use GPU
            n_ctx=16384,          # 16K context
            n_batch=512,
            n_threads=8,
            verbose=False
        )
        
        print("✅ Model loaded successfully!\n")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Create prompt
    prompt = create_legal_prompt(transcript)
    
    # Generate
    print("🤖 Generating legal brief summary...")
    print("⏳ This will take 30-60 seconds...\n")
    
    start_time = time.time()
    
    try:
        response = llm(
            prompt,
            max_tokens=2048,
            temperature=0.1,      # Very low for accuracy
            top_p=0.9,
            stop=["<|eot_id|>", "<|end_of_text|>", "\n\n**7."],
            echo=False
        )
        
        elapsed = time.time() - start_time
        
        # Get the generated text
        generated = response['choices'][0]['text'].strip()
        
        # Complete summary (prompt already has the start)
        full_summary = "**1. EXECUTIVE SUMMARY:**\n" + generated
        
        # Display
        print("="*80)
        print("LEGAL BRIEF SUMMARY")
        print("="*80)
        print(full_summary)
        print("="*80)
        print(f"\n⏱️  Generation time: {elapsed:.1f} seconds")
        print(f"📊 Tokens: {response['usage']['completion_tokens']}")
        print(f"⚡ Speed: {response['usage']['completion_tokens']/elapsed:.1f} tokens/sec")
        print("\n⚠️  Note: Running at CPU speeds (14-21 tok/s instead of 50-100)")
        
        # Save outputs
        output_dir = Path("legal_summaries")
        output_dir.mkdir(exist_ok=True)
        
        base_name = Path(transcript_path).stem
        
        # Text version
        output_file = output_dir / f"{base_name}_llama3_legal_summary_CPU.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Legal Brief Summary - Llama 3 8B Instruct (CPU Version)\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Transcript: {transcript_path}\n")
            f.write("="*80 + "\n\n")
            f.write(full_summary)
        
        print(f"\n✅ Saved to: {output_file}")
        
        # HTML version
        html_file = output_dir / f"{base_name}_llama3_legal_summary_CPU.html"
        html_content = full_summary.replace('**', '<strong>').replace('\n', '<br>\n')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Legal Brief - {base_name} (CPU)</title>
    <style>
        body {{ 
            font-family: 'Times New Roman', serif; 
            max-width: 800px; 
            margin: 40px auto; 
            line-height: 1.8;
            color: #2c3e50;
        }}
        h1 {{ 
            color: #1a1a1a; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px; 
        }}
        strong {{ 
            color: #2c3e50; 
            font-size: 16px;
        }}
        ul {{ 
            margin: 15px 0; 
            padding-left: 30px; 
        }}
        li {{
            margin: 8px 0;
        }}
        .meta {{ 
            color: #7f8c8d; 
            font-size: 14px; 
            margin-bottom: 30px;
            font-style: italic;
        }}
        .section {{
            margin: 25px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .warning {{
            background: #fff3cd;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Legal Brief Summary (CPU Version)</h1>
    <div class="meta">
        Generated by Llama 3 8B Instruct on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
        Transcript: {Path(transcript_path).name}
    </div>
    <div class="warning">
        ⚠️ This was generated using CPU (14-21 tokens/sec). GPU version should be 50-100 tokens/sec.
    </div>
    <div class="section">
        {html_content}
    </div>
</body>
</html>""")
        
        print(f"✅ HTML version: {html_file}")
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(str(html_file))
            print("\n🌐 Opening in browser...")
        except:
            pass
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    else:
        print("Usage: python llama3_legal_summary_CPU.py <transcript_path>")
        print("\nExample:")
        print('python llama3_legal_summary_CPU.py "C:\\transcripts\\2025\\06\\02\\20250602_115752_IPBU.txt"')
        return
    
    # Clean path
    transcript_path = transcript_path.strip('"')
    
    if not os.path.exists(transcript_path):
        print(f"❌ Transcript not found: {transcript_path}")
        return
    
    generate_summary(transcript_path)

if __name__ == "__main__":
    main()