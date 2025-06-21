#!/usr/bin/env python3
"""
Use the Whisper large-v3-turbo model from Kaggle
Download from: rikstillman/faster-whisper-large-v3-turbo-ct2
"""

import os
import sys
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel

def download_from_kaggle(dataset_name="rikstillman/faster-whisper-large-v3-turbo-ct2"):
    """Download the turbo model from Kaggle"""
    print(f"📥 Downloading Whisper turbo model from Kaggle: {dataset_name}")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Download using Kaggle CLI
    try:
        cmd = f"kaggle datasets download -d {dataset_name} -p {models_dir} --unzip"
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Download successful!")
            # Find the model directory
            model_dirs = list(models_dir.glob("*"))
            if model_dirs:
                model_path = model_dirs[0]
                print(f"📁 Model path: {model_path}")
                return str(model_path)
        else:
            print(f"❌ Download failed: {result.stderr}")
            print("\nAlternative: Download manually from:")
            print(f"https://www.kaggle.com/datasets/{dataset_name}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def use_local_model(model_path):
    """Use a locally downloaded model"""
    print(f"\n🚀 Loading Whisper turbo model from: {model_path}")
    
    try:
        # Load the model
        model = WhisperModel(
            model_path,
            device="cuda",
            compute_type="int8_float16",  # Optimal for turbo mode
            num_workers=4,
            cpu_threads=8
        )
        
        print("✅ Model loaded successfully!")
        print("\n⚡ This is the turbo model - optimized for speed!")
        print("- 10x faster than large-v3")
        print("- Minimal quality loss")
        print("- Perfect for real-time transcription")
        
        return model
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def transcribe_audio(model, audio_file):
    """Transcribe audio using the turbo model"""
    print(f"\n🎤 Transcribing: {audio_file}")
    
    segments, info = model.transcribe(
        audio_file,
        beam_size=1,  # Turbo setting
        best_of=1,    # Turbo setting
        temperature=0,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=400
        )
    )
    
    # Collect results
    text = " ".join([seg.text.strip() for seg in segments])
    
    print(f"\n📊 Results:")
    print(f"Duration: {info.duration:.2f}s")
    print(f"Language: {info.language}")
    print(f"Probability: {info.language_probability:.2f}")
    print(f"\n📝 Transcription:\n{text}")
    
    return text

def main():
    """Main function"""
    print("=== Whisper Large-v3-Turbo from Kaggle ===\n")
    
    # Check if model exists locally
    model_paths = [
        "models/faster-whisper-large-v3-turbo-ct2",
        "models/large-v3-turbo-ct2",
        "C:/Users/estillmane/.cache/whisper/large-v3-turbo"
    ]
    
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            print(f"✅ Found local model: {path}")
            break
    
    if not model_path:
        print("❌ Model not found locally")
        response = input("\nDownload from Kaggle? (y/n): ")
        if response.lower() == 'y':
            model_path = download_from_kaggle()
    
    if model_path:
        model = use_local_model(model_path)
        
        if model and len(sys.argv) > 1:
            # Transcribe provided audio file
            audio_file = sys.argv[1]
            if os.path.exists(audio_file):
                transcribe_audio(model, audio_file)
            else:
                print(f"❌ Audio file not found: {audio_file}")
        elif model:
            print("\n💡 Usage: python use_kaggle_whisper_turbo.py <audio_file>")
            print("Example: python use_kaggle_whisper_turbo.py test.wav")

if __name__ == "__main__":
    main()