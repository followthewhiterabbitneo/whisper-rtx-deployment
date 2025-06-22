#!/usr/bin/env python3
"""
Switch between CPU and CUDA versions of llama-cpp-python
"""
import subprocess
import sys

def install_cpu_version():
    """Install regular CPU version that supports Gemma 3"""
    print("Installing CPU version of llama-cpp-python (supports Gemma 3)...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "llama-cpp-python"])
    subprocess.run([sys.executable, "-m", "pip", "install", "llama-cpp-python==0.3.2"])
    print("\n✓ CPU version installed - Gemma 3 will work now!")

def install_cuda_version():
    """Install CUDA version for older models"""
    print("Installing CUDA version of llama-cpp-python (for Gemma 2, Llama, etc)...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "llama-cpp-python"])
    subprocess.run([
        sys.executable, "-m", "pip", "install", "llama-cpp-python",
        "--upgrade", "--force-reinstall", "--no-deps",
        "--index-url", "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121"
    ])
    # Install deps
    for dep in ["numpy", "typing-extensions", "diskcache", "jinja2"]:
        subprocess.run([sys.executable, "-m", "pip", "install", dep])
    print("\n✓ CUDA version installed - GPU acceleration for older models!")

if __name__ == "__main__":
    print("Llama-cpp-python Version Switcher")
    print("="*40)
    print("\nCurrent situation:")
    print("- Gemma 3: Requires newer CPU version (0.3.x)")
    print("- Gemma 2/Llama: Can use CUDA version (0.2.x) for GPU")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "cuda":
        install_cuda_version()
    else:
        install_cpu_version()
        print("\nTo switch to CUDA version later, run:")
        print("python switch_llama_versions.py cuda")