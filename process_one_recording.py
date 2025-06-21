#!/usr/bin/env python3
"""
Process ONE Recording - First Principles
1. Copy file from s40vpsoxweb002
2. Transcribe with Whisper
3. Show results
"""

import os
import sys
import subprocess
import tempfile
import time
from datetime import datetime

print("=" * 60)
print("PROCESS ONE RECORDING - First Principles")
print("=" * 60)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"
TARGET_FILE = "20250620_145645_LOLW.wav"
REMOTE_PATH = f"{REMOTE_BASE}/audio/2025/06/20/14/{TARGET_FILE}"

# Step 1: Copy the file
print("\n1. COPYING FILE VIA SSH")
print("-" * 30)

# Create temp directory
temp_dir = tempfile.mkdtemp(prefix="scream_")
local_file = os.path.join(temp_dir, TARGET_FILE)

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

print(f"Processing {TARGET_FILE}...")
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

output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)

transcript_file = os.path.join(output_dir, f"{TARGET_FILE}.txt")
with open(transcript_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(full_transcript))

print(f"✓ Saved to: {transcript_file}")

# Step 5: Show preview
print("\n5. TRANSCRIPT PREVIEW")
print("-" * 30)

print("First 500 characters:")
preview = " ".join(full_transcript)[:500]
print(preview)
print("...")

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

# Look for names
print("\nSearching for names...")
# Simple pattern for "my name is X" or "this is X"
name_patterns = [
    r'my name is (\w+)',
    r'this is (\w+)',
    r'speaking with (\w+)',
]

names = []
for pattern in name_patterns:
    matches = re.findall(pattern, all_text)
    names.extend(matches)

if names:
    print(f"✓ Names mentioned: {', '.join(set(names))}")

# Step 7: Cleanup
print("\n7. CLEANUP")
print("-" * 30)

os.remove(local_file)
os.rmdir(temp_dir)
print("✓ Temp files cleaned up")

print("\n" + "=" * 60)
print("✅ PROCESSING COMPLETE!")
print(f"   Full transcript saved to: {transcript_file}")
print(f"   Total time: {time.time() - start_time:.1f}s")
print("=" * 60)