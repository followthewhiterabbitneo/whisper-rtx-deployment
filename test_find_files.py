#!/usr/bin/env python3
"""
Test file finding for Windows PowerShell
"""

import sys
import glob
import os

if len(sys.argv) < 2:
    print("Usage: python test_find_files.py pattern")
    print("Example: python test_find_files.py wav_batch_download\\*.wav")
    sys.exit(1)

pattern = sys.argv[1]
print(f"Looking for: {pattern}")
print(f"Current directory: {os.getcwd()}")
print("-" * 50)

# Try different approaches
files = glob.glob(pattern)
print(f"Found {len(files)} files:")
for f in files:
    print(f"  {f}")

# Also try with forward slashes
if "\\" in pattern:
    pattern2 = pattern.replace("\\", "/")
    files2 = glob.glob(pattern2)
    if files2 and files2 != files:
        print(f"\nWith forward slashes ({pattern2}):")
        print(f"Found {len(files2)} files")