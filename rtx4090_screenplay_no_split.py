#!/usr/bin/env python3
"""
RTX 4090 Screenplay WITHOUT Channel Split
For when you can't split stereo (μ-law, etc)
Uses VAD to detect speaker changes instead
"""

import sys
import os
from pathlib import Path
from faster_whisper import WhisperModel
from datetime import datetime
import glob

# Your existing setup
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"  # Your current setting

def process_without_split(audio_file, model):
    """Process audio without channel splitting - uses pause detection"""
    print(f"\n🎬 Processing: {Path(audio_file).name}")
    print("  Using pause detection for speaker changes")
    
    # Transcribe the whole file (Whisper handles μ-law fine!)
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        language="en",
        condition_on_previous_text=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=800,  # Detect speaker changes
            speech_pad_ms=400
        )
    )
    
    # Convert to list with speaker detection
    segment_list = []
    current_speaker = "SPEAKER A"
    
    for i, seg in enumerate(segments):
        # Add segment
        segment_list.append({
            'start': seg.start,
            'end': seg.end,
            'text': seg.text.strip(),
            'speaker': current_speaker
        })
        
        # Check if next segment has a gap (speaker change)
        if i < len(list(segments)) - 1:
            # This is approximate since we're iterating
            # In production, convert to list first
            pass
    
    # Better approach - collect all first
    all_segments = list(segments)
    processed = []
    current_speaker = "SPEAKER A"
    
    for i, seg in enumerate(all_segments):
        # Check for speaker change based on pause
        if i > 0:
            pause = seg.start - all_segments[i-1].end
            if pause > 1.0:  # 1 second pause = speaker change
                current_speaker = "SPEAKER B" if current_speaker == "SPEAKER A" else "SPEAKER A"
        
        processed.append({
            'start': seg.start,
            'end': seg.end,
            'text': seg.text.strip(),
            'speaker': current_speaker
        })
    
    return processed, info

def create_screenplay(segments, audio_file):
    """Format as screenplay"""
    output_dir = Path("screenplay_output")
    output_dir.mkdir(exist_ok=True)
    
    screenplay = []
    screenplay.append(f"SCREENPLAY: {Path(audio_file).name}")
    screenplay.append("="*60)
    screenplay.append("Note: Speakers detected by conversation pauses")
    screenplay.append("="*60)
    screenplay.append("")
    
    # Group by speaker
    current_speaker = None
    current_text = []
    
    for seg in segments:
        if seg['speaker'] != current_speaker:
            if current_speaker and current_text:
                screenplay.append(f"\n{current_speaker}:")
                screenplay.append(' '.join(current_text))
            current_speaker = seg['speaker']
            current_text = [seg['text']]
        else:
            current_text.append(seg['text'])
    
    # Last speaker
    if current_text:
        screenplay.append(f"\n{current_speaker}:")
        screenplay.append(' '.join(current_text))
    
    # Save
    base_name = Path(audio_file).stem
    output_file = output_dir / f"{base_name}_screenplay_vad.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(screenplay))
    
    return output_file

def process_batch(pattern):
    """Process multiple files"""
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found: {pattern}")
        return
    
    print(f"Found {len(files)} files")
    print("Loading model...")
    
    # Load model once
    model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✅ Model loaded")
    
    # Process each file
    all_scenes = []
    
    for i, audio_file in enumerate(files, 1):
        print(f"\n{'='*60}")
        print(f"SCENE {i}/{len(files)}")
        
        segments, info = process_without_split(audio_file, model)
        output = create_screenplay(segments, audio_file)
        
        print(f"✅ Saved: {output}")
        
        all_scenes.append({
            'scene': i,
            'file': audio_file,
            'segments': segments
        })
    
    # Create combined screenplay
    print("\n📝 Creating complete screenplay...")
    
    complete = []
    complete.append("🎬 COMPLETE SCREENPLAY - ALL SCENES")
    complete.append("="*70)
    complete.append(f"Total Scenes: {len(all_scenes)}")
    complete.append("="*70)
    
    for scene_data in all_scenes:
        complete.append(f"\n\n{'='*60}")
        complete.append(f"SCENE {scene_data['scene']}: {Path(scene_data['file']).name}")
        complete.append("="*60)
        
        current_speaker = None
        current_text = []
        
        for seg in scene_data['segments']:
            if seg['speaker'] != current_speaker:
                if current_speaker and current_text:
                    complete.append(f"\n{current_speaker}:")
                    complete.append(' '.join(current_text))
                current_speaker = seg['speaker']
                current_text = [seg['text']]
            else:
                current_text.append(seg['text'])
        
        if current_text:
            complete.append(f"\n{current_speaker}:")
            complete.append(' '.join(current_text))
    
    # Save complete
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    complete_file = Path("screenplay_output") / f"COMPLETE_SCREENPLAY_VAD_{timestamp}.txt"
    
    with open(complete_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(complete))
    
    print(f"\n✅ Complete screenplay: {complete_file}")

def main():
    if len(sys.argv) < 2:
        print("RTX 4090 Screenplay - No Channel Split Required")
        print("Works with ANY audio format including μ-law")
        print("="*50)
        print("Usage:")
        print("  python rtx4090_screenplay_no_split.py 'pattern'")
        print("\nExample:")
        print("  python rtx4090_screenplay_no_split.py wav_batch_download\\*.wav")
        sys.exit(1)
    
    pattern = sys.argv[1]
    process_batch(pattern)

if __name__ == "__main__":
    main()