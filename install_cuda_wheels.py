#!/usr/bin/env python3
"""
Install llama-cpp-python with CUDA support on Windows
"""
import subprocess
import sys
import os

print("Installing llama-cpp-python with CUDA support...")
print("="*50)

# Uninstall first
print("Uninstalling current version...")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "llama-cpp-python"])

# Try the community CUDA wheels
print("\nInstalling CUDA-enabled llama-cpp-python...")
print("Using community wheels from jllllll...")

# Set environment variable for CUDA
os.environ["CMAKE_ARGS"] = "-DGGML_CUDA=on"

# Install from the community wheels
cmd = [
    sys.executable, "-m", "pip", "install",
    "llama-cpp-python",
    "--upgrade",
    "--force-reinstall",
    "--no-deps",
    "--index-url", "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121"
]

result = subprocess.run(cmd)

if result.returncode == 0:
    # Install dependencies
    print("\nInstalling dependencies...")
    deps = ["numpy", "typing-extensions", "diskcache", "jinja2"]
    for dep in deps:
        subprocess.run([sys.executable, "-m", "pip", "install", dep])
    
    print("\n✓ Success! GPU support should now be enabled.")
    print("\nTo verify, look for these in the output when running:")
    print("  - ggml_cuda_init: CUDA used")
    print("  - llm_load_tensors: using CUDA")
else:
    print("\n✗ Installation failed!")
    print("\nTry manual installation:")
    print("1. Visit: https://github.com/jllllll/llama-cpp-python-cuBLAS-wheels")
    print("2. Download the right wheel for your Python version")
    print("3. Install with: pip install <downloaded_wheel.whl>")