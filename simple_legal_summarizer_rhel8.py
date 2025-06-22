#!/usr/bin/env python3
"""
Simple legal summarizer using transformers with a model that works on RHEL8
This uses BART or T5 which are more compatible with older systems
"""
import os
import sys
from pathlib import Path

def create_legal_summary_with_bart():
    """Use BART model for summarization - compatible with older transformers"""
    print("=== Legal Summary Generator (BART) ===")
    
    try:
        from transformers import pipeline
        print("✓ Transformers available")
    except ImportError:
        print("ERROR: transformers not found")
        return
    
    # Path to Eric Rawlins transcript
    transcript_path = Path("/moneyball/whisper-rtx-deployment/test_output/20250620_145645_LOLW.wav.txt")
    
    # Check if transcript exists locally
    if not transcript_path.exists():
        # Try local test file
        transcript_path = Path("test_transcript.txt")
        if not transcript_path.exists():
            print(f"Creating sample transcript at {transcript_path}")
            sample_text = """This is a recorded call between Eric Rawlins and a customer service representative 
            regarding a loan modification request. Mr. Rawlins is inquiring about the status of his 
            application submitted on June 1st, 2025. The representative confirms receipt of the 
            application and indicates that it is currently under review by the underwriting department. 
            The expected timeline for a decision is 7-10 business days. Mr. Rawlins expresses concern 
            about making his upcoming payment and asks about forbearance options. The representative 
            explains the temporary payment suspension program and provides instructions for applying online. 
            Documentation requirements include proof of income, bank statements, and a hardship letter. 
            The call concludes with the representative providing a reference number for follow-up."""
            
            with open(transcript_path, 'w') as f:
                f.write(sample_text)
    
    # Read transcript
    print(f"\nReading transcript from: {transcript_path}")
    try:
        with open(transcript_path, 'r') as f:
            transcript_text = f.read()
        print(f"Transcript length: {len(transcript_text)} characters")
    except Exception as e:
        print(f"ERROR reading transcript: {e}")
        return
    
    # Create summarizer
    print("\nInitializing summarizer...")
    print("Using facebook/bart-large-cnn model (smaller, works with older systems)")
    
    try:
        # Use BART CNN model - good for summarization, works with older transformers
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # Force CPU
        )
        print("✓ Summarizer loaded")
        
        # Chunk text if too long (BART has 1024 token limit)
        max_chunk_size = 1024
        if len(transcript_text) > max_chunk_size:
            print(f"\nText too long, using first {max_chunk_size} characters")
            text_to_summarize = transcript_text[:max_chunk_size]
        else:
            text_to_summarize = transcript_text
        
        # Generate summary
        print("\nGenerating legal summary...")
        summary = summarizer(
            text_to_summarize,
            max_length=150,
            min_length=50,
            do_sample=False
        )
        
        legal_summary = summary[0]['summary_text']
        
        # Format as legal summary
        print("\n=== LEGAL CALL SUMMARY ===")
        print(f"Date: June 20, 2025")
        print(f"Participant: Eric Rawlins")
        print(f"Reference: 20250620_145645_LOLW")
        print(f"\nSummary: {legal_summary}")
        
        # Save summary
        output_path = transcript_path.with_suffix('.legal_summary.txt')
        with open(output_path, 'w') as f:
            f.write(f"LEGAL CALL SUMMARY\n")
            f.write(f"==================\n")
            f.write(f"Date: June 20, 2025\n")
            f.write(f"Participant: Eric Rawlins\n")
            f.write(f"Reference: 20250620_145645_LOLW\n")
            f.write(f"Duration: 197 seconds\n\n")
            f.write(f"Summary:\n{legal_summary}\n\n")
            f.write(f"Generated using BART CNN model\n")
        
        print(f"\n✓ Summary saved to: {output_path}")
        
        # Database storage info
        print("\n=== Database Storage ===")
        print("To store in call_transcripts table:")
        print("UPDATE recordings SET summary = '<summary>' WHERE orkUid = '20250620_145645_LOLW';")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTrying alternative approach...")
        
        # Fallback to simple extraction
        print("\n=== Simple Rule-Based Summary ===")
        lines = transcript_text.split('.')[:3]  # First 3 sentences
        simple_summary = '. '.join(lines).strip() + '.'
        print(f"Summary: {simple_summary}")

def main():
    print("=== Legal Call Summarizer for RHEL8 ===")
    print(f"Python: {sys.version}")
    
    create_legal_summary_with_bart()
    
    print("\n=== Next Steps ===")
    print("1. Modify this script to read actual transcripts")
    print("2. Connect to database to store summaries")
    print("3. Process multiple recordings in batch")

if __name__ == "__main__":
    main()