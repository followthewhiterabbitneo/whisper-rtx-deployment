#!/usr/bin/env python3
"""
Test actual Whisper turbo speed on RTX 4090
"""

import time
from faster_whisper import WhisperModel

print("Testing Whisper turbo speed...")

# Load model
model = WhisperModel(
    "models/faster-whisper-large-v3-turbo-ct2",
    device="cuda", 
    compute_type="int8_float16"
)

# Test file
test_file = "test_audio.wav"  # Put any test file here

# Warm up
print("\nWarm-up run...")
segments, info = model.transcribe(test_file, beam_size=1)
list(segments)  # Force evaluation

# Actual test
print("\nSpeed test...")
start = time.time()

segments, info = model.transcribe(
    test_file,
    beam_size=1,
    best_of=1,
    temperature=0.0,
    condition_on_previous_text=False,
    vad_filter=True
)

# Get full text
text = " ".join([s.text for s in segments])
elapsed = time.time() - start

print(f"\nResults:")
print(f"- Audio duration: {info.duration:.1f} seconds")
print(f"- Transcription time: {elapsed:.1f} seconds") 
print(f"- Speed: {info.duration/elapsed:.1f}x real-time")
print(f"- Text length: {len(text)} characters")
print(f"\nFor 1518 recordings (~4500 minutes):")
print(f"- At this speed: {4500*60/info.duration*elapsed/3600:.1f} hours")