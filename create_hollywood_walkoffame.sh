#!/bin/bash
#
# HOLLYWOOD WALK OF FAME - First Principles Build
# Creates a complete Hollywood transcription environment from scratch
# With root privileges for system-wide star installation
#

echo "🌟 HOLLYWOOD WALK OF FAME BUILDER 🌟"
echo "===================================="
echo "Creating your transcription studio from first principles..."
echo ""

# Check if we can sudo without password
echo "🔐 Checking sudo privileges..."
if sudo -n true 2>/dev/null; then
    echo "✅ Passwordless sudo available!"
else
    echo "❌ This script requires passwordless sudo"
    echo "   Add to /etc/sudoers: $USER ALL=(ALL) NOPASSWD: ALL"
    exit 1
fi

# Function to print star
print_star() {
    echo "⭐ $1"
}

# Create Hollywood base directory
HOLLYWOOD_BASE="/opt/hollywood"
print_star "Creating Hollywood Boulevard at $HOLLYWOOD_BASE"
sudo mkdir -p $HOLLYWOOD_BASE
sudo chown $USER:$USER $HOLLYWOOD_BASE

# Create directory structure
print_star "Building the Walk of Fame structure..."
mkdir -p $HOLLYWOOD_BASE/{studio,stars,scripts,models,output}
mkdir -p $HOLLYWOOD_BASE/output/{screenplay,detailed,json}

# Create virtual environment
print_star "Setting up the Hollywood Studio environment..."
cd $HOLLYWOOD_BASE
python3 -m venv studio-env

# Activate and setup
source studio-env/bin/activate

# Upgrade pip first
print_star "Upgrading the studio equipment..."
pip install --upgrade pip setuptools wheel

# Install core dependencies
print_star "Installing A-list dependencies..."
pip install numpy scipy
pip install faster-whisper
pip install pydub  # For audio manipulation
pip install wave

# Create the main star - our transcription script
print_star "Creating the main star script..."
cat > $HOLLYWOOD_BASE/scripts/hollywood_transcribe.py << 'EOF'
#!/usr/bin/env python3
"""
🌟 HOLLYWOOD TRANSCRIPTION STUDIO 🌟
First Principles Screenplay Transcription
"""

import os
import sys
import wave
import json
import argparse
from datetime import datetime
from pathlib import Path
from faster_whisper import WhisperModel

