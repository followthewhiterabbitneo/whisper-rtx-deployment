#!/usr/bin/env python3
"""
RTX 4090 BATCH SCREENPLAY PROCESSOR
Process multiple stereo files → Individual scenes + Complete screenplay
Left = UNDERWRITER, Right = BROKER
"""

import sys
import os
from pathlib import Path
import wave
import numpy as np
from faster_whisper import WhisperModel
from datetime import datetime
import json
import glob

# RTX 4090 Settings
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"  # 24GB VRAM can handle it

class BatchScreenplayProcessor:
    def __init__(self):
        self.model = None
        self.all_scenes = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_model(self):
        """Load Whisper model once for all files"""
        print("🚀 Loading Whisper model on RTX 4090...")
        self.model = WhisperModel(
            MODEL_PATH,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            num_workers=4
        )
        print("✅ Model loaded! Ready for batch processing")
        
    def split_stereo(self, wav_file):
        """Split stereo into L/R mono files"""
        try:
            with wave.open(wav_file, 'rb') as wav:
                if wav.getnchannels() != 2:
                    print(f"⚠️  Skipping {wav_file} - not stereo")
                    return None, None
                    
                frames = wav.readframes(wav.getnframes())
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                
            # Convert to numpy
            dtype = np.int16 if sample_width == 2 else np.int32
            audio_data = np.frombuffer(frames, dtype=dtype)
            audio_data = audio_data.reshape(-1, 2)
            
            # Split channels
            left = audio_data[:, 0]
            right = audio_data[:, 1]
            
            # Save temp files
            temp_dir = Path("temp_batch")
            temp_dir.mkdir(exist_ok=True)
            
            base = Path(wav_file).stem
            left_file = str(temp_dir / f"{base}_L.wav")
            right_file = str(temp_dir / f"{base}_R.wav")
            
            # Write mono files
            for data, filename in [(left, left_file), (right, right_file)]:
                with wave.open(filename, 'wb') as out:
                    out.setnchannels(1)
                    out.setsampwidth(sample_width)
                    out.setframerate(framerate)
                    out.writeframes(data.tobytes())
                    
            return left_file, right_file
            
        except Exception as e:
            print(f"❌ Error with {wav_file}: {e}")
            return None, None
            
    def transcribe_channel(self, audio_file, speaker):
        """Transcribe single channel"""
        segments, info = self.model.transcribe(
            audio_file,
            beam_size=5,
            language="en",
            condition_on_previous_text=True,
            initial_prompt=f"This is a {speaker} in a loan underwriting call.",
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )
        
        return [{
            'start': seg.start,
            'end': seg.end,
            'text': seg.text.strip(),
            'speaker': speaker
        } for seg in segments]
        
    def process_single_file(self, wav_file, scene_number):
        """Process one stereo file into a scene"""
        print(f"\n🎬 SCENE {scene_number}: {Path(wav_file).name}")
        print("="*50)
        
        # Split stereo
        left_file, right_file = self.split_stereo(wav_file)
        if not left_file:
            return None
            
        # Transcribe both channels
        print("📞 Transcribing UNDERWRITER (left channel)...")
        uw_segments = self.transcribe_channel(left_file, "UNDERWRITER")
        
        print("📱 Transcribing BROKER (right channel)...")
        broker_segments = self.transcribe_channel(right_file, "BROKER")
        
        # Cleanup temp files
        try:
            os.remove(left_file)
            os.remove(right_file)
        except:
            pass
            
        # Merge and sort
        all_segments = uw_segments + broker_segments
        all_segments.sort(key=lambda x: x['start'])
        
        # Create scene data
        scene = {
            'scene_number': scene_number,
            'file': Path(wav_file).name,
            'segments': all_segments,
            'duration': all_segments[-1]['end'] if all_segments else 0,
            'uw_count': len(uw_segments),
            'broker_count': len(broker_segments)
        }
        
        # Save individual scene
        self.save_individual_scene(scene, wav_file)
        
        return scene
        
    def save_individual_scene(self, scene, original_file):
        """Save individual scene screenplay"""
        output_dir = Path("screenplay_scenes")
        output_dir.mkdir(exist_ok=True)
        
        base_name = Path(original_file).stem
        
        # Format screenplay
        screenplay = []
        screenplay.append(f"SCENE {scene['scene_number']}: {base_name}")
        screenplay.append("="*50)
        screenplay.append(f"Duration: {self.format_duration(scene['duration'])}")
        screenplay.append(f"File: {scene['file']}")
        screenplay.append("="*50)
        screenplay.append("")
        
        # Group by speaker
        current_speaker = None
        current_text = []
        
        for seg in scene['segments']:
            if seg['speaker'] != current_speaker:
                if current_speaker and current_text:
                    screenplay.append(f"\n{current_speaker}:")
                    screenplay.append(f"{' '.join(current_text)}")
                    
                current_speaker = seg['speaker']
                current_text = [seg['text']]
            else:
                current_text.append(seg['text'])
                
        # Last speaker
        if current_text:
            screenplay.append(f"\n{current_speaker}:")
            screenplay.append(f"{' '.join(current_text)}")
            
        # Save scene file
        scene_file = output_dir / f"SCENE_{scene['scene_number']:02d}_{base_name}.txt"
        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(screenplay))
            
        print(f"✅ Scene saved: {scene_file}")
        
    def create_complete_screenplay(self):
        """Combine all scenes into complete screenplay"""
        output_dir = Path("screenplay_output")
        output_dir.mkdir(exist_ok=True)
        
        screenplay = []
        screenplay.append("🎬 COMPLETE SCREENPLAY - ALL SCENES 🎬")
        screenplay.append("="*70)
        screenplay.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        screenplay.append(f"Total Scenes: {len(self.all_scenes)}")
        screenplay.append(f"Total Duration: {self.format_duration(sum(s['duration'] for s in self.all_scenes))}")
        screenplay.append("="*70)
        screenplay.append("\n")
        
        # Add each scene
        for scene in self.all_scenes:
            screenplay.append(f"\n{'='*70}")
            screenplay.append(f"SCENE {scene['scene_number']}: {scene['file']}")
            screenplay.append(f"Duration: {self.format_duration(scene['duration'])}")
            screenplay.append("="*70)
            screenplay.append("")
            
            # Group by speaker
            current_speaker = None
            current_text = []
            
            for seg in scene['segments']:
                if seg['speaker'] != current_speaker:
                    if current_speaker and current_text:
                        screenplay.append(f"\n{current_speaker}:")
                        screenplay.append(f"{' '.join(current_text)}")
                        
                    current_speaker = seg['speaker']
                    current_text = [seg['text']]
                else:
                    current_text.append(seg['text'])
                    
            # Last speaker
            if current_text:
                screenplay.append(f"\n{current_speaker}:")
                screenplay.append(f"{' '.join(current_text)}")
                
            screenplay.append("\n")
        
        # Save complete screenplay
        complete_file = output_dir / f"COMPLETE_SCREENPLAY_{self.timestamp}.txt"
        with open(complete_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(screenplay))
            
        # Also save master JSON
        json_file = output_dir / f"COMPLETE_DATA_{self.timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': self.timestamp,
                'total_scenes': len(self.all_scenes),
                'total_duration': sum(s['duration'] for s in self.all_scenes),
                'scenes': self.all_scenes
            }, f, indent=2)
            
        return complete_file, json_file
        
    def format_duration(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        else:
            return f"{minutes}m {secs}s"
            
    def process_batch(self, file_pattern):
        """Process all files matching pattern"""
        # Find all matching files
        files = glob.glob(file_pattern)
        if not files:
            print(f"❌ No files found matching: {file_pattern}")
            return
            
        print(f"\n🎬 BATCH SCREENPLAY PROCESSOR")
        print(f"Found {len(files)} files to process")
        print("="*50)
        
        # Process each file
        for i, wav_file in enumerate(files, 1):
            scene = self.process_single_file(wav_file, i)
            if scene:
                self.all_scenes.append(scene)
                
        # Create complete screenplay
        if self.all_scenes:
            print("\n📝 Creating complete screenplay...")
            complete_file, json_file = self.create_complete_screenplay()
            
            print("\n" + "="*70)
            print("✅ BATCH PROCESSING COMPLETE!")
            print("="*70)
            print(f"Processed: {len(self.all_scenes)} scenes")
            print(f"Individual scenes: screenplay_scenes/")
            print(f"Complete screenplay: {complete_file}")
            print(f"Complete data: {json_file}")
        else:
            print("❌ No scenes were successfully processed")
            
        # Cleanup
        try:
            import shutil
            shutil.rmtree("temp_batch", ignore_errors=True)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("RTX 4090 BATCH SCREENPLAY PROCESSOR")
        print("="*40)
        print("Usage:")
        print("  python rtx4090_batch_screenplay.py 'pattern'")
        print("\nExamples:")
        print("  python rtx4090_batch_screenplay.py '*.wav'")
        print("  python rtx4090_batch_screenplay.py 'calls/*.wav'")
        print("  python rtx4090_batch_screenplay.py 'loan_*.wav'")
        sys.exit(1)
        
    file_pattern = sys.argv[1]
    
    # Create processor
    processor = BatchScreenplayProcessor()
    
    # Load model once
    processor.load_model()
    
    # Process all files
    processor.process_batch(file_pattern)

if __name__ == "__main__":
    main()