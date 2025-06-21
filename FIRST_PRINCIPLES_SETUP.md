# Whisper RTX Deployment - First Principles Setup

## What You Actually Need (Minimum Viable Setup)

### 1. Hardware Requirements
- **GPU**: NVIDIA RTX 4090 (or any CUDA-capable GPU with 8GB+ VRAM)
- **OS**: Windows 11 with WSL2 for development
- **Storage**: ~2GB for model + space for audio files

### 2. Core Dependencies
```bash
# System level
- Python 3.11+
- CUDA 12.x
- cuDNN
- FFmpeg (for audio processing)

# Python packages (minimal)
pip install faster-whisper  # This pulls in all needed dependencies
```

### 3. The Model
You need ONE thing: the Whisper large-v3-turbo model in CTranslate2 format
- Source: `deepdml/faster-whisper-large-v3-turbo-ct2` on Kaggle
- Size: ~1.5GB
- Format: CTranslate2 (optimized for inference)

### 4. Essential Code (Just 3 Files!)

#### File 1: `minimal_transcribe.py`
```python
from faster_whisper import WhisperModel

# Load model
model = WhisperModel("models/faster-whisper-large-v3-turbo-ct2", 
                     device="cuda",
                     compute_type="int8_float16")

# Transcribe
segments, info = model.transcribe("audio.wav", beam_size=5)

# Output
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

#### File 2: `download_model.py`
```python
import kagglehub
import shutil
import os

# Download model from Kaggle
path = kagglehub.model_download("deepdml/faster-whisper-large-v3-turbo-ct2")
print(f"Downloaded to: {path}")

# Copy to local models directory
os.makedirs("models", exist_ok=True)
shutil.copytree(path, "models/faster-whisper-large-v3-turbo-ct2", dirs_exist_ok=True)
```

#### File 3: `batch_process.py`
```python
import os
from pathlib import Path
from faster_whisper import WhisperModel

model = WhisperModel("models/faster-whisper-large-v3-turbo-ct2", 
                     device="cuda",
                     compute_type="int8_float16")

# Process all WAV files
for wav_file in Path("wav").glob("*.wav"):
    print(f"Processing {wav_file.name}...")
    segments, _ = model.transcribe(str(wav_file))
    
    # Save transcription
    output_file = Path("transcriptions") / f"{wav_file.stem}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for segment in segments:
            f.write(f"{segment.text}\n")
```

## Bootstrap Script (Start Fresh in 5 Minutes)

```bash
#!/bin/bash
# bootstrap_whisper_rtx.sh

echo "🚀 Setting up Whisper RTX from scratch..."

# 1. Create directory structure
mkdir -p whisper-rtx-deployment/{models,wav,transcriptions}
cd whisper-rtx-deployment

# 2. Install Python dependencies
pip install faster-whisper kagglehub

# 3. Download the model
python3 << 'EOF'
import kagglehub
import shutil
import os

print("📥 Downloading Whisper turbo model...")
path = kagglehub.model_download("deepdml/faster-whisper-large-v3-turbo-ct2")
shutil.copytree(path, "models/faster-whisper-large-v3-turbo-ct2", dirs_exist_ok=True)
print("✅ Model ready!")
EOF

# 4. Create the transcription script
cat > transcribe.py << 'EOF'
import sys
from faster_whisper import WhisperModel

model = WhisperModel("models/faster-whisper-large-v3-turbo-ct2", 
                     device="cuda", compute_type="int8_float16")

if len(sys.argv) > 1:
    segments, _ = model.transcribe(sys.argv[1])
    for segment in segments:
        print(segment.text)
else:
    print("Usage: python transcribe.py <audio_file>")
EOF

echo "✅ Setup complete! Usage:"
echo "  python transcribe.py your_audio.wav"
```

## What Everything Else Is For

### Nice-to-Have Features (Not Essential)
1. **Error handling** - The scripts in the repo handle edge cases
2. **Progress bars** - Visual feedback for long transcriptions  
3. **Kaggle integration** - For sharing results when network is restricted
4. **Cleanup tools** - For managing disk space
5. **System recon** - To verify GPU/CUDA setup

### The Reality Check
- **80% of the value** comes from just having the model + faster-whisper
- **15% more value** from batch processing capability
- **5% remaining** is convenience features

## Minimal Docker Version
```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip ffmpeg
RUN pip3 install faster-whisper

COPY models /models
COPY transcribe.py /

ENTRYPOINT ["python3", "/transcribe.py"]
```

## The Truth About This Project

You really just need:
1. **The model files** (1.5GB)
2. **faster-whisper** library
3. **~10 lines of Python**

Everything else is quality-of-life improvements!

## To Recreate From Absolute Zero

```bash
# On a fresh RTX 4090 system:
curl -O https://raw.githubusercontent.com/followthewhiterabbitneo/whisper-rtx-deployment/master/bootstrap_whisper_rtx.sh
bash bootstrap_whisper_rtx.sh
# Done in ~5 minutes (mostly model download time)
```