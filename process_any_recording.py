#!/usr/bin/env python3
"""
Process ANY Recording - Flexible version
Usage: python process_any_recording.py <orkuid>
Example: python process_any_recording.py 20250620_145645_LOLW
"""

import os
import sys
import subprocess
import tempfile
import time
from datetime import datetime

if len(sys.argv) < 2:
    print("Usage: python process_any_recording.py <orkuid>")
    print("Example: python process_any_recording.py 20250620_145645_LOLW")
    sys.exit(1)

ORKUID = sys.argv[1]

print("=" * 60)
print(f"PROCESS RECORDING: {ORKUID}")
print("=" * 60)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

# Parse orkuid to build path
# Format: YYYYMMDD_HHMMSS_XXXX
if len(ORKUID) < 15:
    print(f"✗ Invalid orkuid format: {ORKUID}")
    sys.exit(1)

year = ORKUID[:4]
month = ORKUID[4:6]
day = ORKUID[6:8]
hour = ORKUID[9:11]
filename = f"{ORKUID}.wav"

REMOTE_PATH = f"{REMOTE_BASE}/audio/{year}/{month}/{day}/{hour}/{filename}"

# Step 1: Copy the file
print("\n1. COPYING FILE VIA SSH")
print("-" * 30)

# Create temp directory
temp_dir = tempfile.mkdtemp(prefix="scream_")
local_file = os.path.join(temp_dir, filename)

print(f"Remote: {REMOTE_PATH}")
print(f"Local:  {local_file}")

# SCP the file
scp_cmd = ['scp', f'{SSH_USER}@{SSH_HOST}:{REMOTE_PATH}', local_file]
print(f"\nCopying...")
start_time = time.time()

result = subprocess.run(scp_cmd, capture_output=True, text=True)

if result.returncode == 0 and os.path.exists(local_file):
    copy_time = time.time() - start_time
    file_size = os.path.getsize(local_file)
    print(f"✓ File copied in {copy_time:.1f}s")
    print(f"  Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
else:
    print(f"✗ Copy failed: {result.stderr}")
    sys.exit(1)

# Step 2: Load Whisper and transcribe
print("\n2. LOADING WHISPER MODEL")
print("-" * 30)

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("✗ faster_whisper not installed")
    print("  Run: pip install faster-whisper")
    sys.exit(1)

model_path = "models/faster-whisper-large-v3-turbo-ct2"
if not os.path.exists(model_path):
    print(f"✗ Model not found at {model_path}")
    print("  Run download script first")
    sys.exit(1)

print(f"Loading model from {model_path}...")
model = WhisperModel(model_path, device="cuda", compute_type="int8_float16")
print("✓ Model loaded")

# Step 3: Transcribe
print("\n3. TRANSCRIBING AUDIO")
print("-" * 30)

print(f"Processing {filename}...")
start_time = time.time()

segments, info = model.transcribe(local_file, beam_size=5)

# Collect all text
full_transcript = []
for segment in segments:
    full_transcript.append(segment.text.strip())

transcribe_time = time.time() - start_time

print(f"✓ Transcription complete in {transcribe_time:.1f}s")
print(f"  Language: {info.language}")
print(f"  Duration: {info.duration:.1f}s")
print(f"  Speed: {info.duration/transcribe_time:.1f}x realtime")

# Step 4: Save transcript
print("\n4. SAVING TRANSCRIPT")
print("-" * 30)

output_dir = "transcriptions"
os.makedirs(output_dir, exist_ok=True)

transcript_file = os.path.join(output_dir, f"{ORKUID}_transcript.txt")
with open(transcript_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(full_transcript))

print(f"✓ Saved to: {transcript_file}")

# Step 5: Generate legal summary (optional)
print("\n5. LEGAL SUMMARY (Optional)")
print("-" * 30)

generate_summary = input("Generate legal summary? (y/n): ").lower().strip() == 'y'

if generate_summary:
    print("Loading Gemma 3 for legal summary...")
    
    # Import and run the legal summary script
    try:
        from test_gemma3_legal import load_model, create_legal_summary_prompt, generate_summary
        
        # Load Gemma model
        llm = load_model()
        
        # Create prompt
        transcript_text = "\n".join(full_transcript)
        prompt = create_legal_summary_prompt(transcript_text[:8000])  # Limit context
        
        # Generate summary
        print("Generating summary...")
        summary = generate_summary(llm, prompt)
        
        # Save summary
        summary_file = os.path.join(output_dir, f"{ORKUID}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✓ Summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"✗ Summary generation failed: {e}")

# Step 6: Extract key information
print("\n6. KEY INFORMATION")
print("-" * 30)

# Join all text for searching
all_text = " ".join(full_transcript).lower()

# Look for loan number
import re
loan_patterns = [
    r'loan\s*(?:number)?\s*[:\s]*(\d{8,12})',
    r'application\s*(?:number)?\s*[:\s]*(\d{8,12})',
]

loan_numbers = []
for pattern in loan_patterns:
    matches = re.findall(pattern, all_text)
    loan_numbers.extend(matches)

if loan_numbers:
    print(f"✓ Loan numbers found: {', '.join(set(loan_numbers))}")
else:
    print("✗ No loan numbers found")

# Step 7: Cleanup
print("\n7. CLEANUP")
print("-" * 30)

os.remove(local_file)
os.rmdir(temp_dir)
print("✓ Temp files cleaned up")

print("\n" + "=" * 60)
print("✅ PROCESSING COMPLETE!")
print(f"   Orkuid: {ORKUID}")
print(f"   Transcript: {transcript_file}")
if generate_summary and 'summary_file' in locals():
    print(f"   Summary: {summary_file}")
print(f"   Total time: {time.time() - start_time:.1f}s")
print("=" * 60)