#!/usr/bin/env python3
"""
Extract and setup Whisper model from Kaggle tar.gz download
"""

import os
import tarfile
import zipfile
from pathlib import Path

def extract_archive(archive_path, extract_to):
    """Extract tar.gz or zip archive"""
    print(f"📦 Extracting: {archive_path.name}")
    
    try:
        if archive_path.suffix == '.gz' and archive_path.stem.endswith('.tar'):
            # Handle tar.gz
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_to)
                print(f"✅ Extracted tar.gz to: {extract_to}")
        elif archive_path.suffix == '.zip':
            # Handle zip
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                print(f"✅ Extracted zip to: {extract_to}")
        else:
            print(f"❌ Unknown archive format: {archive_path.suffix}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False

def setup_whisper_model():
    """Extract and setup the Whisper model"""
    print("=== Whisper Model Setup from Archive ===\n")
    
    # Look for archive in downloads folder
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    # Find archive files
    archive_patterns = [
        "faster-whisper-large-v3-turbo-ct2.tar.gz",
        "faster-whisper-large-v3-turbo-ct2.zip",
        "archive.tar.gz",
        "archive.zip"
    ]
    
    archive_file = None
    for pattern in archive_patterns:
        archive_path = downloads_dir / pattern
        if archive_path.exists():
            archive_file = archive_path
            break
    
    if not archive_file:
        # Check current directory too
        for pattern in archive_patterns:
            archive_path = Path(pattern)
            if archive_path.exists():
                archive_file = archive_path
                break
    
    if not archive_file:
        print("❌ No archive found!")
        print("\nPlease download the model from Kaggle and place it in:")
        print(f"  {downloads_dir.absolute()}")
        print("\nExpected filename: faster-whisper-large-v3-turbo-ct2.tar.gz")
        return False
    
    print(f"✅ Found archive: {archive_file}")
    
    # Create target directory
    target_dir = Path("models/faster-whisper-large-v3-turbo-ct2")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract archive
    temp_extract = Path("temp_extract")
    temp_extract.mkdir(exist_ok=True)
    
    if extract_archive(archive_file, temp_extract):
        # Find the model files in extracted content
        model_files = []
        for file in temp_extract.rglob("*"):
            if file.is_file() and file.name in [
                "config.json", "model.bin", "tokenizer.json", 
                "vocabulary.json", "preprocessor_config.json",
                "README.md", ".gitattributes"
            ]:
                model_files.append(file)
        
        if not model_files:
            print("❌ No model files found in archive!")
            return False
        
        # Copy files to target directory
        print(f"\n📁 Setting up model in: {target_dir}")
        for file in model_files:
            target_file = target_dir / file.name
            file.rename(target_file)
            print(f"  ✅ Moved: {file.name}")
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_extract)
        
        print("\n🎉 Model setup complete!")
        print("\n💡 To use the model:")
        print("   python use_kaggle_whisper_turbo.py test.wav")
        
        # Verify installation
        verify_model(target_dir)
        return True
    
    return False

def verify_model(model_dir):
    """Verify the model is set up correctly"""
    required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
    
    print(f"\n🔍 Verifying model...")
    
    missing = []
    for file in required_files:
        file_path = model_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {file} ({size_mb:.1f} MB)")
        else:
            missing.append(file)
            print(f"  ❌ {file} - MISSING")
    
    if not missing:
        print("\n✅ Model ready to use!")
        return True
    else:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False

if __name__ == "__main__":
    setup_whisper_model()