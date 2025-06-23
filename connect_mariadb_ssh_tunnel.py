#!/usr/bin/env python3
"""
Connect to MariaDB via SSH tunnel
This works when you can't directly reach s01vdsoxweb047
"""

import subprocess
import time
import pymysql
import sys
import threading
from datetime import datetime, timedelta

print("=" * 60)
print("MARIADB CONNECTION VIA SSH TUNNEL")
print("=" * 60)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"
DB_HOST = "s01vdsoxweb047"
DB_PORT = 3306
LOCAL_PORT = 33306  # Local port for tunnel

DB_CONFIG = {
    'host': 'localhost',  # Connect to localhost through tunnel
    'port': LOCAL_PORT,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

print(f"\n1. Creating SSH tunnel...")
print(f"   SSH: {SSH_USER}@{SSH_HOST}")
print(f"   Tunnel: localhost:{LOCAL_PORT} -> {DB_HOST}:{DB_PORT}")

# Create SSH tunnel
ssh_cmd = [
    'ssh',
    '-N',  # No command
    '-L', f'{LOCAL_PORT}:{DB_HOST}:{DB_PORT}',
    f'{SSH_USER}@{SSH_HOST}'
]

# Start tunnel in background
tunnel_process = subprocess.Popen(ssh_cmd)
print("✓ SSH tunnel started")

# Wait for tunnel to establish
print("Waiting for tunnel to establish...")
time.sleep(2)

try:
    # Connect to database through tunnel
    print(f"\n2. Connecting to MariaDB through tunnel...")
    connection = pymysql.connect(**DB_CONFIG)
    print("✓ Connected successfully!")
    
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Get database info
    cursor.execute("SELECT VERSION() as version")
    result = cursor.fetchone()
    print(f"\nDatabase version: {result['version']}")
    
    # Find Eric Rawlins recordings
    print("\n3. Searching for Eric Rawlins recordings...")
    print("-" * 60)
    
    # First, let's see all recent recordings
    query = """
    SELECT 
        r.orkuid,
        r.filename,
        r.duration,
        r.timestamp,
        r.localparty,
        r.remoteparty
    FROM recordings r
    WHERE 
        r.duration >= 120
        AND r.timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    ORDER BY r.timestamp DESC
    LIMIT 20
    """
    
    cursor.execute(query)
    recordings = cursor.fetchall()
    
    print(f"\nRecent recordings (last 24 hours):")
    for rec in recordings[:5]:
        print(f"\nOrkuid: {rec['orkuid']}")
        print(f"Timestamp: {rec['timestamp']}")
        print(f"Duration: {rec['duration']}s")
        print(f"Parties: {rec['localparty']} <-> {rec['remoteparty']}")
    
    # Now search specifically for Eric Rawlins
    print("\n\n4. Eric Rawlins specific search...")
    
    # Check if Eric Rawlins exists in orkusers
    cursor.execute("""
        SELECT uid, firstname, lastname, userstring 
        FROM orkusers 
        WHERE firstname LIKE '%Eric%' OR lastname LIKE '%Rawlins%'
        LIMIT 10
    """)
    
    users = cursor.fetchall()
    if users:
        print("\nFound users matching 'Eric' or 'Rawlins':")
        for user in users:
            print(f"  - {user['firstname']} {user['lastname']} (uid: {user['uid']}, userstring: {user['userstring']})")
    
    # Alternative search by party name
    print("\n5. Searching by party name containing 'Eric' or 'Rawlins'...")
    cursor.execute("""
        SELECT orkuid, filename, duration, timestamp, localparty, remoteparty
        FROM recordings
        WHERE (localparty LIKE '%Eric%' OR localparty LIKE '%Rawlins%' 
               OR remoteparty LIKE '%Eric%' OR remoteparty LIKE '%Rawlins%')
        AND duration >= 120
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    party_matches = cursor.fetchall()
    if party_matches:
        print(f"\nFound {len(party_matches)} recordings with 'Eric' or 'Rawlins' in party names:")
        for rec in party_matches:
            print(f"\nOrkuid: {rec['orkuid']}")
            print(f"Parties: {rec['localparty']} <-> {rec['remoteparty']}")
            print(f"Duration: {rec['duration']}s")
    
    # Close database connection
    cursor.close()
    connection.close()
    print("\n✓ Database connection closed")
    
except pymysql.Error as e:
    print(f"\n✗ Database error: {e}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    
finally:
    # Kill SSH tunnel
    print("\nClosing SSH tunnel...")
    tunnel_process.terminate()
    tunnel_process.wait()
    print("✓ SSH tunnel closed")

print("\n" + "=" * 60)
print("Use connect_mariadb_direct.py if you can reach s01vdsoxweb047 directly")
print("=" * 60)