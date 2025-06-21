#!/bin/bash
# Setup Enterprise Connection for SCREAM
# This script establishes SSH tunnel and mounts NFS

echo "=========================================="
echo "SCREAM Enterprise Connection Setup"
echo "=========================================="

# Configuration
SSH_USER="estillmane"
SSH_HOST="s40vpsoxweb002"
NFS_PATH="/var/log/orkaudio.prod.nfs"
LOCAL_MOUNT="/mnt/orkaudio"
DB_PORT="3306"
LOCAL_DB_PORT="33306"  # Local port for tunneled connection

# Step 1: Check if SSH key exists (for passwordless login)
echo ""
echo "1. Checking SSH access..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 $SSH_USER@$SSH_HOST echo "SSH OK" 2>&1 | grep -q "SSH OK"; then
    echo "✓ SSH access confirmed (passwordless)"
else
    echo "✗ SSH access failed. Please ensure:"
    echo "  - Your SSH key is set up for $SSH_USER@$SSH_HOST"
    echo "  - Or you can login without password"
    exit 1
fi

# Step 2: Create SSH tunnel for database
echo ""
echo "2. Creating SSH tunnel for MariaDB..."

# Check if tunnel already exists
if lsof -i :$LOCAL_DB_PORT > /dev/null 2>&1; then
    echo "✓ SSH tunnel already active on port $LOCAL_DB_PORT"
else
    echo "Starting SSH tunnel..."
    ssh -f -N -L $LOCAL_DB_PORT:localhost:$DB_PORT $SSH_USER@$SSH_HOST
    sleep 2
    
    if lsof -i :$LOCAL_DB_PORT > /dev/null 2>&1; then
        echo "✓ SSH tunnel created: localhost:$LOCAL_DB_PORT -> $SSH_HOST:$DB_PORT"
    else
        echo "✗ Failed to create SSH tunnel"
        exit 1
    fi
fi

# Step 3: Mount NFS share
echo ""
echo "3. Mounting NFS share..."

# Create mount point if it doesn't exist
if [ ! -d "$LOCAL_MOUNT" ]; then
    echo "Creating mount point: $LOCAL_MOUNT"
    sudo mkdir -p $LOCAL_MOUNT
fi

# Check if already mounted
if mount | grep -q "$LOCAL_MOUNT"; then
    echo "✓ NFS already mounted at $LOCAL_MOUNT"
else
    echo "Mounting NFS share..."
    # Mount via SSH tunnel
    sudo sshfs -o allow_other,default_permissions,ro \
        $SSH_USER@$SSH_HOST:$NFS_PATH $LOCAL_MOUNT
    
    if mount | grep -q "$LOCAL_MOUNT"; then
        echo "✓ NFS mounted at $LOCAL_MOUNT (read-only)"
    else
        echo "✗ Failed to mount NFS share"
        echo "  Trying alternative mount method..."
        
        # Alternative: Direct NFS mount if on same network
        sudo mount -t nfs -o ro $SSH_HOST:$NFS_PATH $LOCAL_MOUNT 2>/dev/null
        
        if mount | grep -q "$LOCAL_MOUNT"; then
            echo "✓ NFS mounted using direct method"
        else
            echo "✗ Could not mount NFS share"
            exit 1
        fi
    fi
fi

# Step 4: Test database connection
echo ""
echo "4. Testing database connection..."

# Test with Python
python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        port=$LOCAL_DB_PORT,
        user='root',
        password='admin',
        database='oreka'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM orksegment')
    count = cursor.fetchone()[0]
    print(f'✓ Database connection successful: {count:,} recordings found')
    conn.close()
except Exception as e:
    print(f'✗ Database connection failed: {e}')
"

# Step 5: Test file access
echo ""
echo "5. Testing file access..."

# Look for a recent WAV file
SAMPLE_FILE=$(find $LOCAL_MOUNT -name "*.wav" -type f 2>/dev/null | head -1)

if [ -n "$SAMPLE_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$SAMPLE_FILE" 2>/dev/null || stat -f%z "$SAMPLE_FILE" 2>/dev/null)
    echo "✓ Can access recordings: Found $(basename $SAMPLE_FILE) ($FILE_SIZE bytes)"
else
    echo "⚠ No WAV files found - this might be normal if checking a specific subdirectory"
fi

# Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo "SSH Tunnel: localhost:$LOCAL_DB_PORT -> $SSH_HOST:$DB_PORT"
echo "NFS Mount: $LOCAL_MOUNT -> $SSH_HOST:$NFS_PATH"
echo ""
echo "To stop the tunnel later:"
echo "  kill \$(lsof -t -i:$LOCAL_DB_PORT)"
echo ""
echo "To unmount NFS:"
echo "  sudo umount $LOCAL_MOUNT"
echo ""
echo "Now you can run:"
echo "  python test_single_recording.py"
echo "=========================================="