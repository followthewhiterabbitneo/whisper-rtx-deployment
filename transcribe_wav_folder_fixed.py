#!/usr/bin/env python3
"""
Transcribe all WAV files in the wav/ folder using Whisper turbo model
Fixed to handle Windows case-insensitive file system
"""

import os
import time
from pathlib import Path
from faster_whisper import WhisperModel

def transcribe_folder():
    """Transcribe all audio files in wav/ folder"""
    print("=== Whisper Turbo Batch Transcription ===\n")
    
    # Set up paths
    wav_dir = Path("wav")
    output_dir = Path("transcriptions")
    output_dir.mkdir(exist_ok=True)
    
    # Check if wav directory exists
    if not wav_dir.exists():
        print(f"❌ Directory not found: {wav_dir}")
        print("Please create a 'wav' folder and put audio files in it")
        return
    
    # Find audio files (case-insensitive on Windows)
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.opus']
    audio_files = set()  # Use set to avoid duplicates
    
    for ext in audio_extensions:
        # Only search lowercase extension to avoid duplicates on Windows
        for file in wav_dir.glob(f"*{ext.lower()}"):
            audio_files.add(file)
        # Also check uppercase if different
        for file in wav_dir.glob(f"*{ext.upper()}"):
            audio_files.add(file)
    
    # Convert to sorted list
    audio_files = sorted(list(audio_files))
    
    if not audio_files:
        print(f"❌ No audio files found in {wav_dir}")
        return
    
    print(f"📁 Found {len(audio_files)} audio file(s) to transcribe:")
    for f in audio_files:
        print(f"  - {f.name} ({f.stat().st_size/1024/1024:.1f} MB)")
    
    # Load model
    model_path = "models/faster-whisper-large-v3-turbo-ct2"
    if not Path(model_path).exists():
        print(f"❌ Model not found at: {model_path}")
        print("Run 'python fix_model_names.py' first")
        return
    
    print(f"\n🚀 Loading Whisper turbo model...")
    start = time.time()
    
    model = WhisperModel(
        model_path,
        device="cuda",
        compute_type="int8_float16",
        num_workers=4
    )
    
    load_time = time.time() - start
    print(f"✅ Model loaded in {load_time:.2f}s")
    
    # Process each file
    total_audio_duration = 0
    total_transcribe_time = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{'='*50}")
        print(f"📄 File {i}/{len(audio_files)}: {audio_file.name}")
        
        try:
            # Transcribe
            start = time.time()
            segments, info = model.transcribe(
                str(audio_file),
                beam_size=1,  # Turbo setting
                best_of=1,    # Turbo setting
                temperature=0,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                ),
                language="en"  # Force English for speed, remove if multilingual
            )
            
            # Collect text
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            transcribe_time = time.time() - start
            
            # Save transcription
            output_file = output_dir / f"{audio_file.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"File: {audio_file.name}\n")
                f.write(f"Duration: {info.duration:.2f}s\n")
                f.write(f"Language: {info.language}\n")
                f.write(f"Transcription time: {transcribe_time:.2f}s\n")
                f.write(f"Real-time factor: {transcribe_time/info.duration:.2f}x\n")
                f.write(f"\n{'='*50}\n\n")
                f.write(full_text.strip())
            
            # Print summary
            print(f"⏱️  Duration: {info.duration:.2f}s")
            print(f"🚀 Transcribed in: {transcribe_time:.2f}s")
            print(f"📊 Speed: {transcribe_time/info.duration:.2f}x real-time")
            print(f"📝 Saved to: {output_file}")
            print(f"\n📄 Preview: {full_text[:200]}...")
            
            # Update totals
            total_audio_duration += info.duration
            total_transcribe_time += transcribe_time
            
        except Exception as e:
            print(f"❌ Error transcribing {audio_file.name}: {e}")
            continue
    
    # Final summary
    if audio_files:
        print(f"\n{'='*50}")
        print("📊 FINAL SUMMARY")
        print(f"{'='*50}")
        print(f"Total files: {len(audio_files)}")
        print(f"Total audio: {total_audio_duration:.2f}s ({total_audio_duration/60:.1f} minutes)")
        print(f"Total time: {total_transcribe_time:.2f}s ({total_transcribe_time/60:.1f} minutes)")
        if total_audio_duration > 0:
            print(f"Average speed: {total_transcribe_time/total_audio_duration:.2f}x real-time")
        print(f"\n✅ All transcriptions saved to: {output_dir.absolute()}")

def main():
    """Main function"""
    import sys
    
    # Check for GPU
    import torch
    if not torch.cuda.is_available():
        print("⚠️  WARNING: No GPU detected! This will be slow on CPU.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    transcribe_folder()

if __name__ == "__main__":
    main()