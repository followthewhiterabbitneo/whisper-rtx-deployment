#!/usr/bin/env python3
"""
Setup script for Gemma 2 9B on RHEL8 server
Run this on s01vpsromuls001 after pulling from GitHub
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    print("=== Gemma 2 9B Setup Script for RHEL8 ===")
    
    # Check if we're in the right directory
    if not os.path.exists("/moneyball/whisper-rtx-deployment"):
        print("ERROR: This script should be run from /moneyball/whisper-rtx-deployment")
        sys.exit(1)
    
    models_dir = Path("/moneyball/whisper-rtx-deployment/models")
    
    # Find the tar.gz file
    tar_files = list(models_dir.glob("*gemma*2*9b*.tar.gz"))
    if not tar_files:
        print("ERROR: No Gemma 2 9B tar.gz file found in models/")
        print("Files in models/:")
        for f in models_dir.iterdir():
            print(f"  - {f.name}")
        sys.exit(1)
    
    tar_file = tar_files[0]
    print(f"Found model archive: {tar_file.name}")
    
    # Extract the model
    extract_dir = models_dir / "gemma-2-9b-it-Q5_K_M-GGUF"
    if extract_dir.exists():
        print(f"Model already extracted to {extract_dir}")
    else:
        print(f"Extracting {tar_file.name}...")
        cmd = ["tar", "-xzf", str(tar_file), "-C", str(models_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR extracting: {result.stderr}")
            sys.exit(1)
        print("Extraction complete!")
    
    # Check for GGUF file
    gguf_files = list(models_dir.rglob("*.gguf"))
    if gguf_files:
        print(f"\nFound GGUF model: {gguf_files[0].name}")
        print(f"Full path: {gguf_files[0]}")
    else:
        print("\nWARNING: No .gguf file found after extraction")
    
    # Check GPU availability
    print("\n=== GPU Check ===")
    try:
        result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print("No GPU detected")
    except FileNotFoundError:
        print("nvidia-smi not found")
    
    # Check environment
    print("\n=== Environment Check ===")
    print(f"Python: {sys.executable}")
    print(f"Working dir: {os.getcwd()}")
    
    # Next steps
    print("\n=== Next Steps ===")
    print("1. Activate environment: source /moneyball/gemma-env/bin/activate")
    print("2. Run test script: python test_gemma2_gpu_rhel8.py")
    
if __name__ == "__main__":
    main()