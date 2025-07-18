#!/usr/bin/env python3
"""
Fix llama-cpp-python to use GPU on Windows RTX
"""

import subprocess
import sys

print("Fixing llama-cpp-python for GPU support...")
print("="*50)

# Uninstall current version
print("1. Uninstalling current llama-cpp-python...")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "llama-cpp-python"])

# Install with CUDA support
print("\n2. Installing llama-cpp-python with CUDA support...")
print("This will take a few minutes to compile...")

# For Windows with CUDA 12.x - use pre-built wheel
print("Detecting system...")
import platform
if platform.system() == "Windows":
    # Direct wheel URL for Windows CUDA 12.1
    wheel_url = "https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.2-cu121/llama_cpp_python-0.3.2-cp311-cp311-win_amd64.whl"
    install_cmd = [sys.executable, "-m", "pip", "install", wheel_url]
else:
    install_cmd = [
        sys.executable, "-m", "pip", "install", 
        "llama-cpp-python",
        "--force-reinstall",
        "--no-cache-dir",
        "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121"
    ]

result = subprocess.run(install_cmd)

if result.returncode == 0:
    print("\n✓ Successfully installed llama-cpp-python with GPU support!")
    print("\nTo verify GPU is working, run:")
    print("python test_gemma3_legal.py test_output/20250620_145645_LOLW.wav.txt")
    print("\nLook for 'CUDA' in the output!")
else:
    print("\n✗ Installation failed!")
    print("Try manual installation:")
    print("pip install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121")