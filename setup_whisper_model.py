#!/usr/bin/env python3
"""
Setup Whisper model from manually downloaded Kaggle files
Handles files with (1) suffix from browser downloads
"""

import os
import shutil
from pathlib import Path

def setup_model_directory():
    """Create the proper directory structure and organize model files"""
    
    print("=== Whisper Model Setup ===\n")
    
    # Expected model files
    expected_files = [
        "README.md",
        "config.json", 
        ".gitattributes",
        "model.bin",
        "preprocessor_config.json",
        "tokenizer.json",
        "vocabulary.json"
    ]
    
    # Create target directory
    target_dir = Path("models/faster-whisper-large-v3-turbo-ct2")
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory: {target_dir}")
    
    # Look for files in common download locations
    search_dirs = [
        Path.cwd(),  # Current directory
        Path.home() / "Downloads",
        Path("C:/Users/estillmane/Downloads"),
        Path.cwd() / "downloads"
    ]
    
    files_found = []
    files_to_rename = []
    
    print("\n🔍 Searching for model files...")
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        # Look for both normal and (1) suffixed files
        for expected_file in expected_files:
            # Check normal filename
            normal_path = search_dir / expected_file
            if normal_path.exists():
                files_found.append((normal_path, expected_file))
                
            # Check with (1) suffix - common browser download rename
            # Handle both "file (1).ext" and "file(1).ext" patterns
            base, ext = os.path.splitext(expected_file)
            
            # Try different patterns
            patterns = [
                f"{base} (1){ext}",  # Space before (1)
                f"{base}(1){ext}",   # No space
                f"{expected_file} (1)",  # Suffix at end
                f"{expected_file}(1)"    # Suffix at end, no space
            ]
            
            for pattern in patterns:
                renamed_path = search_dir / pattern
                if renamed_path.exists():
                    files_to_rename.append((renamed_path, expected_file))
                    break
    
    # Special handling for .gitattributes which might be "gitattributes (1)"
    for search_dir in search_dirs:
        if search_dir.exists():
            gitattr_patterns = [
                "gitattributes (1)",
                "gitattributes(1)", 
                "gitattributes",
                ".gitattributes (1)"
            ]
            for pattern in gitattr_patterns:
                path = search_dir / pattern
                if path.exists() and not any(f[1] == ".gitattributes" for f in files_found + files_to_rename):
                    files_to_rename.append((path, ".gitattributes"))
                    break
    
    # Report findings
    all_files = files_found + files_to_rename
    print(f"\n📊 Found {len(all_files)} files:")
    
    for src, dst in all_files:
        status = " [needs rename]" if (src, dst) in files_to_rename else ""
        print(f"  • {src.name} -> {dst}{status}")
    
    # Check if we have all required files
    found_names = {dst for _, dst in all_files}
    missing = set(expected_files) - found_names
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        print("\nPlease download all files from:")
        print("https://www.kaggle.com/datasets/rikstillman/faster-whisper-large-v3-turbo-ct2")
        return False
    
    # Copy/move files to target directory
    print(f"\n📁 Setting up model in: {target_dir}")
    
    for src_path, dst_name in all_files:
        dst_path = target_dir / dst_name
        
        try:
            # Copy file (preserving original in Downloads)
            shutil.copy2(src_path, dst_path)
            print(f"  ✅ Copied: {dst_name}")
        except Exception as e:
            print(f"  ❌ Error copying {dst_name}: {e}")
    
    print("\n🎉 Model setup complete!")
    print(f"\n💡 To use the model:")
    print(f"   python use_kaggle_whisper_turbo.py test.wav")
    
    return True

def verify_model(model_dir="models/faster-whisper-large-v3-turbo-ct2"):
    """Verify the model is set up correctly"""
    model_path = Path(model_dir)
    
    if not model_path.exists():
        print(f"❌ Model directory not found: {model_dir}")
        return False
    
    required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
    
    print(f"\n🔍 Verifying model in: {model_dir}")
    
    for file in required_files:
        file_path = model_path / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {file} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {file} - MISSING")
            return False
    
    print("\n✅ Model verification passed!")
    return True

if __name__ == "__main__":
    if setup_model_directory():
        verify_model()