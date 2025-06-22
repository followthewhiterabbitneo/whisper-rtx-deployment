#!/usr/bin/env python3
"""
Check where packages are being installed in the virtual environment
"""
import os
import sys
import site
import subprocess
from pathlib import Path

def check_venv_locations():
    print("=== Virtual Environment Location Check ===")
    
    # Check if in venv
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: Not in a virtual environment!")
        print("Activate with: source /moneyball/gemma-env/bin/activate")
        return
    
    print(f"Python executable: {sys.executable}")
    print(f"Python prefix: {sys.prefix}")
    print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    
    # Check site-packages location
    print("\nSite packages locations:")
    for path in site.getsitepackages():
        print(f"  - {path}")
        if os.path.exists(path):
            # Check disk usage
            try:
                result = subprocess.run(
                    ["du", "-sh", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                if result.returncode == 0:
                    size = result.stdout.strip().split('\t')[0]
                    print(f"    Size: {size}")
            except:
                pass
    
    # Check pip cache location
    print("\nPip cache location:")
    result = subprocess.run(
        ["pip", "cache", "dir"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if result.returncode == 0:
        cache_dir = result.stdout.strip()
        print(f"  {cache_dir}")
        if os.path.exists(cache_dir):
            try:
                result = subprocess.run(
                    ["du", "-sh", cache_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                if result.returncode == 0:
                    size = result.stdout.strip().split('\t')[0]
                    print(f"  Size: {size}")
            except:
                pass
    
    # Check disk space
    print("\nDisk space check:")
    # Check /moneyball
    result = subprocess.run(
        ["df", "-h", "/moneyball"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if result.returncode == 0:
        print("Moneyball partition:")
        print(result.stdout)
    
    # Check home directory
    result = subprocess.run(
        ["df", "-h", os.path.expanduser("~")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if result.returncode == 0:
        print("Home directory partition:")
        print(result.stdout)
    
    # Recommendations
    print("\n=== Recommendations ===")
    if "/moneyball" in sys.prefix:
        print("✓ Good: Virtual environment is in /moneyball")
    else:
        print("⚠ Warning: Virtual environment is NOT in /moneyball")
        print("  Packages will be installed in:", sys.prefix)
    
    print("\nTo save space, you can:")
    print("1. Clear pip cache: pip cache purge")
    print("2. Remove unused packages: pip list | grep -v gemma")
    print("3. Use --no-cache-dir when installing: pip install --no-cache-dir package_name")

if __name__ == "__main__":
    check_venv_locations()