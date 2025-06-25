#!/bin/bash
# Create Hollywood environment for screenplay-style transcriptions

echo "🎬 Creating Hollywood environment for screenplay transcriptions..."

# Create virtual environment
python3 -m venv hollywood-env

# Activate it
source hollywood-env/bin/activate

# Install base requirements
pip install --upgrade pip
pip install faster-whisper
pip install numpy scipy
pip install pydub  # For audio channel splitting

echo "✅ Hollywood environment created!"
echo "📝 To activate: source hollywood-env/bin/activate"
echo "🎭 Ready for screenplay-style transcriptions!"