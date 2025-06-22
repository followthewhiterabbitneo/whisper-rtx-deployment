#!/usr/bin/env python3
"""
Summary script that monitors GPU usage and uses shorter chunks
"""
import subprocess
import os
import time
import threading

# Force GPU
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['OLLAMA_HOME'] = '/moneyball/ollama'
os.environ['OLLAMA_MODELS'] = '/moneyball/ollama/models'

def monitor_gpu():
    """Monitor GPU usage in background"""
    while getattr(monitor_gpu, 'running', True):
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            print(f"[GPU Monitor] {result.stdout.strip()}")
        time.sleep(2)

def summarize_chunk(text, max_length=500):
    """Summarize a smaller chunk of text"""
    prompt = f"Summarize this concisely:\n{text[:max_length]}"
    
    print(f"Processing {len(prompt)} characters...")
    start = time.time()
    
    result = subprocess.run(
        ["ollama", "run", "gemma2-legal", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=120
    )
    
    elapsed = time.time() - start
    print(f"Response time: {elapsed:.1f}s")
    
    if elapsed > 10:
        print("⚠️  Slow response - may be using CPU")
    
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"

def create_legal_summary_fast():
    """Create summary with GPU monitoring"""
    print("=== GPU-Accelerated Legal Summary ===")
    
    # Start GPU monitor
    monitor_gpu.running = True
    monitor_thread = threading.Thread(target=monitor_gpu)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Create or read transcript
    transcript_path = "/moneyball/whisper-rtx-deployment/eric_rawlins_transcript.txt"
    if not os.path.exists(transcript_path):
        print("Creating test transcript...")
        test_text = """Date: June 20, 2025
Eric Rawlins called about loan modification status.
Application submitted June 1st. Under review.
Decision expected in 7-10 days. Forbearance offered.
Reference: SR-2025-0620-3847"""
        with open(transcript_path, 'w') as f:
            f.write(test_text)
    
    with open(transcript_path, 'r') as f:
        transcript = f.read()
    
    print(f"\nTranscript length: {len(transcript)} chars")
    
    # Process in chunks for speed
    print("\n1. Key Information Extraction...")
    key_info = summarize_chunk(transcript, 800)
    
    print("\n2. Creating Legal Format...")
    legal_prompt = f"Format as legal summary:\n{key_info[:300]}"
    legal_summary = summarize_chunk(legal_prompt, 500)
    
    # Stop monitor
    monitor_gpu.running = False
    time.sleep(1)
    
    # Save result
    output = f"""LEGAL SUMMARY (GPU Accelerated)
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
===================================

{legal_summary}

Key Points:
{key_info}

Source: {transcript_path}
"""
    
    output_path = transcript_path.replace('.txt', '_gpu_summary.txt')
    with open(output_path, 'w') as f:
        f.write(output)
    
    print(f"\n✓ Saved to: {output_path}")
    print("\nSummary Preview:")
    print(legal_summary[:200] + "...")
    
    # Check if GPU was used
    print("\n=== Performance Analysis ===")
    subprocess.run(["nvidia-smi"])

if __name__ == "__main__":
    try:
        create_legal_summary_fast()
    except subprocess.TimeoutExpired:
        print("\nTIMEOUT! Ollama is not using GPU properly.")
        print("\nTry:")
        print("1. pkill ollama")
        print("2. nvidia-smi  # Ensure GPU is free")
        print("3. CUDA_VISIBLE_DEVICES=0 ollama serve &")
        print("4. Run this script again")