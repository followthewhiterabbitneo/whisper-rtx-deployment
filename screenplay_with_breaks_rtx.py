#!/usr/bin/env python3
"""
SCREENPLAY WITH SPEAKER BREAKS - For RTX 4090
Uses VAD (voice activity detection) to guess speaker changes
No new imports - uses your existing faster-whisper!
"""

import sys
import os
from faster_whisper import WhisperModel
from datetime import datetime

# Your existing model setup
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"

def format_screenplay_with_speakers(audio_file):
    """Format as screenplay with speaker detection based on pauses"""
    
    print("🎬 SCREENPLAY WITH SPEAKER DETECTION")
    print("=" * 50)
    print(f"📁 Input: {audio_file}")
    print("💡 Using pause detection to identify speaker changes")
    print("=" * 50)
    
    # Load model
    print(f"\n📦 Loading model...")
    model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✅ Model loaded!")
    
    # Transcribe with aggressive VAD to catch speaker changes
    print("\n🎤 Transcribing with speaker break detection...")
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        language="en",
        condition_on_previous_text=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=800,  # Longer silence = speaker change
            speech_pad_ms=200
        )
    )
    
    # Convert to list for processing
    segment_list = []
    for seg in segments:
        segment_list.append({
            'start': seg.start,
            'end': seg.end,
            'text': seg.text.strip()
        })
    
    # Build screenplay
    screenplay = []
    screenplay.append("=" * 80)
    screenplay.append("CALL TRANSCRIPT - SCREENPLAY FORMAT")
    screenplay.append(f"File: {os.path.basename(audio_file)}")
    screenplay.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    screenplay.append("Note: Speakers estimated based on conversation patterns")
    screenplay.append("=" * 80)
    screenplay.append("")
    
    # Alternate speakers based on segments
    current_speaker = "SPEAKER A"
    
    for i, segment in enumerate(segment_list):
        # Check if there's a significant pause before this segment
        if i > 0:
            pause_duration = segment['start'] - segment_list[i-1]['end']
            # If pause > 1 second, likely speaker change
            if pause_duration > 1.0:
                current_speaker = "SPEAKER B" if current_speaker == "SPEAKER A" else "SPEAKER A"
        
        # Format timestamp
        timestamp = f"[{segment['start']:.1f} - {segment['end']:.1f}]"
        
        # Add to screenplay
        screenplay.append(f"{current_speaker} {timestamp}:")
        screenplay.append(f"  {segment['text']}")
        screenplay.append("")
    
    # Join all lines
    screenplay_text = "\n".join(screenplay)
    
    # Save regular screenplay
    output_file = audio_file.replace('.wav', '_screenplay_speakers.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(screenplay_text)
    
    print(f"\n✅ Screenplay saved to: {output_file}")
    
    # Also save a cleaner version without timestamps
    clean_screenplay = []
    clean_screenplay.append("=" * 80)
    clean_screenplay.append("CLEAN SCREENPLAY FORMAT (NO TIMESTAMPS)")
    clean_screenplay.append("=" * 80)
    clean_screenplay.append("")
    
    current_speaker = "SPEAKER A"
    current_lines = []
    
    for i, segment in enumerate(segment_list):
        # Check for speaker change
        if i > 0:
            pause_duration = segment['start'] - segment_list[i-1]['end']
            if pause_duration > 1.0 and current_lines:
                # Output previous speaker's collected lines
                clean_screenplay.append(f"{current_speaker}:")
                clean_screenplay.append(f"  {' '.join(current_lines)}")
                clean_screenplay.append("")
                current_lines = []
                current_speaker = "SPEAKER B" if current_speaker == "SPEAKER A" else "SPEAKER A"
        
        current_lines.append(segment['text'])
    
    # Don't forget last speaker
    if current_lines:
        clean_screenplay.append(f"{current_speaker}:")
        clean_screenplay.append(f"  {' '.join(current_lines)}")
    
    clean_text = "\n".join(clean_screenplay)
    
    # Save clean version
    clean_file = audio_file.replace('.wav', '_screenplay_clean.txt')
    with open(clean_file, 'w', encoding='utf-8') as f:
        f.write(clean_text)
    
    print(f"✅ Clean screenplay saved to: {clean_file}")
    
    # Show preview
    print("\n" + "=" * 50)
    print("PREVIEW:")
    print("=" * 50)
    preview = clean_text[:800] + "..." if len(clean_text) > 800 else clean_text
    print(preview)
    
    return output_file, clean_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python screenplay_with_breaks_rtx.py <audio_file.wav>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    format_screenplay_with_speakers(audio_file)

if __name__ == "__main__":
    main()