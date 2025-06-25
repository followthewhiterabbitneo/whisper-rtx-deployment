#!/usr/bin/env python3
"""
SIMPLE TURN BY TURN - No BS, just works
"""

import sys
from faster_whisper import WhisperModel
from pathlib import Path
import glob

# Your existing setup
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"

def process_file(audio_file, model):
    """Just transcribe and detect turns by pauses"""
    print(f"\nProcessing: {Path(audio_file).name}")
    
    # Transcribe - Whisper handles μ-law fine!
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        language="en",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=1000)  # 1 second = speaker change
    )
    
    # Convert to list
    all_segs = list(segments)
    
    # Output turn by turn
    output = []
    output.append(f"FILE: {Path(audio_file).name}")
    output.append("="*60)
    
    current_speaker = "A"
    for i, seg in enumerate(all_segs):
        # Check for speaker change (1+ second gap)
        if i > 0 and (seg.start - all_segs[i-1].end) > 1.0:
            current_speaker = "B" if current_speaker == "A" else "A"
        
        output.append(f"\nSPEAKER {current_speaker}:")
        output.append(seg.text.strip())
    
    # Save
    output_dir = Path("turn_by_turn_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{Path(audio_file).stem}_turns.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"✅ Saved: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_turn_by_turn.py <pattern>")
        print("Example: python simple_turn_by_turn.py wav_batch_download\\*.wav")
        sys.exit(1)
    
    pattern = sys.argv[1]
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found: {pattern}")
        sys.exit(1)
    
    print(f"Found {len(files)} files")
    
    # Load model once
    print("Loading model...")
    model = WhisperModel(MODEL_PATH, device="cuda", compute_type="int8_float16")
    
    # Process all
    for f in files:
        process_file(f, model)
    
    print("\n✅ ALL DONE!")

if __name__ == "__main__":
    main()