#!/usr/bin/env python3
"""
Check WAV file format details
Diagnose "unknown format" errors
"""

import sys
import wave
import struct
import os
from pathlib import Path

def check_wav_file(filename):
    """Check detailed WAV format info"""
    print(f"\n{'='*60}")
    print(f"FILE: {filename}")
    print(f"Size: {os.path.getsize(filename):,} bytes")
    print("="*60)
    
    try:
        # Try with wave module first
        with wave.open(filename, 'rb') as wav:
            print("✅ Standard WAV format detected")
            print(f"Channels: {wav.getnchannels()}")
            print(f"Sample width: {wav.getsampwidth()} bytes")
            print(f"Frame rate: {wav.getframerate()} Hz")
            print(f"Frames: {wav.getnframes():,}")
            print(f"Compression: {wav.getcomptype()}")
            print(f"Duration: {wav.getnframes() / wav.getframerate():.2f} seconds")
            
    except wave.Error as e:
        print(f"❌ Wave module error: {e}")
        
        # Try to read raw header
        try:
            with open(filename, 'rb') as f:
                # Read RIFF header
                riff = f.read(4)
                size = struct.unpack('<I', f.read(4))[0]
                wave_tag = f.read(4)
                
                print(f"\nRaw header info:")
                print(f"RIFF tag: {riff}")
                print(f"File size: {size:,} bytes")
                print(f"WAVE tag: {wave_tag}")
                
                # Read fmt chunk
                fmt = f.read(4)
                fmt_size = struct.unpack('<I', f.read(4))[0]
                audio_format = struct.unpack('<H', f.read(2))[0]
                channels = struct.unpack('<H', f.read(2))[0]
                sample_rate = struct.unpack('<I', f.read(4))[0]
                byte_rate = struct.unpack('<I', f.read(4))[0]
                block_align = struct.unpack('<H', f.read(2))[0]
                bits_per_sample = struct.unpack('<H', f.read(2))[0]
                
                print(f"\nFormat chunk:")
                print(f"Format tag: {audio_format} ", end="")
                if audio_format == 1:
                    print("(PCM)")
                elif audio_format == 3:
                    print("(IEEE Float)")
                elif audio_format == 6:
                    print("(A-law)")
                elif audio_format == 7:
                    print("(μ-law)")
                else:
                    print(f"(Unknown format - this might be the issue!)")
                    
                print(f"Channels: {channels}")
                print(f"Sample rate: {sample_rate} Hz")
                print(f"Bits per sample: {bits_per_sample}")
                
        except Exception as e2:
            print(f"❌ Raw read error: {e2}")
            
    # Try with pydub as alternative
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(filename)
        print(f"\n✅ Pydub can read the file")
        print(f"Duration: {len(audio)/1000:.2f} seconds")
        print(f"Channels: {audio.channels}")
        print(f"Frame rate: {audio.frame_rate}")
        print(f"Sample width: {audio.sample_width}")
    except ImportError:
        print("\n📦 Pydub not installed (pip install pydub)")
    except Exception as e:
        print(f"\n❌ Pydub error: {e}")

def convert_to_standard_wav(input_file, output_file):
    """Try to convert to standard WAV format"""
    print(f"\n🔄 Attempting conversion to standard WAV...")
    
    try:
        from pydub import AudioSegment
        
        # Load audio (pydub handles many formats)
        audio = AudioSegment.from_file(input_file)
        
        # Export as standard WAV
        audio.export(
            output_file,
            format="wav",
            parameters=["-acodec", "pcm_s16le"]  # Standard 16-bit PCM
        )
        
        print(f"✅ Converted to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("WAV Format Checker")
        print("="*30)
        print("Usage: python check_wav_format.py <wav_file>")
        print("   or: python check_wav_format.py <pattern>")
        sys.exit(1)
        
    pattern = sys.argv[1]
    
    # Check if it's a pattern or single file
    if '*' in pattern:
        import glob
        files = glob.glob(pattern)
        print(f"Checking {len(files)} files matching: {pattern}")
    else:
        files = [pattern]
        
    for f in files:
        if os.path.exists(f):
            check_wav_file(f)
        else:
            print(f"❌ File not found: {f}")
            
    # Offer conversion
    if len(files) == 1 and os.path.exists(files[0]):
        print("\n" + "="*60)
        response = input("Try to convert to standard WAV? (y/n): ")
        if response.lower() == 'y':
            output = files[0].replace('.wav', '_converted.wav')
            convert_to_standard_wav(files[0], output)

if __name__ == "__main__":
    main()