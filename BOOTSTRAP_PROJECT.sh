#!/bin/bash
# BOOTSTRAP_PROJECT.sh - Complete setup from scratch
# This script will get you to the exact point of successfully transcribing one file

set -e  # Exit on error

echo "=================================================="
echo "SCREAM PROJECT BOOTSTRAP"
echo "=================================================="
echo "This will set up everything needed to transcribe"
echo "your first recording, just like we did."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "process_one_recording.py" ]; then
    echo "❌ Error: Run this script from the whisper-rtx-deployment directory"
    exit 1
fi

# Step 1: Check Python
echo -e "\n1. Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "✓ Python $PYTHON_VERSION found"
else
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Step 2: Install dependencies
echo -e "\n2. Installing Python dependencies..."
pip install -r requirements.txt || pip install faster-whisper pymysql paramiko

# Step 3: Check/Download Whisper model
echo -e "\n3. Checking Whisper model..."
MODEL_PATH="models/faster-whisper-large-v3-turbo-ct2"

if [ -f "$MODEL_PATH/model.bin" ]; then
    echo "✓ Model already exists"
else
    echo "📥 Downloading Whisper model (1.5GB)..."
    python3 << 'EOF'
import os
try:
    import kagglehub
    print("Using kagglehub to download model...")
    path = kagglehub.model_download("deepdml/faster-whisper-large-v3-turbo-ct2")
    print(f"Downloaded to: {path}")
    # You'll need to copy from kagglehub cache to local models/ directory
except:
    print("❌ kagglehub not available")
    print("Please download the model manually:")
    print("1. Go to https://www.kaggle.com/models/deepdml/faster-whisper-large-v3-turbo-ct2")
    print("2. Download and extract to models/faster-whisper-large-v3-turbo-ct2/")
EOF
fi

# Step 4: Test SSH connection
echo -e "\n4. Testing SSH connection to s40vpsoxweb002..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 estillmane@s40vpsoxweb002 'echo "SSH_OK"' &> /dev/null; then
    echo "✓ SSH connection working"
else
    echo "❌ SSH connection failed"
    echo "Please ensure you can SSH to estillmane@s40vpsoxweb002 without password"
    echo "Run: ssh-copy-id estillmane@s40vpsoxweb002"
    exit 1
fi

# Step 5: Create output directory
echo -e "\n5. Creating directories..."
mkdir -p test_output
mkdir -p temp
echo "✓ Directories created"

# Step 6: Quick GPU check
echo -e "\n6. Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    echo "✓ GPU found: $GPU_NAME"
else
    echo "⚠️  nvidia-smi not found - GPU may not be available"
    echo "   Transcription will use CPU (slower)"
fi

# Step 7: Test file access
echo -e "\n7. Checking access to test file..."
TEST_FILE="/var/log/orkaudio.prod.nfs/audio/2025/06/20/14/20250620_145645_LOLW.wav"
if ssh estillmane@s40vpsoxweb002 "ls -la '$TEST_FILE'" &> /dev/null; then
    echo "✓ Test file accessible on remote server"
else
    echo "⚠️  Test file not found at expected location"
    echo "   You may need to update the filename in process_one_recording.py"
fi

# Step 8: Summary
echo -e "\n=================================================="
echo "✅ BOOTSTRAP COMPLETE!"
echo "=================================================="
echo ""
echo "You can now run:"
echo "  python process_one_recording.py"
echo ""
echo "This will:"
echo "1. Copy 20250620_145645_LOLW.wav from s40vpsoxweb002"
echo "2. Transcribe it using Whisper on your GPU"
echo "3. Save the transcript to test_output/"
echo ""
echo "To process a different file:"
echo "  Edit TARGET_FILE in process_one_recording.py"
echo ""
echo "For full pipeline with database:"
echo "  python test_single_recording.py"
echo "=================================================="