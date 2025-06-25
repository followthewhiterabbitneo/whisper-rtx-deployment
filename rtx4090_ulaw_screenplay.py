#!/usr/bin/env python3
"""
RTX 4090 μ-law Telephony Screenplay Processor
Handles 8kHz μ-law WAV files directly
"""

import sys
import os
import subprocess
from pathlib import Path
import glob
import tempfile
from faster_whisper import WhisperModel
from datetime import datetime
import json

# RTX 4090 Settings
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

class ULawScreenplayProcessor:
    def __init__(self):
        self.model = None
        self.all_scenes = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_model(self):
        """Load Whisper model"""
        print("🚀 Loading Whisper on RTX 4090...")
        self.model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
        print("✅ Model ready!")
        
    def convert_ulaw_stereo(self, ulaw_file):
        """Convert μ-law to PCM and split stereo"""
        print(f"📞 Processing μ-law file: {Path(ulaw_file).name}")
        
        # Create temp files
        temp_pcm = tempfile.NamedTemporaryFile(suffix='_pcm.wav', delete=False).name
        temp_left = tempfile.NamedTemporaryFile(suffix='_L.wav', delete=False).name
        temp_right = tempfile.NamedTemporaryFile(suffix='_R.wav', delete=False).name
        
        try:
            # Convert μ-law to PCM
            cmd_convert = [
                'ffmpeg', '-i', ulaw_file,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # Upsample for better quality
                '-y', temp_pcm
            ]
            subprocess.run(cmd_convert, capture_output=True, check=True)
            
            # Split channels
            cmd_left = [
                'ffmpeg', '-i', temp_pcm,
                '-af', 'pan=mono|c0=c0',
                '-y', temp_left
            ]
            subprocess.run(cmd_left, capture_output=True, check=True)
            
            cmd_right = [
                'ffmpeg', '-i', temp_pcm,
                '-af', 'pan=mono|c0=c1', 
                '-y', temp_right
            ]
            subprocess.run(cmd_right, capture_output=True, check=True)
            
            # Clean up PCM file
            os.remove(temp_pcm)
            
            return temp_left, temp_right
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Conversion error: {e}")
            # Cleanup
            for f in [temp_pcm, temp_left, temp_right]:
                if os.path.exists(f):
                    os.remove(f)
            return None, None
            
    def process_scene(self, ulaw_file, scene_number):
        """Process one μ-law file into a scene"""
        # Convert and split
        left_file, right_file = self.convert_ulaw_stereo(ulaw_file)
        if not left_file:
            return None
            
        # Transcribe
        print("  📞 Transcribing UNDERWRITER...")
        uw_segs, _ = self.model.transcribe(left_file, language="en", vad_filter=True)
        uw_list = [{'speaker': 'UNDERWRITER', 'text': seg.text.strip(),
                    'start': seg.start, 'end': seg.end} for seg in uw_segs]
        
        print("  📱 Transcribing BROKER...")
        broker_segs, _ = self.model.transcribe(right_file, language="en", vad_filter=True)
        broker_list = [{'speaker': 'BROKER', 'text': seg.text.strip(),
                       'start': seg.start, 'end': seg.end} for seg in broker_segs]
        
        # Cleanup temp files
        os.remove(left_file)
        os.remove(right_file)
        
        # Merge and sort
        all_segments = uw_list + broker_list
        all_segments.sort(key=lambda x: x['start'])
        
        # Create scene
        scene = {
            'scene_number': scene_number,
            'file': Path(ulaw_file).name,
            'segments': all_segments,
            'uw_count': len(uw_list),
            'broker_count': len(broker_list)
        }
        
        # Save individual scene
        self.save_scene(scene)
        
        return scene
        
    def save_scene(self, scene):
        """Save individual scene screenplay"""
        output_dir = Path("screenplay_scenes")
        output_dir.mkdir(exist_ok=True)
        
        screenplay = []
        screenplay.append(f"SCENE {scene['scene_number']}: {scene['file']}")
        screenplay.append("="*60)
        screenplay.append(f"μ-law Telephony Recording (8kHz)")
        screenplay.append(f"Underwriter: {scene['uw_count']} segments")
        screenplay.append(f"Broker: {scene['broker_count']} segments")
        screenplay.append("="*60)
        screenplay.append("")
        
        # Group by speaker
        current_speaker = None
        current_text = []
        
        for seg in scene['segments']:
            if seg['speaker'] != current_speaker:
                if current_speaker and current_text:
                    screenplay.append(f"\n{current_speaker}:")
                    screenplay.append(' '.join(current_text))
                current_speaker = seg['speaker']
                current_text = [seg['text']]
            else:
                current_text.append(seg['text'])
                
        # Last speaker
        if current_text:
            screenplay.append(f"\n{current_speaker}:")
            screenplay.append(' '.join(current_text))
            
        # Save
        scene_file = output_dir / f"SCENE_{scene['scene_number']:02d}_{Path(scene['file']).stem}.txt"
        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(screenplay))
            
        print(f"  ✅ Scene saved: {scene_file}")
        
    def create_complete_screenplay(self):
        """Combine all scenes"""
        if not self.all_scenes:
            return None
            
        output_dir = Path("screenplay_output")
        output_dir.mkdir(exist_ok=True)
        
        screenplay = []
        screenplay.append("🎬 COMPLETE μ-LAW TELEPHONY SCREENPLAY 🎬")
        screenplay.append("="*70)
        screenplay.append(f"Format: 8kHz μ-law telephony recordings")
        screenplay.append(f"Total Scenes: {len(self.all_scenes)}")
        screenplay.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        screenplay.append("="*70)
        
        for scene in self.all_scenes:
            screenplay.append(f"\n\n{'='*70}")
            screenplay.append(f"SCENE {scene['scene_number']}: {scene['file']}")
            screenplay.append("="*70)
            screenplay.append("")
            
            current_speaker = None
            current_text = []
            
            for seg in scene['segments']:
                if seg['speaker'] != current_speaker:
                    if current_speaker and current_text:
                        screenplay.append(f"\n{current_speaker}:")
                        screenplay.append(' '.join(current_text))
                    current_speaker = seg['speaker']
                    current_text = [seg['text']]
                else:
                    current_text.append(seg['text'])
                    
            if current_text:
                screenplay.append(f"\n{current_speaker}:")
                screenplay.append(' '.join(current_text))
                
        # Save
        output_file = output_dir / f"COMPLETE_ULAW_SCREENPLAY_{self.timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(screenplay))
            
        return output_file
        
    def process_batch(self, pattern):
        """Process all μ-law files"""
        files = glob.glob(pattern)
        
        if not files:
            print(f"No files found: {pattern}")
            return
            
        print(f"\n🎬 μ-LAW BATCH PROCESSOR")
        print(f"Found {len(files)} files")
        print("="*50)
        
        for i, f in enumerate(files, 1):
            print(f"\n📽️  SCENE {i}/{len(files)}")
            scene = self.process_scene(f, i)
            if scene:
                self.all_scenes.append(scene)
                
        # Create complete screenplay
        if self.all_scenes:
            output = self.create_complete_screenplay()
            print("\n" + "="*70)
            print("✅ BATCH PROCESSING COMPLETE!")
            print(f"Processed: {len(self.all_scenes)} scenes")
            print(f"Individual scenes: screenplay_scenes/")
            print(f"Complete screenplay: {output}")

def main():
    if len(sys.argv) < 2:
        print("RTX 4090 μ-law Screenplay Processor")
        print("For 8kHz μ-law telephony recordings")
        print("="*40)
        print("Usage:")
        print("  python rtx4090_ulaw_screenplay.py 'pattern'")
        print("\nExample:")
        print("  python rtx4090_ulaw_screenplay.py wav_batch_download\\*.wav")
        sys.exit(1)
        
    # Check for ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("❌ FFmpeg not found!")
        print("Install with: choco install ffmpeg")
        sys.exit(1)
        
    pattern = sys.argv[1]
    
    processor = ULawScreenplayProcessor()
    processor.load_model()
    processor.process_batch(pattern)

if __name__ == "__main__":
    main()