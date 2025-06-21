#!/usr/bin/env python3
"""
Fix model files with (1) in their names from manual extraction
"""

import os
import shutil
from pathlib import Path

def fix_model_files():
    """Rename files with (1) suffix and organize them"""
    print("=== Fixing Whisper Model Files ===\n")
    
    # Look in downloads folder and current directory
    search_dirs = [Path("downloads"), Path(".")]
    
    # Files to rename
    rename_map = {
        "config (1).json": "config.json",
        "model (1).bin": "model.bin",
        "gitattributes (1)": ".gitattributes",
        "README (1).md": "README.md",
        # Also handle without spaces
        "config(1).json": "config.json",
        "model(1).bin": "model.bin",
        "gitattributes(1)": ".gitattributes",
        # Files that might not have (1)
        "tokenizer.json": "tokenizer.json",
        "vocabulary.json": "vocabulary.json",
        "preprocessor_config.json": "preprocessor_config.json"
    }
    
    # Create target directory
    target_dir = Path("models/faster-whisper-large-v3-turbo-ct2")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    files_found = {}
    
    # Search for files
    print("🔍 Looking for model files...")
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for old_name, new_name in rename_map.items():
            file_path = search_dir / old_name
            if file_path.exists() and new_name not in files_found:
                files_found[new_name] = file_path
                print(f"  ✅ Found: {old_name} -> {new_name}")
        
        # Also check for files without (1) suffix
        for file in search_dir.iterdir():
            if file.is_file() and file.name in rename_map.values() and file.name not in files_found:
                files_found[file.name] = file
                print(f"  ✅ Found: {file.name}")
    
    # Check what we have
    required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
    missing = [f for f in required_files if f not in files_found]
    
    if missing:
        print(f"\n⚠️  Missing required files: {', '.join(missing)}")
        print("\nMake sure you've extracted ALL files from the tar.gz")
        return False
    
    # Copy and rename files
    print(f"\n📁 Setting up model in: {target_dir}")
    for new_name, src_path in files_found.items():
        dst_path = target_dir / new_name
        try:
            shutil.copy2(src_path, dst_path)
            print(f"  ✅ Copied: {new_name}")
        except Exception as e:
            print(f"  ❌ Error copying {new_name}: {e}")
    
    # Verify
    print("\n🔍 Verifying model...")
    for file in required_files:
        file_path = target_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {file} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {file} - MISSING")
    
    print("\n🎉 Model setup complete!")
    print("\n💡 To use the model:")
    print("   python use_kaggle_whisper_turbo.py test.wav")
    
    # Optional: Clean up source files
    response = input("\n🗑️  Delete original files with (1) in names? (y/n): ")
    if response.lower() == 'y':
        for src_path in files_found.values():
            if '(1)' in src_path.name:
                src_path.unlink()
                print(f"  🗑️  Deleted: {src_path.name}")
    
    return True

if __name__ == "__main__":
    fix_model_files()