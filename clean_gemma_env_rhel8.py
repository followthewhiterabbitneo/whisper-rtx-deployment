#!/usr/bin/env python3
"""
Clean up Modular/magic conflicts and reinstall llama-cpp-python on RHEL8
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return output"""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if check and result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    print("=== Cleaning Gemma Environment on RHEL8 ===")
    
    # Check if we're in the venv
    if "gemma-env" not in sys.prefix:
        print("ERROR: Please activate the gemma-env first:")
        print("source /moneyball/gemma-env/bin/activate")
        sys.exit(1)
    
    print("\n1. Checking for Modular/magic installations...")
    
    # Check for magic/modular packages
    run_command("pip list | grep -i magic", check=False)
    run_command("pip list | grep -i modular", check=False)
    run_command("pip list | grep -i mojo", check=False)
    
    print("\n2. Checking system paths for magic...")
    # Check common Modular installation paths
    modular_paths = [
        "$HOME/.modular",
        "$HOME/.local/bin/magic",
        "/usr/local/bin/magic",
        "$HOME/.magic"
    ]
    
    for path in modular_paths:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            print(f"Found: {expanded}")
    
    print("\n3. Current llama-cpp-python status...")
    run_command("pip show llama-cpp-python", check=False)
    
    print("\n=== Cleanup Steps ===")
    print("To clean up, run these commands:")
    print()
    print("# 1. Uninstall any conflicting packages")
    print("pip uninstall -y magic modular mojo llama-cpp-python")
    print()
    print("# 2. Remove Modular directories (if they exist)")
    print("rm -rf ~/.modular ~/.magic")
    print()
    print("# 3. Clean pip cache")
    print("pip cache purge")
    print()
    print("# 4. Reinstall llama-cpp-python with GPU support")
    print("CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python --force-reinstall --no-cache-dir")
    print()
    print("# 5. Alternative: Install CPU-only version (if GPU version fails)")
    print("pip install llama-cpp-python --force-reinstall --no-cache-dir")
    print()
    print("# 6. Verify the model file")
    print("file /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf")
    print("ls -lh /moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf")

if __name__ == "__main__":
    main()