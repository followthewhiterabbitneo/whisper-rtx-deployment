#!/usr/bin/env python3
"""
Debug script to see what files are found in wav folder
"""

from pathlib import Path

def debug_wav_folder():
    """Show what files are in the wav folder"""
    print("=== Debug WAV Folder ===\n")
    
    wav_dir = Path("wav")
    
    if not wav_dir.exists():
        print(f"❌ Directory not found: {wav_dir}")
        return
    
    # List ALL files
    print(f"📁 All files in {wav_dir}:")
    all_files = list(wav_dir.iterdir())
    for f in all_files:
        print(f"  - {f.name} ({'directory' if f.is_dir() else f'file: {f.stat().st_size/1024/1024:.1f}MB'})")
    
    # Check what audio files are detected
    print("\n🎵 Audio files detected:")
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.opus']
    audio_files = []
    
    for ext in audio_extensions:
        found = list(wav_dir.glob(f"*{ext}"))
        if found:
            print(f"  {ext}: {[f.name for f in found]}")
            audio_files.extend(found)
        
        found_upper = list(wav_dir.glob(f"*{ext.upper()}"))
        if found_upper:
            print(f"  {ext.upper()}: {[f.name for f in found_upper]}")
            audio_files.extend(found_upper)
    
    # Remove duplicates
    unique_files = list(set(audio_files))
    print(f"\n📊 Total unique audio files: {len(unique_files)}")
    for f in unique_files:
        print(f"  - {f.name}")

if __name__ == "__main__":
    debug_wav_folder()