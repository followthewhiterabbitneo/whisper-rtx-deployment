#!/usr/bin/env python3
"""
SCREENPLAY SIMPLE - For RTX 4090
Uses only existing faster-whisper setup
No new imports needed!
"""

import sys
import os
from faster_whisper import WhisperModel
from datetime import datetime

# Your existing model setup
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"

def transcribe_as_screenplay(audio_file):
    """Transcribe and format as screenplay using existing setup"""
    
    print("🎬 SCREENPLAY TRANSCRIPTION")
    print("=" * 50)
    print(f"📁 Input: {audio_file}")
    print("=" * 50)
    
    # Load model (same as your existing scripts)
    print(f"\n📦 Loading model...")
    model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✅ Model loaded!")
    
    # Transcribe with timestamps
    print("\n🎤 Transcribing...")
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        language="en",
        condition_on_previous_text=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Format as screenplay
    screenplay = []
    screenplay.append("=" * 80)
    screenplay.append("CALL TRANSCRIPT - SCREENPLAY FORMAT")
    screenplay.append(f"File: {os.path.basename(audio_file)}")
    screenplay.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    screenplay.append("=" * 80)
    screenplay.append("")
    
    # Since we can't separate speakers without stereo split,
    # format with timestamps and natural breaks
    for segment in segments:
        timestamp = f"[{segment.start:.1f}s]"
        text = segment.text.strip()
        
        # Add timestamp and text
        screenplay.append(f"{timestamp}")
        screenplay.append(f"{text}")
        screenplay.append("")  # Blank line between segments
    
    # Join all lines
    screenplay_text = "\n".join(screenplay)
    
    # Save output
    output_file = audio_file.replace('.wav', '_screenplay.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(screenplay_text)
    
    print(f"\n✅ Screenplay saved to: {output_file}")
    
    # Show preview
    print("\n" + "=" * 50)
    print("PREVIEW (first 500 chars):")
    print("=" * 50)
    preview = screenplay_text[:500] + "..." if len(screenplay_text) > 500 else screenplay_text
    print(preview)
    
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python screenplay_simple_rtx.py <audio_file.wav>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    transcribe_as_screenplay(audio_file)

if __name__ == "__main__":
    main()