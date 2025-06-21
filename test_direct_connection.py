#!/usr/bin/env python3
"""
Test Direct Connection - Simplified version
Assumes you're on the same network as s40vpsoxweb002
"""

import os
import sys

print("SCREAM Direct Connection Test")
print("=" * 40)

# Test 1: Can we SSH?
print("\n1. Testing SSH connection...")
ssh_test = os.system("ssh estillmane@s40vpsoxweb002 'echo SSH_OK' 2>&1 | grep -q SSH_OK")
if ssh_test == 0:
    print("✓ SSH connection successful")
else:
    print("✗ Cannot SSH to s40vpsoxweb002")
    print("  Make sure you can: ssh estillmane@s40vpsoxweb002")
    sys.exit(1)

# Test 2: Can we see the NFS directory via SSH?
print("\n2. Checking NFS directory...")
nfs_check = os.popen("ssh estillmane@s40vpsoxweb002 'ls -la /var/log/orkaudio.prod.nfs/ | head -5'").read()
if nfs_check:
    print("✓ NFS directory accessible:")
    print(nfs_check)
else:
    print("✗ Cannot access NFS directory")

# Test 3: Database connection via SSH tunnel
print("\n3. Setting up database connection...")
print("Creating SSH tunnel: localhost:33306 -> s40vpsoxweb002:3306")

# Kill any existing tunnel
os.system("pkill -f 'ssh.*33306:localhost:3306'")

# Create new tunnel
tunnel_cmd = "ssh -f -N -L 33306:localhost:3306 estillmane@s40vpsoxweb002"
if os.system(tunnel_cmd) == 0:
    print("✓ SSH tunnel created")
else:
    print("✗ Failed to create SSH tunnel")
    sys.exit(1)

# Test database
print("\n4. Testing database connection...")
try:
    import pymysql
    conn = pymysql.connect(
        host='localhost',
        port=33306,
        user='root',
        password='admin',
        database='oreka'
    )
    cursor = conn.cursor()
    
    # Get recent recording
    cursor.execute("""
        SELECT COUNT(*) as total,
               MAX(timestamp) as latest
        FROM orksegment
        WHERE duration >= 120
    """)
    result = cursor.fetchone()
    print(f"✓ Database connected: {result[0]:,} calls found")
    print(f"  Latest call: {result[1]}")
    
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# Test 4: Mount NFS locally
print("\n5. Mounting NFS share locally...")
local_mount = "/mnt/orkaudio"

if os.path.exists(local_mount) and os.listdir(local_mount):
    print(f"✓ NFS already mounted at {local_mount}")
else:
    print(f"Mounting to {local_mount}...")
    os.system(f"sudo mkdir -p {local_mount}")
    
    # Try SSHFS first
    mount_cmd = f"sudo sshfs -o allow_other,ro estillmane@s40vpsoxweb002:/var/log/orkaudio.prod.nfs {local_mount}"
    if os.system(mount_cmd) == 0:
        print(f"✓ Mounted via SSHFS")
    else:
        # Try direct NFS
        mount_cmd = f"sudo mount -t nfs -o ro s40vpsoxweb002:/var/log/orkaudio.prod.nfs {local_mount}"
        if os.system(mount_cmd) == 0:
            print(f"✓ Mounted via NFS")
        else:
            print("✗ Failed to mount - will access files via SSH")

print("\n✅ Connection test complete!")
print("\nNext: Run python test_single_recording.py")