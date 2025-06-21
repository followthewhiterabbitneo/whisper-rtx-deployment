#!/usr/bin/env python3
"""
Test SSH File Copy - Verify we can copy WAV files from s40vpsoxweb002
"""

import os
import subprocess
import tempfile
from pathlib import Path

print("SSH File Copy Test")
print("=" * 50)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

# Step 1: Test SSH connection
print("\n1. Testing SSH connection...")
ssh_test = subprocess.run(
    ['ssh', f'{SSH_USER}@{SSH_HOST}', 'echo "SSH_OK"'],
    capture_output=True, text=True
)

if ssh_test.returncode == 0 and "SSH_OK" in ssh_test.stdout:
    print("✓ SSH connection successful")
else:
    print("✗ SSH connection failed")
    print(f"  Error: {ssh_test.stderr}")
    exit(1)

# Step 2: Use specific WAV file
print("\n2. Using specific WAV file...")
target_filename = "20250620_145645_LOLW.wav"
print(f"  Target: {target_filename}")

# Search for this specific file
find_cmd = f"find {REMOTE_BASE}/audio -name '{target_filename}' -type f"
ssh_find = subprocess.run(
    ['ssh', f'{SSH_USER}@{SSH_HOST}', find_cmd],
    capture_output=True, text=True
)

if ssh_find.returncode == 0 and ssh_find.stdout.strip():
    remote_file = ssh_find.stdout.strip()
    print(f"✓ Found at: {remote_file}")
else:
    print(f"✗ File {target_filename} not found")
    print("\nSearching in expected location...")
    # Try the expected path based on the date in filename (YYYYMMDD)
    # 20250620 = 2025/06/20
    expected_path = f"{REMOTE_BASE}/audio/2025/06/20"
    ls_cmd = f"ls -la {expected_path}/*{target_filename} 2>/dev/null || echo 'Not in expected path'"
    result = subprocess.run(['ssh', f'{SSH_USER}@{SSH_HOST}', ls_cmd], capture_output=True, text=True)
    print(result.stdout)
    
    # List what's actually there
    print(f"\nChecking what files exist in {expected_path}/...")
    ls_cmd2 = f"ls {expected_path}/ 2>/dev/null | grep -E '(LOLW|wav)' | head -10"
    subprocess.run(['ssh', f'{SSH_USER}@{SSH_HOST}', ls_cmd2])
    exit(1)

# Step 3: Get file info
print("\n3. Getting file information...")
stat_cmd = f"stat -c '%s %Y' '{remote_file}'"
ssh_stat = subprocess.run(
    ['ssh', f'{SSH_USER}@{SSH_HOST}', stat_cmd],
    capture_output=True, text=True
)

if ssh_stat.returncode == 0:
    size, mtime = ssh_stat.stdout.strip().split()
    print(f"✓ File size: {int(size):,} bytes")
    print(f"  Modified: {mtime}")
else:
    print("✗ Cannot stat file")

# Step 4: Copy file locally
print("\n4. Copying file via SCP...")
temp_dir = tempfile.mkdtemp(prefix="scream_test_")
local_file = os.path.join(temp_dir, os.path.basename(remote_file))

scp_cmd = [
    'scp',
    '-v',  # Verbose for debugging
    f'{SSH_USER}@{SSH_HOST}:{remote_file}',
    local_file
]

print(f"  Command: {' '.join(scp_cmd)}")
scp_result = subprocess.run(scp_cmd, capture_output=True, text=True)

if scp_result.returncode == 0 and os.path.exists(local_file):
    local_size = os.path.getsize(local_file)
    print(f"✓ File copied successfully: {local_size:,} bytes")
    print(f"  Local path: {local_file}")
else:
    print("✗ SCP failed")
    print(f"  Error: {scp_result.stderr}")
    exit(1)

# Step 5: Verify we can read the WAV file
print("\n5. Verifying WAV file...")
try:
    import wave
    with wave.open(local_file, 'rb') as wav:
        print(f"✓ Valid WAV file")
        print(f"  Channels: {wav.getnchannels()}")
        print(f"  Sample rate: {wav.getframerate()} Hz")
        print(f"  Duration: {wav.getnframes() / wav.getframerate():.1f} seconds")
except Exception as e:
    print(f"⚠ Cannot read as WAV: {e}")
    print("  File might be in a different format or codec")

# Step 6: Cleanup
print("\n6. Cleaning up...")
os.remove(local_file)
os.rmdir(temp_dir)
print("✓ Temp files removed")

print("\n✅ SSH file copy test successful!")
print("\nNext steps:")
print("1. This confirms we can copy files from s40vpsoxweb002")
print("2. SCREAM will use this method to get WAV files")
print("3. Process locally on RTX, then clean up")