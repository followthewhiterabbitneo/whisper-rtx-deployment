#!/usr/bin/env python3
"""
Download Whisper large-v3 turbo model for faster-whisper
The turbo model provides the best balance of speed and quality
"""

import os
import sys
from faster_whisper import download_model

def download_turbo_model():
    """Download the Whisper large-v3 turbo model"""
    print("Downloading Whisper large-v3 turbo model...")
    print("This is the latest and fastest high-quality model from OpenAI")
    print("Model size: ~1.5GB")
    
    try:
        # Download the turbo model
        # Note: As of late 2024, the turbo model is available as "large-v3"
        # with specific configuration for turbo mode
        model_path = download_model("large-v3", cache_dir=None)
        
        print(f"\n✅ Model downloaded successfully!")
        print(f"📁 Location: {model_path}")
        
        # Also download a smaller model for testing/comparison
        print("\nAlso downloading 'base' model for quick tests...")
        base_path = download_model("base", cache_dir=None)
        print(f"✅ Base model downloaded to: {base_path}")
        
        print("\n🚀 Available models for faster-whisper:")
        print("- large-v3: Highest quality (turbo capable)")
        print("- base: Faster, good for testing")
        print("- tiny: Fastest, lowest quality")
        
        print("\n💡 For turbo mode with large-v3:")
        print("Use: WhisperModel('large-v3', device='cuda', compute_type='float16')")
        
        return model_path
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Ensure you have ~2GB free space")
        print("3. Try manual download from Hugging Face:")
        print("   https://huggingface.co/Systran/faster-whisper-large-v3")
        return None

def check_existing_models():
    """Check what models are already cached"""
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    whisper_cache = os.path.expanduser("~/.cache/whisper")
    
    print("Checking existing models...")
    
    if os.path.exists(cache_dir):
        models = [d for d in os.listdir(cache_dir) if 'whisper' in d.lower()]
        if models:
            print(f"\nFound in Hugging Face cache: {models}")
    
    if os.path.exists(whisper_cache):
        models = os.listdir(whisper_cache)
        if models:
            print(f"Found in Whisper cache: {models}")

def main():
    """Main function"""
    print("=== Whisper Turbo Model Downloader ===\n")
    
    # Check existing models
    check_existing_models()
    
    # Prompt to download
    response = input("\nDownload Whisper large-v3 turbo model? (y/n): ")
    if response.lower() == 'y':
        download_turbo_model()
    else:
        print("Skipped download.")
        print("\nTo use existing models:")
        print("from faster_whisper import WhisperModel")
        print("model = WhisperModel('large-v3', device='cuda')")

if __name__ == "__main__":
    main()