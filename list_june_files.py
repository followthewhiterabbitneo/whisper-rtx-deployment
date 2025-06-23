#!/usr/bin/env python3
"""
List actual files in the audio directory for June 2025
"""

import subprocess
import pymysql

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

print("Checking audio files for June 2025...")

# Method 1: Check via SSH what files actually exist
print("\n1. Checking actual files on server...")
ssh_cmd = [
    "ssh", 
    "estillmane@s40vpsoxweb002",
    "find /var/log/orkaudio.prod.nfs/audio/2025/06 -name '*.wav' -type f | head -20"
]

result = subprocess.run(ssh_cmd, capture_output=True, text=True)
if result.returncode == 0:
    print("Sample files found:")
    for line in result.stdout.strip().split('\n'):
        print(f"  {line}")
else:
    print("Failed to list files")

# Method 2: Check database for sample June recordings
print("\n2. Checking database for June 2025 recordings...")
conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

cursor.execute("""
    SELECT orkUid, filename, duration, timestamp, localParty, remoteParty
    FROM orktape
    WHERE timestamp >= '2025-06-01' 
    AND timestamp <= '2025-06-20'
    AND duration >= 90
    ORDER BY timestamp
    LIMIT 10
""")

records = cursor.fetchall()
print(f"\nFound {len(records)} sample recordings:")
for rec in records:
    print(f"\n  orkUid: {rec['orkUid']}")
    print(f"  Filename: {rec['filename']}")
    print(f"  Duration: {rec['duration']}s")
    print(f"  Parties: {rec['localParty']} <-> {rec['remoteParty']}")

# Check if files match expected format
print("\n3. Checking filename format...")
if records:
    rec = records[0]
    expected_path = f"/var/log/orkaudio.prod.nfs/audio/{rec['filename']}"
    
    check_cmd = [
        "ssh",
        "estillmane@s40vpsoxweb002", 
        f"ls -la {expected_path}"
    ]
    
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ File exists: {expected_path}")
        print(f"  Details: {result.stdout.strip()}")
    else:
        print(f"✗ File not found: {expected_path}")
        print(f"  Error: {result.stderr}")

cursor.close()
conn.close()