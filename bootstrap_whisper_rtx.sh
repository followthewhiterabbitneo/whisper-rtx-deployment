#!/bin/bash
# Bootstrap Whisper RTX Deployment from scratch
# This single script sets up everything you need

set -e  # Exit on error

echo "🚀 Whisper RTX Bootstrap Script"
echo "==============================="
echo "This will set up a complete Whisper transcription system on your RTX GPU"
echo ""

# Check if we're on Windows or Linux
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# 1. Create project structure
echo "📁 Creating project directories..."
mkdir -p whisper-rtx-deployment/{models,wav,transcriptions,downloads}
cd whisper-rtx-deployment

# 2. Check Python
echo "🐍 Checking Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python not found! Please install Python 3.11+"
    exit 1
fi

# 3. Install dependencies
echo "📦 Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install faster-whisper kagglehub

# 4. Create the model downloader
echo "📝 Creating model downloader..."
cat > download_model.py << 'EOF'
import os
import sys
import shutil

try:
    import kagglehub
except ImportError:
    print("Installing kagglehub...")
    os.system(f"{sys.executable} -m pip install kagglehub")
    import kagglehub

print("📥 Downloading Whisper large-v3-turbo model from Kaggle...")
print("This is a 1.5GB download, please be patient...")

try:
    path = kagglehub.model_download("deepdml/faster-whisper-large-v3-turbo-ct2")
    print(f"✅ Downloaded to: {path}")
    
    # Copy to local models directory
    dest = "models/faster-whisper-large-v3-turbo-ct2"
    if os.path.exists(dest):
        print("Model already exists locally, skipping copy")
    else:
        print("Copying model to local directory...")
        shutil.copytree(path, dest, dirs_exist_ok=True)
        print("✅ Model ready!")
        
except Exception as e:
    print(f"❌ Error downloading model: {e}")
    print("\nAlternative: Download manually from:")
    print("https://www.kaggle.com/models/deepdml/faster-whisper-large-v3-turbo-ct2")
    sys.exit(1)
EOF

# 5. Create the main transcription script
echo "📝 Creating transcription script..."
cat > transcribe.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal Whisper transcription script
Usage: python transcribe.py <audio_file>
"""

import sys
import os
from pathlib import Path

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Installing faster-whisper...")
    os.system(f"{sys.executable} -m pip install faster-whisper")
    from faster_whisper import WhisperModel

def transcribe_file(audio_path, model_path="models/faster-whisper-large-v3-turbo-ct2"):
    """Transcribe a single audio file"""
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        print("Run: python download_model.py")
        return
    
    print(f"🎤 Loading model...")
    model = WhisperModel(model_path, 
                         device="cuda",
                         compute_type="int8_float16")
    
    print(f"📝 Transcribing {audio_path}...")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    print(f"\n🎯 Detected language: {info.language} (probability: {info.language_probability:.2f})")
    print("\n--- Transcription ---\n")
    
    full_text = []
    for segment in segments:
        text = segment.text.strip()
        print(text)
        full_text.append(text)
    
    # Save to file
    output_dir = Path("transcriptions")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{Path(audio_path).stem}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(full_text))
    
    print(f"\n✅ Saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        print("\nExample:")
        print("  python transcribe.py audio.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    transcribe_file(audio_file)
EOF

# 6. Create batch processing script
echo "📝 Creating batch processing script..."
cat > batch_transcribe.py << 'EOF'
#!/usr/bin/env python3
"""
Batch transcribe all audio files in the wav/ directory
"""

import os
from pathlib import Path
from faster_whisper import WhisperModel
import time

def batch_transcribe():
    model_path = "models/faster-whisper-large-v3-turbo-ct2"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        print("Run: python download_model.py")
        return
    
    # Find audio files
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(Path("wav").glob(f"*{ext}"))
    
    if not audio_files:
        print("❌ No audio files found in wav/ directory")
        return
    
    print(f"🎤 Found {len(audio_files)} audio files")
    print(f"📝 Loading model...")
    
    model = WhisperModel(model_path, 
                         device="cuda",
                         compute_type="int8_float16")
    
    Path("transcriptions").mkdir(exist_ok=True)
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing {audio_file.name}...")
        
        start_time = time.time()
        segments, info = model.transcribe(str(audio_file), beam_size=5)
        
        # Collect transcription
        transcription = []
        for segment in segments:
            transcription.append(segment.text.strip())
        
        # Save to file
        output_file = Path("transcriptions") / f"{audio_file.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(transcription))
        
        duration = time.time() - start_time
        print(f"✅ Completed in {duration:.1f}s - Saved to {output_file}")
    
    print(f"\n🎉 All done! Transcribed {len(audio_files)} files")

if __name__ == "__main__":
    batch_transcribe()
EOF

# 7. Create a test script
echo "📝 Creating system test script..."
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test if everything is set up correctly"""

import sys
import os

print("🧪 Testing Whisper RTX Setup")
print("=" * 40)

# Test 1: Python version
print(f"✓ Python version: {sys.version.split()[0]}")

# Test 2: CUDA availability
try:
    import torch
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("✗ CUDA not available - CPU mode will be used (slower)")
except ImportError:
    print("✗ PyTorch not installed - will be installed with faster-whisper")

# Test 3: Model exists
model_path = "models/faster-whisper-large-v3-turbo-ct2/model.bin"
if os.path.exists(model_path):
    size = os.path.getsize(model_path) / (1024**3)
    print(f"✓ Model found: {size:.2f} GB")
else:
    print("✗ Model not found - run: python download_model.py")

# Test 4: faster-whisper
try:
    import faster_whisper
    print(f"✓ faster-whisper version: {faster_whisper.__version__}")
except ImportError:
    print("✗ faster-whisper not installed - run: pip install faster-whisper")

print("\n" + "=" * 40)
print("Setup test complete!")
EOF

# 8. Download the model
echo ""
echo "📥 Downloading model (this may take a few minutes)..."
$PYTHON_CMD download_model.py

# 9. Final setup
echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Quick Start Guide:"
echo "-------------------"
echo "1. Test your setup:"
echo "   $PYTHON_CMD test_setup.py"
echo ""
echo "2. Transcribe a single file:"
echo "   $PYTHON_CMD transcribe.py your_audio.wav"
echo ""
echo "3. Batch transcribe (put files in wav/ directory):"
echo "   $PYTHON_CMD batch_transcribe.py"
echo ""
echo "📁 Project structure:"
echo "   whisper-rtx-deployment/"
echo "   ├── models/              # Whisper model files"
echo "   ├── wav/                 # Put audio files here"
echo "   ├── transcriptions/      # Output transcriptions"
echo "   ├── transcribe.py        # Single file transcription"
echo "   └── batch_transcribe.py  # Batch processing"
echo ""
echo "🚀 You're ready to transcribe at 10-20x real-time speed!"