class HollywoodTranscriber:
    def __init__(self, model_path=None):
        self.model_path = model_path or "/opt/hollywood/models/faster-whisper-large-v3-turbo-ct2"
        self.device = "cuda"
        self.compute_type = "int8_float16"
        
    def roll_camera(self):
        """Initialize the model - ACTION!"""
        print("🎬 LIGHTS, CAMERA, ACTION!")
        print("Loading the star performer (Whisper model)...")
        self.model = WhisperModel(
            self.model_path, 
            device=self.device, 
            compute_type=self.compute_type
        )
        print("✨ Star is ready for their close-up!")
        
    def direct_scene(self, audio_file):
        """Direct the transcription scene"""
        print(f"\n🎭 Scene: {Path(audio_file).name}")
        print("="*50)
        
        # Get audio info
        with wave.open(audio_file, 'rb') as wav:
            channels = wav.getnchannels()
            duration = wav.getnframes() / wav.getframerate()
            print(f"📽️  Format: {channels} channel(s), {duration:.1f} seconds")
        
        # Transcribe
        print("\n🎤 Rolling... (transcribing)")
        segments, info = self.model.transcribe(
            audio_file,
            beam_size=5,
            language="en",
            condition_on_previous_text=True,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=800,
                speech_pad_ms=200
            )
        )
        
        return list(segments), info
        
    def write_screenplay(self, segments, audio_file):
        """Write the screenplay in Hollywood style"""
        base_name = Path(audio_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Screenplay format
        screenplay = []
        screenplay.append("="*80)
        screenplay.append("🎬 HOLLYWOOD SCREENPLAY TRANSCRIPT 🎬")
        screenplay.append(f"Production: {base_name}")
        screenplay.append(f"Take: {timestamp}")
        screenplay.append("="*80)
        screenplay.append("")
        
        # Detect speaker changes based on pauses
        current_speaker = "ACTOR A"
        for i, segment in enumerate(segments):
            # Check for speaker change
            if i > 0:
                pause = segment.start - segments[i-1].end
                if pause > 1.0:  # 1 second pause = likely speaker change
                    current_speaker = "ACTOR B" if current_speaker == "ACTOR A" else "ACTOR A"
            
            screenplay.append(f"\n{current_speaker}:")
            screenplay.append(f"  {segment.text.strip()}")
            screenplay.append(f"  [Take {i+1}: {segment.start:.1f}s - {segment.end:.1f}s]")
        
        # Save screenplay
        output_file = f"/opt/hollywood/output/screenplay/{base_name}_{timestamp}_screenplay.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(screenplay))
            
        print(f"\n🌟 Screenplay saved: {output_file}")
        return output_file
        
    def create_credits(self, segments, info, audio_file):
        """Create the closing credits (metadata)"""
        base_name = Path(audio_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        credits = {
            "production": base_name,
            "timestamp": timestamp,
            "duration": info.duration,
            "language": info.language,
            "scenes": len(segments),
            "stars": ["ACTOR A", "ACTOR B"],
            "director": "Whisper AI",
            "studio": "Hollywood Transcription Studios"
        }
        
        credits_file = f"/opt/hollywood/output/json/{base_name}_{timestamp}_credits.json"
        with open(credits_file, 'w') as f:
            json.dump(credits, f, indent=2)
            
        print(f"📽️  Credits saved: {credits_file}")
        return credits_file

def main():
    parser = argparse.ArgumentParser(description="🌟 Hollywood Transcription Studio")
    parser.add_argument("audio_file", help="Audio file to transcribe")
    parser.add_argument("--model", help="Model path", default=None)
    args = parser.parse_args()
    
    # Create the star
    star = HollywoodTranscriber(args.model)
    
    # Roll camera
    star.roll_camera()
    
    # Direct the scene
    segments, info = star.direct_scene(args.audio_file)
    
    # Write screenplay
    screenplay = star.write_screenplay(segments, args.audio_file)
    
    # Create credits
    credits = star.create_credits(segments, info, args.audio_file)
    
    print("\n🎬 That's a wrap!")
    print("="*50)

if __name__ == "__main__":
    main()
EOF

# Make it executable
chmod +x $HOLLYWOOD_BASE/scripts/hollywood_transcribe.py

# Create a system-wide command
print_star "Installing star on the Walk of Fame..."
sudo cat > /tmp/hollywood << EOF
#!/bin/bash
source /opt/hollywood/studio-env/bin/activate
python /opt/hollywood/scripts/hollywood_transcribe.py "\$@"
EOF
sudo mv /tmp/hollywood /usr/local/bin/
sudo chmod +x /usr/local/bin/hollywood

# Create setup status file
print_star "Recording this historic moment..."
cat > $HOLLYWOOD_BASE/WALK_OF_FAME.txt << EOF
🌟 HOLLYWOOD WALK OF FAME 🌟
========================

Installation Date: $(date)
Installed By: $USER
Location: $HOLLYWOOD_BASE

Directory Structure:
- studio/      : Virtual environment
- stars/       : Future star scripts
- scripts/     : Main transcription scripts  
- models/      : AI model storage
- output/      : Transcription results
  - screenplay/: Screenplay format outputs
  - detailed/  : Detailed transcriptions
  - json/      : Metadata and credits

To use:
  hollywood <audio_file.wav>

Or directly:
  source /opt/hollywood/studio-env/bin/activate
  python /opt/hollywood/scripts/hollywood_transcribe.py <audio_file>

Remember: This is YOUR Walk of Fame!
EOF

# Create README
print_star "Writing the Hollywood sign..."
cat > $HOLLYWOOD_BASE/README.md << EOF
# 🌟 Hollywood Transcription Studios 🌟

Welcome to your personal Walk of Fame for audio transcription!

## Quick Start

\`\`\`bash
# From anywhere in the system:
hollywood your_audio.wav

# Or activate the studio:
source /opt/hollywood/studio-env/bin/activate
\`\`\`

## Features

- 🎬 Screenplay-style formatting
- 🎭 Automatic speaker detection (Actor A/B)
- 📽️ Professional timestamps
- 🌟 Hollywood-themed output

## Directory Structure

- **studio/** - Virtual environment (your production crew)
- **scripts/** - Transcription scripts (your directors)
- **models/** - AI models (your stars)
- **output/** - Results (your productions)

## Adding Your Model

Place your Whisper model in:
/opt/hollywood/models/

Then use:
\`\`\`bash
hollywood --model /opt/hollywood/models/your-model audio.wav
\`\`\`

---
*Created with ⭐ on the Hollywood Walk of Fame*
EOF

# Final message
echo ""
echo "🌟🌟🌟 HOLLYWOOD WALK OF FAME COMPLETE! 🌟🌟🌟"
echo ""
echo "Your transcription studio is ready at: $HOLLYWOOD_BASE"
echo ""
echo "To transcribe from anywhere:"
echo "  hollywood your_audio.wav"
echo ""
echo "To activate the studio environment:"
echo "  source /opt/hollywood/studio-env/bin/activate"
echo ""
echo "⭐ You now have your own star on the Walk of Fame! ⭐"
echo ""

# Show the walk of fame
ls -la $HOLLYWOOD_BASE/