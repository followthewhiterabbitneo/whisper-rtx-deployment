#!/usr/bin/env python3
"""
Quick check for specific file - no searching, just direct path
"""

import subprocess
import sys

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

# File we want
target_file = "20250620_145645_LOLW.wav"

# Expected path: /var/log/orkaudio.prod.nfs/audio/2025/06/20/14/20250620_145645_LOLW.wav
expected_path = f"{REMOTE_BASE}/audio/2025/06/20/14/{target_file}"

print(f"Checking: {expected_path}")
print("-" * 60)

# Direct check
cmd = f"ls -la '{expected_path}' 2>&1"
result = subprocess.run(
    ['ssh', f'{SSH_USER}@{SSH_HOST}', cmd],
    capture_output=True, text=True
)

if result.returncode == 0 and target_file in result.stdout:
    print("✅ FILE FOUND!")
    print(result.stdout.strip())
    
    # Get file size in human readable format
    size_cmd = f"ls -lh '{expected_path}' | awk '{{print $5}}'"
    size_result = subprocess.run(
        ['ssh', f'{SSH_USER}@{SSH_HOST}', size_cmd],
        capture_output=True, text=True
    )
    print(f"\nFile size: {size_result.stdout.strip()}")
    
else:
    print("❌ File not found at expected location")
    
    # Check what's in the hour directory
    print("\nChecking what's in the 14 hour directory...")
    ls_cmd = f"ls {REMOTE_BASE}/audio/2025/06/20/14/ | grep -E '(LOLW|\.wav$)' | head -5"
    ls_result = subprocess.run(
        ['ssh', f'{SSH_USER}@{SSH_HOST}', ls_cmd],
        capture_output=True, text=True
    )
    
    if ls_result.stdout:
        print("Files found in hour 14:")
        print(ls_result.stdout)
    else:
        print("No files found. Checking what hours exist...")
        hours_cmd = f"ls -d {REMOTE_BASE}/audio/2025/06/20/*/"
        hours_result = subprocess.run(
            ['ssh', f'{SSH_USER}@{SSH_HOST}', hours_cmd],
            capture_output=True, text=True
        )
        print("Available hours:")
        print(hours_result.stdout)