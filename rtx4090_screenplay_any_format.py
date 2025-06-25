#!/usr/bin/env python3
"""
RTX 4090 SCREENPLAY - Handles ANY audio format
Uses ffmpeg to ensure compatibility
"""

import sys
import os
from pathlib import Path
import subprocess
import numpy as np
from faster_whisper import WhisperModel
from datetime import datetime
import json
import tempfile

# RTX 4090 Settings
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

def convert_to_wav_stereo(input_file):
    """Convert any audio to standard stereo WAV using ffmpeg"""
    print(f"🔄 Converting {Path(input_file).name} to standard WAV...")
    
    # Create temp file
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    
    # Use ffmpeg to convert to standard stereo WAV
    cmd = [
        'ffmpeg', '-i', input_file,
        '-acodec', 'pcm_s16le',  # Standard 16-bit PCM
        '-ar', '16000',           # 16kHz sample rate (good for speech)
        '-ac', '2',               # Force stereo
        '-y',                     # Overwrite
        temp_wav
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Conversion successful")
            return temp_wav
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            # Try simpler conversion
            cmd_simple = ['ffmpeg', '-i', input_file, '-y', temp_wav]
            result2 = subprocess.run(cmd_simple, capture_output=True, text=True)
            if result2.returncode == 0:
                print("✅ Simple conversion worked")
                return temp_wav
            else:
                print(f"❌ Simple conversion also failed: {result2.stderr}")
                return None
    except FileNotFoundError:
        print("❌ FFmpeg not found! Install with: choco install ffmpeg")
        return None
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None

def split_channels_numpy(wav_file):
    """Split stereo using numpy (more robust)"""
    print("📊 Splitting stereo channels...")
    
    # Use ffmpeg to split channels
    temp_left = tempfile.NamedTemporaryFile(suffix='_L.wav', delete=False).name
    temp_right = tempfile.NamedTemporaryFile(suffix='_R.wav', delete=False).name
    
    # Extract left channel
    cmd_left = [
        'ffmpeg', '-i', wav_file,
        '-af', 'pan=mono|c0=c0',  # Left channel only
        '-y', temp_left
    ]
    
    # Extract right channel  
    cmd_right = [
        'ffmpeg', '-i', wav_file,
        '-af', 'pan=mono|c0=c1',  # Right channel only
        '-y', temp_right
    ]
    
    try:
        subprocess.run(cmd_left, capture_output=True, check=True)
        subprocess.run(cmd_right, capture_output=True, check=True)
        print("✅ Channel split successful")
        return temp_left, temp_right
    except Exception as e:
        print(f"❌ Channel split error: {e}")
        return None, None

def process_any_audio(input_file):
    """Process any audio format into screenplay"""
    print(f"\n🎬 Processing: {Path(input_file).name}")
    print("="*60)
    
    # Convert to standard WAV
    wav_file = convert_to_wav_stereo(input_file)
    if not wav_file:
        print("❌ Could not convert audio file")
        return None
        
    # Split channels
    left_file, right_file = split_channels_numpy(wav_file)
    if not left_file:
        print("❌ Could not split channels")
        # Clean up
        try:
            os.remove(wav_file)
        except:
            pass
        return None
        
    # Load model
    print("\n🚀 Loading Whisper model...")
    model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
    
    # Transcribe both channels
    print("📞 Transcribing UNDERWRITER channel...")
    uw_segments, _ = model.transcribe(left_file, language="en", vad_filter=True)
    uw_list = [{'speaker': 'UNDERWRITER', 'text': seg.text.strip(), 
                'start': seg.start, 'end': seg.end} for seg in uw_segments]
    
    print("📱 Transcribing BROKER channel...")
    broker_segments, _ = model.transcribe(right_file, language="en", vad_filter=True)
    broker_list = [{'speaker': 'BROKER', 'text': seg.text.strip(),
                    'start': seg.start, 'end': seg.end} for seg in broker_segments]
    
    # Merge and sort
    all_segments = uw_list + broker_list
    all_segments.sort(key=lambda x: x['start'])
    
    # Create screenplay
    screenplay = []
    screenplay.append(f"SCREENPLAY: {Path(input_file).name}")
    screenplay.append("="*60)
    screenplay.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    screenplay.append("="*60)
    screenplay.append("")
    
    current_speaker = None
    current_text = []
    
    for seg in all_segments:
        if seg['speaker'] != current_speaker:
            if current_speaker and current_text:
                screenplay.append(f"\n{current_speaker}:")
                screenplay.append(f"{' '.join(current_text)}")
            current_speaker = seg['speaker']
            current_text = [seg['text']]
        else:
            current_text.append(seg['text'])
            
    # Last speaker
    if current_text:
        screenplay.append(f"\n{current_speaker}:")
        screenplay.append(f"{' '.join(current_text)}")
        
    # Save output
    output_dir = Path("screenplay_output")
    output_dir.mkdir(exist_ok=True)
    
    base_name = Path(input_file).stem
    output_file = output_dir / f"{base_name}_screenplay.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(screenplay))
        
    print(f"\n✅ Screenplay saved: {output_file}")
    
    # Cleanup temp files
    for f in [wav_file, left_file, right_file]:
        try:
            if f and os.path.exists(f):
                os.remove(f)
        except:
            pass
            
    return output_file

def main():
    if len(sys.argv) < 2:
        print("RTX 4090 Screenplay - Any Format")
        print("="*40)
        print("Usage: python rtx4090_screenplay_any_format.py <audio_file>")
        print("\nSupports: WAV, MP3, M4A, OGG, FLAC, etc.")
        print("Requires: ffmpeg (choco install ffmpeg)")
        sys.exit(1)
        
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
        
    process_any_audio(input_file)

if __name__ == "__main__":
    main()