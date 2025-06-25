#!/usr/bin/env python3
"""
PROPER TURN BY TURN - Same quality as your regular transcription
"""

import sys
from faster_whisper import WhisperModel
from pathlib import Path
import glob

# Your EXACT settings from use_kaggle_whisper_turbo.py
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"

def process_file(audio_file, model):
    """Use your PROVEN settings"""
    print(f"\nProcessing: {Path(audio_file).name}")
    
    # Use YOUR EXACT transcription settings that work well
    segments, info = model.transcribe(
        audio_file,
        beam_size=1,          # Your turbo setting
        best_of=1,            # Your turbo setting
        temperature=0,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,  # Your setting
            speech_pad_ms=400            # Your setting
        )
    )
    
    # Get all segments first
    all_segments = []
    for seg in segments:
        all_segments.append({
            'start': seg.start,
            'end': seg.end,
            'text': seg.text.strip()
        })
    
    # Now detect speaker changes by NATURAL pauses
    output = []
    output.append(f"TRANSCRIPT: {Path(audio_file).name}")
    output.append("="*60)
    output.append("")
    
    current_speaker = "SPEAKER A"
    speaker_text = []
    
    for i, seg in enumerate(all_segments):
        # Check for speaker change (longer pause = new speaker)
        if i > 0:
            pause = seg['start'] - all_segments[i-1]['end']
            if pause > 1.5:  # 1.5 seconds = likely speaker change
                # Output previous speaker
                if speaker_text:
                    output.append(f"{current_speaker}:")
                    output.append(' '.join(speaker_text))
                    output.append("")
                # Switch speaker
                current_speaker = "SPEAKER B" if current_speaker == "SPEAKER A" else "SPEAKER A"
                speaker_text = []
        
        speaker_text.append(seg['text'])
    
    # Don't forget last speaker
    if speaker_text:
        output.append(f"{current_speaker}:")
        output.append(' '.join(speaker_text))
    
    # Also save a simple version (just the text, no speakers)
    simple_text = ' '.join([seg['text'] for seg in all_segments])
    
    # Save both versions
    output_dir = Path("turn_by_turn_output")
    output_dir.mkdir(exist_ok=True)
    
    # Turn by turn version
    turn_file = output_dir / f"{Path(audio_file).stem}_turns.txt"
    with open(turn_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    # Simple version (like your normal output)
    simple_file = output_dir / f"{Path(audio_file).stem}_simple.txt"
    with open(simple_file, 'w', encoding='utf-8') as f:
        f.write(f"TRANSCRIPT: {Path(audio_file).name}\n")
        f.write("="*60 + "\n\n")
        f.write(simple_text)
    
    print(f"✅ Saved:")
    print(f"   Turn-by-turn: {turn_file}")
    print(f"   Simple text: {simple_file}")
    
    return turn_file

def main():
    if len(sys.argv) < 2:
        print("PROPER Turn-by-Turn Transcription")
        print("Same quality as your regular transcripts")
        print("="*40)
        print("Usage: python proper_turn_by_turn.py <pattern>")
        print("Example: python proper_turn_by_turn.py wav_batch_download\\*.wav")
        sys.exit(1)
    
    pattern = sys.argv[1]
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found: {pattern}")
        sys.exit(1)
    
    print(f"Found {len(files)} files")
    
    # Load model with YOUR settings
    print("Loading model...")
    model = WhisperModel(
        MODEL_PATH, 
        device="cuda", 
        compute_type="int8_float16",  # Your exact setting
        num_workers=4,
        cpu_threads=8
    )
    
    # Process all
    for f in files:
        process_file(f, model)
    
    print("\n✅ ALL DONE!")
    print(f"📁 Check: turn_by_turn_output/")

if __name__ == "__main__":
    main()