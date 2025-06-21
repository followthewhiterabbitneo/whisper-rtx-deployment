#!/usr/bin/env python3
"""
Simple SSH connection test
"""

import subprocess
import os

print("SSH Connection Test")
print("=" * 40)

# Configuration
SSH_USER = "estillmane"
SSH_HOST = "s40vpsoxweb002"

# Test 1: Basic SSH
print("\n1. Basic SSH test...")
cmd = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 
       f'{SSH_USER}@{SSH_HOST}', 'echo "Connected"']
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Command: {' '.join(cmd)}")
print(f"Return code: {result.returncode}")
print(f"STDOUT: {result.stdout}")
print(f"STDERR: {result.stderr}")

# Test 2: Check hostname
print("\n2. Getting hostname...")
cmd2 = ['ssh', f'{SSH_USER}@{SSH_HOST}', 'hostname']
result2 = subprocess.run(cmd2, capture_output=True, text=True)
print(f"Hostname: {result2.stdout.strip() if result2.returncode == 0 else 'FAILED'}")

# Test 3: Check directory
print("\n3. Checking NFS directory...")
cmd3 = ['ssh', f'{SSH_USER}@{SSH_HOST}', 'ls -ld /var/log/orkaudio.prod.nfs/']
result3 = subprocess.run(cmd3, capture_output=True, text=True)
print(f"Directory: {result3.stdout.strip() if result3.returncode == 0 else 'FAILED'}")

# Test 4: Simple Python SSH
print("\n4. Python SSH test...")
try:
    output = subprocess.check_output(
        ['ssh', f'{SSH_USER}@{SSH_HOST}', 'echo "Python SSH OK"'],
        text=True
    )
    print(f"✓ Python SSH working: {output.strip()}")
except subprocess.CalledProcessError as e:
    print(f"✗ Python SSH failed: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\nDone!")