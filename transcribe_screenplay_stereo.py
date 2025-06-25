#!/usr/bin/env python3
"""
SCREENPLAY TRANSCRIPTION - Stereo Channel Based
Transcribes left/right channels separately for turn-by-turn dialogue
Left channel = Local Party (UWM Underwriter)
Right channel = Remote Party (Broker/Client)
"""

import sys
import os
from pathlib import Path
import wave
import numpy as np
from faster_whisper import WhisperModel
from datetime import datetime
import json

# Model configuration
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"

def split_stereo_channels(wav_file):
    """Split stereo WAV into left and right channels"""
    print(f"📂 Opening stereo file: {wav_file}")
    
    with wave.open(wav_file, 'rb') as wav:
        # Check if stereo
        channels = wav.getnchannels()
        if channels != 2:
            print(f"⚠️  Warning: File has {channels} channels, expected 2 (stereo)")
            return None, None
            
        # Read audio data
        frames = wav.readframes(wav.getnframes())
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        
    # Convert to numpy array
    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        print(f"❌ Unsupported sample width: {sample_width}")
        return None, None
        
    audio_data = np.frombuffer(frames, dtype=dtype)
    
    # Reshape to separate channels
    audio_data = audio_data.reshape(-1, 2)
    left_channel = audio_data[:, 0]
    right_channel = audio_data[:, 1]
    
    print(f"✅ Split into L/R channels: {len(left_channel)} samples each")
    
    # Save temporary mono files
    temp_left = wav_file.replace('.wav', '_LEFT_TEMP.wav')
    temp_right = wav_file.replace('.wav', '_RIGHT_TEMP.wav')
    
    # Write left channel
    with wave.open(temp_left, 'wb') as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(sample_width)
        wav_out.setframerate(framerate)
        wav_out.writeframes(left_channel.tobytes())
    
    # Write right channel
    with wave.open(temp_right, 'wb') as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(sample_width)
        wav_out.setframerate(framerate)
        wav_out.writeframes(right_channel.tobytes())
    
    return temp_left, temp_right

def transcribe_channel(model, audio_file, speaker_name):
    """Transcribe a single channel"""
    print(f"\n🎙️  Transcribing {speaker_name} channel...")
    
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        language="en",
        condition_on_previous_text=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Convert generator to list and get segments with timing
    segments_list = []
    for segment in segments:
        segments_list.append({
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.strip(),
            'speaker': speaker_name
        })
    
    print(f"✅ Found {len(segments_list)} segments for {speaker_name}")
    return segments_list

def merge_screenplay(left_segments, right_segments):
    """Merge left and right segments into screenplay format"""
    # Combine all segments
    all_segments = left_segments + right_segments
    
    # Sort by start time
    all_segments.sort(key=lambda x: x['start'])
    
    # Format as screenplay
    screenplay = []
    screenplay.append("=" * 80)
    screenplay.append("CALL TRANSCRIPT - SCREENPLAY FORMAT")
    screenplay.append("=" * 80)
    screenplay.append("")
    
    current_speaker = None
    current_text = []
    
    for segment in all_segments:
        # If speaker changes, output previous speaker's text
        if current_speaker and current_speaker != segment['speaker']:
            screenplay.append(f"{current_speaker}:")
            screenplay.append(f"  {' '.join(current_text)}")
            screenplay.append("")
            current_text = []
        
        current_speaker = segment['speaker']
        current_text.append(segment['text'])
    
    # Don't forget the last speaker's text
    if current_text:
        screenplay.append(f"{current_speaker}:")
        screenplay.append(f"  {' '.join(current_text)}")
    
    return "\n".join(screenplay)

def create_detailed_format(left_segments, right_segments):
    """Create detailed format with timestamps"""
    all_segments = left_segments + right_segments
    all_segments.sort(key=lambda x: x['start'])
    
    detailed = []
    detailed.append("=" * 80)
    detailed.append("DETAILED TRANSCRIPT WITH TIMESTAMPS")
    detailed.append("=" * 80)
    detailed.append("")
    
    for segment in all_segments:
        timestamp = f"[{segment['start']:.2f} - {segment['end']:.2f}]"
        detailed.append(f"{timestamp} {segment['speaker']}:")
        detailed.append(f"  {segment['text']}")
        detailed.append("")
    
    return "\n".join(detailed)

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_screenplay_stereo.py <audio_file.wav>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    print("🎬 SCREENPLAY TRANSCRIPTION - Stereo Channel Based")
    print("=" * 50)
    print(f"📁 Input: {audio_file}")
    print(f"🎯 Left Channel: UNDERWRITER (Local Party)")
    print(f"📞 Right Channel: BROKER/CLIENT (Remote Party)")
    print("=" * 50)
    
    # Load model
    print(f"\n📦 Loading Whisper model from {MODEL_PATH}...")
    model = WhisperModel(MODEL_PATH, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✅ Model loaded successfully!")
    
    # Split channels
    left_file, right_file = split_stereo_channels(audio_file)
    if not left_file or not right_file:
        print("❌ Failed to split stereo channels")
        sys.exit(1)
    
    try:
        # Transcribe each channel
        left_segments = transcribe_channel(model, left_file, "UNDERWRITER")
        right_segments = transcribe_channel(model, right_file, "BROKER")
        
        # Create screenplay format
        screenplay = merge_screenplay(left_segments, right_segments)
        
        # Create detailed format
        detailed = create_detailed_format(left_segments, right_segments)
        
        # Save outputs
        base_name = os.path.splitext(audio_file)[0]
        
        # Save screenplay format
        screenplay_file = f"{base_name}_screenplay.txt"
        with open(screenplay_file, 'w', encoding='utf-8') as f:
            f.write(screenplay)
        print(f"\n📝 Screenplay saved to: {screenplay_file}")
        
        # Save detailed format
        detailed_file = f"{base_name}_detailed.txt"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            f.write(detailed)
        print(f"📊 Detailed transcript saved to: {detailed_file}")
        
        # Save JSON format for further processing
        json_file = f"{base_name}_segments.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'left_segments': left_segments,
                'right_segments': right_segments,
                'all_segments': left_segments + right_segments
            }, f, indent=2)
        print(f"💾 JSON segments saved to: {json_file}")
        
        # Print preview
        print("\n" + "=" * 50)
        print("PREVIEW (first 1000 chars):")
        print("=" * 50)
        print(screenplay[:1000] + "..." if len(screenplay) > 1000 else screenplay)
        
    finally:
        # Cleanup temp files
        if os.path.exists(left_file):
            os.remove(left_file)
        if os.path.exists(right_file):
            os.remove(right_file)
        print("\n🧹 Cleaned up temporary files")

if __name__ == "__main__":
    main()