#!/usr/bin/env python3
"""
Summarize transcripts using Ollama Gemma model
Creates professional legal summaries
"""
import subprocess
import os
from pathlib import Path
from datetime import datetime

# Ensure Ollama uses /moneyball
os.environ['OLLAMA_HOME'] = '/moneyball/ollama'
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

def query_gemma(prompt, max_tokens=500):
    """Query Gemma model via Ollama"""
    cmd = ["ollama", "run", "gemma2-legal"]
    
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def create_legal_summary(transcript_path):
    """Create a professional legal summary from transcript"""
    
    # Read transcript
    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        print(f"Error: Transcript not found at {transcript_path}")
        return None
    
    transcript = transcript_file.read_text()
    print(f"Processing: {transcript_file.name}")
    print(f"Transcript length: {len(transcript)} characters")
    
    # Create prompt for legal summary
    prompt = f"""You are a legal documentation specialist. Create a professional legal summary from this call transcript.

Include:
1. Call Details (date, duration, participants)
2. Purpose of Call
3. Key Issues Discussed
4. Actions Taken
5. Commitments Made
6. Next Steps
7. Important Deadlines

Transcript:
{transcript[:3000]}  # Limit to first 3000 chars for context window

Professional Legal Summary:"""

    print("\nGenerating legal summary with Gemma 2 9B...")
    summary = query_gemma(prompt)
    
    # Create structured output
    output = f"""LEGAL CALL SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: Gemma 2 9B via Ollama
{'=' * 60}

{summary}

{'=' * 60}
Source: {transcript_file.name}
Generated in: /moneyball/whisper-rtx-deployment/
"""
    
    # Save summary
    output_path = transcript_file.parent / f"{transcript_file.stem}_legal_summary.txt"
    output_path.write_text(output)
    
    print(f"\n✓ Summary saved to: {output_path}")
    print("\n--- SUMMARY PREVIEW ---")
    print(summary[:500] + "..." if len(summary) > 500 else summary)
    
    return summary

def main():
    """Process Eric Rawlins transcript"""
    print("=== Gemma Legal Summary Generator ===")
    print("Using Ollama with Gemma 2 9B model")
    print("")
    
    # First create the test transcript
    create_script = Path("/moneyball/whisper-rtx-deployment/create_test_transcript.py")
    if create_script.exists():
        print("Creating test transcript...")
        subprocess.run(["python3", str(create_script)])
        print("")
    
    # Process the transcript
    transcript_path = "/moneyball/whisper-rtx-deployment/eric_rawlins_transcript.txt"
    
    if not Path(transcript_path).exists():
        print("Test transcript not found. Creating simple one...")
        test_content = """Call Date: June 20, 2025
Participant: Eric Rawlins
Subject: Loan Modification Status

Eric Rawlins called to check on his loan modification application submitted June 1st. 
Application is under review by underwriting. Decision expected in 7-10 business days.
Customer expressed concern about upcoming payment. Agent offered forbearance options.
Reference number: SR-2025-0620-3847"""
        Path(transcript_path).write_text(test_content)
    
    # Generate summary
    summary = create_legal_summary(transcript_path)
    
    if summary:
        print("\n✓ Summary generation complete!")
        print("\nTo process other transcripts:")
        print(f"python3 {__file__} /path/to/transcript.txt")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Process specific file
        create_legal_summary(sys.argv[1])
    else:
        # Process test transcript
        main()