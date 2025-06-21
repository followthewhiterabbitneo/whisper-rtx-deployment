#!/usr/bin/env python3
"""
Find specific recording file on s40vpsoxweb002
"""

import subprocess
import sys

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
REMOTE_BASE = "/var/log/orkaudio.prod.nfs"

# File we're looking for
target_file = "20250620_145645_LOLW.wav"

print(f"Searching for: {target_file}")
print("=" * 50)

# Test SSH connection first
print("\nTesting SSH connection...")
test_cmd = ['ssh', '-v', f'{SSH_USER}@{SSH_HOST}', 'echo "SSH_OK"']
test_result = subprocess.run(test_cmd, capture_output=True, text=True)

if "SSH_OK" in test_result.stdout:
    print("✓ SSH connection successful")
else:
    print("✗ SSH connection failed")
    print(f"STDOUT: {test_result.stdout}")
    print(f"STDERR: {test_result.stderr[:500]}")  # First 500 chars
    print(f"Return code: {test_result.returncode}")
    sys.exit(1)

# Extract date from filename (YYYYMMDD_HHMMSS_XXXX.wav)
# 20250620 = June 20, 2025 (yesterday)
year = target_file[0:4]    # 2025
month = target_file[4:6]   # 06
day = target_file[6:8]     # 20
hour = target_file[9:11]   # 14

print(f"Expected date: {year}/{month}/{day}")
print(f"Expected hour: {hour}")

# Search strategies
searches = [
    # 1. Full search (might be slow)
    (f"find {REMOTE_BASE}/audio -name '{target_file}' -type f 2>/dev/null | head -1", 
     "Full search in audio directory"),
    
    # 2. Expected path based on date
    (f"ls -la {REMOTE_BASE}/audio/{year}/{month}/{day}/{hour}/{target_file} 2>/dev/null",
     f"Direct path: audio/{year}/{month}/{day}/{hour}/"),
    
    # 3. Check all hours of that day
    (f"ls -la {REMOTE_BASE}/audio/{year}/{month}/{day}/*/{target_file} 2>/dev/null",
     f"All hours on {year}/{month}/{day}"),
    
    # 4. Search by orkuid
    (f"find {REMOTE_BASE}/audio -name '*LOLW.wav' -type f 2>/dev/null | head -5",
     "Search for any file ending with LOLW.wav"),
    
    # 5. Check if date directory exists
    (f"ls -ld {REMOTE_BASE}/audio/{year}/{month}/{day}/ 2>/dev/null",
     f"Check if date directory exists"),
]

# Try each search
for cmd, description in searches:
    print(f"\n{description}:")
    print(f"  Command: {cmd}")
    
    # Show what we're running
    full_cmd = ['ssh', f'{SSH_USER}@{SSH_HOST}', cmd]
    print(f"  Running: ssh {SSH_USER}@{SSH_HOST} '{cmd}'")
    
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    
    print(f"  Return code: {result.returncode}")
    
    if result.stdout.strip():
        print(f"  ✓ STDOUT: {result.stdout.strip()}")
        if target_file in result.stdout:
            print(f"\n✅ FOUND! File location confirmed")
            break
    else:
        print(f"  ✗ No stdout results")
        
    if result.stderr.strip():
        print(f"  STDERR: {result.stderr.strip()}")

# Also check in database
print("\n" + "=" * 50)
print("Checking database for this recording...")

db_query = f"""
mysql -h localhost -u root -padmin oreka -e "
SELECT s.orkuid, s.timestamp, s.duration, t.filename 
FROM orksegment s 
JOIN orktape t ON s.orkuid = t.orkuid 
WHERE s.orkuid = 'LOLW' 
   OR t.filename LIKE '%LOLW%'
LIMIT 5;
"
"""

print("Running database query...")
db_result = subprocess.run(
    ['ssh', f'{SSH_USER}@{SSH_HOST}', db_query],
    capture_output=True, text=True
)

if db_result.stdout:
    print("Database results:")
    print(db_result.stdout)
else:
    print("No database results found")