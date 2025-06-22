#!/usr/bin/env python3
"""
Check GGUF file integrity and format on RHEL8
"""
import os
import struct
import subprocess
from pathlib import Path

def check_gguf_magic(file_path):
    """Check if file has valid GGUF magic number"""
    try:
        with open(file_path, 'rb') as f:
            # GGUF files should start with specific magic bytes
            magic = f.read(4)
            
            # GGUF magic number is 'GGUF' (0x47475546)
            expected_magic = b'GGUF'
            
            print(f"First 4 bytes (raw): {magic}")
            print(f"First 4 bytes (hex): {magic.hex()}")
            print(f"Expected magic: {expected_magic} ({expected_magic.hex()})")
            
            if magic == expected_magic:
                print("✓ Valid GGUF magic number!")
                return True
            else:
                print("✗ Invalid magic number - file may be corrupted")
                
                # Check if it might be a different format
                if magic[:2] == b'PK':
                    print("  → File appears to be a ZIP archive")
                elif magic[:3] == b'\x1f\x8b\x08':
                    print("  → File appears to be GZIP compressed")
                elif magic == b'ggjt':
                    print("  → File appears to be old GGML format")
                    
                return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

def main():
    print("=== GGUF File Check ===")
    
    model_path = Path("/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf")
    
    if not model_path.exists():
        print(f"ERROR: Model file not found at {model_path}")
        return
    
    # Basic file info
    print(f"\nFile: {model_path}")
    size = model_path.stat().st_size
    print(f"Size: {size:,} bytes ({size / 1024**3:.2f} GB)")
    
    # Check file type using 'file' command
    print("\nFile type check:")
    result = subprocess.run(
        ["file", str(model_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    print(result.stdout.strip())
    
    # Check magic number
    print("\nMagic number check:")
    check_gguf_magic(model_path)
    
    # Check if file might still be compressed
    print("\nChecking if file needs extraction:")
    tar_file = Path("/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-q5_k_m.gguf-gguf-downloaded-jun-huggingingface-v1.tar.gz")
    if tar_file.exists():
        print(f"Found tar.gz: {tar_file.name}")
        print("The GGUF file might not have been properly extracted.")
        print("\nTo re-extract, run:")
        print(f"cd {model_path.parent}")
        print(f"tar -tzf {tar_file.name} | head -10  # List contents")
        print(f"tar -xzf {tar_file.name}  # Extract")
    
    # Suggest alternatives
    print("\n=== Possible Solutions ===")
    print("1. The file may not have extracted properly from the tar.gz")
    print("2. The file may be corrupted during download")
    print("3. We may need a different model format")
    print("\nTry using transformers library instead of llama-cpp-python")

if __name__ == "__main__":
    main()