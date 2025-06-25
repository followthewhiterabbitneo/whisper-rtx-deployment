#!/usr/bin/env python3
"""
Convert μ-law (u-law) WAV files to standard PCM WAV
Specifically for telephony recordings (8kHz, μ-law)
"""

import sys
import os
import subprocess
from pathlib import Path
import glob

def convert_ulaw_to_pcm(input_file, output_file=None):
    """Convert μ-law WAV to standard PCM WAV using ffmpeg"""
    
    if not output_file:
        # Create output filename
        base = Path(input_file).stem
        output_dir = Path("converted_wav")
        output_dir.mkdir(exist_ok=True)
        output_file = str(output_dir / f"{base}_pcm.wav")
    
    print(f"Converting: {Path(input_file).name}")
    print(f"  Format: μ-law 8kHz → PCM 16kHz")
    
    # FFmpeg command to convert μ-law to PCM
    cmd = [
        'ffmpeg',
        '-i', input_file,           # Input
        '-acodec', 'pcm_s16le',     # Convert to 16-bit PCM
        '-ar', '16000',             # Upsample to 16kHz (better for Whisper)
        '-ac', '2',                 # Ensure stereo
        '-y',                       # Overwrite
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Converted: {Path(output_file).name}")
            return output_file
        else:
            print(f"  ❌ Error: {result.stderr}")
            return None
    except FileNotFoundError:
        print("❌ FFmpeg not found!")
        print("Install with: choco install ffmpeg")
        return None

def batch_convert_ulaw(pattern):
    """Convert all μ-law files matching pattern"""
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found matching: {pattern}")
        return []
    
    print(f"Found {len(files)} μ-law files to convert")
    print("="*50)
    
    converted_files = []
    for f in files:
        output = convert_ulaw_to_pcm(f)
        if output:
            converted_files.append(output)
    
    print(f"\n✅ Converted {len(converted_files)} files")
    print(f"📁 Output directory: converted_wav/")
    
    return converted_files

def main():
    if len(sys.argv) < 2:
        print("μ-law to PCM WAV Converter")
        print("="*30)
        print("For your telephony recordings (8kHz μ-law)")
        print("")
        print("Usage:")
        print("  python convert_ulaw_to_pcm.py <file.wav>")
        print("  python convert_ulaw_to_pcm.py 'pattern*.wav'")
        print("")
        print("Example:")
        print("  python convert_ulaw_to_pcm.py wav_batch_download\\*.wav")
        sys.exit(1)
    
    input_pattern = sys.argv[1]
    
    if '*' in input_pattern:
        # Batch mode
        batch_convert_ulaw(input_pattern)
    else:
        # Single file
        if os.path.exists(input_pattern):
            convert_ulaw_to_pcm(input_pattern)
        else:
            print(f"File not found: {input_pattern}")

if __name__ == "__main__":
    main()