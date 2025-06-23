#!/usr/bin/env python3
"""
Find more Eric Rawlins calls in the database
To be run on RTX 4090 with database access
"""

import subprocess
import json
from datetime import datetime, timedelta

print("=" * 60)
print("FIND ERIC RAWLINS CALLS")
print("=" * 60)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
DB_HOST = "s40vpsoxweb002"
DB_USER = "root"
DB_PASS = "admin"
DB_NAME = "oreka"

# SQL query to find Eric Rawlins calls
# Looking for recent calls (last 7 days) with decent duration
sql_query = """
SELECT 
    r.orkUid,
    r.filename,
    r.duration,
    r.timestamp,
    u.firstname,
    u.lastname
FROM oreka.recordings r
JOIN oreka.orksegments s ON r.orkUid = s.tape_id
JOIN oreka.orkusers u ON s.user_id = u.id
WHERE 
    u.firstname = 'Eric' 
    AND u.lastname = 'Rawlins'
    AND r.duration >= 120
    AND r.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY r.timestamp DESC
LIMIT 10;
"""

# Create SSH tunnel and run query
print("\n1. Setting up SSH tunnel to database...")
print(f"   SSH: {SSH_USER}@{SSH_HOST}")
print(f"   DB:  {DB_HOST}:3306")

# Use SSH to run mysql query directly
ssh_mysql_cmd = [
    'ssh',
    f'{SSH_USER}@{SSH_HOST}',
    f'mysql -h {DB_HOST} -u {DB_USER} -p{DB_PASS} {DB_NAME} -e "{sql_query}"'
]

print("\n2. Querying database for Eric Rawlins calls...")
result = subprocess.run(ssh_mysql_cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("✓ Query successful!")
    print("\nResults:")
    print("-" * 60)
    print(result.stdout)
    
    # Parse results to create file paths
    lines = result.stdout.strip().split('\n')
    if len(lines) > 1:  # Skip header
        print("\n3. Audio file paths:")
        print("-" * 60)
        for line in lines[1:]:
            fields = line.split('\t')
            if len(fields) >= 2:
                orkuid = fields[0]
                filename = fields[1]
                duration = fields[2] if len(fields) > 2 else "unknown"
                
                # Convert filename to path
                # Format: 2025/06/20/14/20250620_145645_LOLW.wav
                if len(orkuid) >= 8:
                    year = orkuid[:4]
                    month = orkuid[4:6]
                    day = orkuid[6:8]
                    hour = orkuid[9:11] if len(orkuid) > 10 else "00"
                    
                    audio_path = f"/var/log/orkaudio.prod.nfs/audio/{year}/{month}/{day}/{hour}/{filename}"
                    print(f"\nOrkuid: {orkuid}")
                    print(f"Duration: {duration}s")
                    print(f"Path: {audio_path}")
else:
    print(f"✗ Query failed: {result.stderr}")

print("\n" + "=" * 60)
print("To process a recording, update TARGET_FILE in process_one_recording.py")
print("=" * 60)