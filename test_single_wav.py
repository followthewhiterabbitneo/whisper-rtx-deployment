#!/usr/bin/env python3
"""
Test single WAV file to verify format
Run this on RTX 4090 with one of your 13 files
"""

import sys
import wave
from faster_whisper import WhisperModel

def test_wav_file(wav_file):
    """Test a single WAV file from your loan timeline"""
    print(f"Testing: {wav_file}")
    print("="*60)
    
    # 1. Check format
    try:
        with wave.open(wav_file, 'rb') as w:
            print(f"✅ Standard WAV readable")
            print(f"   Channels: {w.getnchannels()}")
            print(f"   Sample rate: {w.getframerate()} Hz")
            print(f"   Sample width: {w.getsampwidth()} bytes")
            print(f"   Duration: {w.getnframes() / w.getframerate():.1f} seconds")
    except Exception as e:
        print(f"❌ Wave module error: {e}")
        print("   This might be μ-law or compressed format")
    
    # 2. Test with Whisper (this should work regardless)
    print("\n🎤 Testing with Whisper...")
    
    model = WhisperModel(
        "models/faster-whisper-large-v3-turbo-ct2",
        device="cuda",
        compute_type="int8_float16"
    )
    
    segments, info = model.transcribe(
        wav_file,
        beam_size=5,
        language="en",
        vad_filter=True
    )
    
    # Get first few segments
    count = 0
    for seg in segments:
        print(f"\n[{seg.start:.1f}s - {seg.end:.1f}s]")
        print(f"  {seg.text.strip()}")
        count += 1
        if count >= 3:
            break
    
    print(f"\n✅ Whisper transcribed successfully!")
    print(f"   Total duration: {info.duration:.1f}s")
    print(f"   Language: {info.language}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_single_wav.py <one_of_your_13_files.wav>")
        print("\nExample:")
        print("  python test_single_wav.py wav_batch_download\\loan_call_001.wav")
        sys.exit(1)
    
    test_wav_file(sys.argv[1])