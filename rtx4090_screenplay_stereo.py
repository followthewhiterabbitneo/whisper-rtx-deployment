#!/usr/bin/env python3
"""
RTX 4090 SCREENPLAY TRANSCRIPTION - Windows PowerShell Ready
Optimized for 24GB VRAM - Stereo Channel Separation
Left Channel = UNDERWRITER
Right Channel = BROKER/REMOTE PARTY
"""

import sys
import os
from pathlib import Path
import wave
import numpy as np
from faster_whisper import WhisperModel
from datetime import datetime
import json

# RTX 4090 Optimized Settings
MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"  # Use full float16 with 24GB VRAM
BATCH_SIZE = 16  # Can handle larger batches with 24GB

def print_rtx_banner():
    """Show RTX 4090 startup banner"""
    print("="*70)
    print("🚀 RTX 4090 SCREENPLAY TRANSCRIPTION 🚀")
    print("24GB VRAM | CUDA Optimized | Stereo Channel Separation")
    print("="*70)
    print()

def split_stereo_to_mono(wav_file):
    """Split stereo WAV into left (Underwriter) and right (Broker) channels"""
    print(f"📂 Opening stereo file: {wav_file}")
    
    try:
        with wave.open(wav_file, 'rb') as wav:
            channels = wav.getnchannels()
            if channels != 2:
                print(f"⚠️  File has {channels} channels - expected stereo (2)")
                if channels == 1:
                    print("   This is MONO audio - no channel separation possible")
                    return None, None
                
            frames = wav.readframes(wav.getnframes())
            sample_width = wav.getsampwidth()
            framerate = wav.getframerate()
            duration = wav.getnframes() / framerate
            
        print(f"✅ Stereo file confirmed: {duration:.1f} seconds")
        
        # Convert to numpy
        if sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            print(f"❌ Unsupported sample width: {sample_width}")
            return None, None
            
        audio_data = np.frombuffer(frames, dtype=dtype)
        audio_data = audio_data.reshape(-1, 2)
        
        # Extract channels
        left_channel = audio_data[:, 0]
        right_channel = audio_data[:, 1]
        
        # Create temp directory if needed
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        
        # Save as mono files
        base_name = Path(wav_file).stem
        left_file = str(temp_dir / f"{base_name}_UNDERWRITER.wav")
        right_file = str(temp_dir / f"{base_name}_BROKER.wav")
        
        # Write left channel (Underwriter)
        with wave.open(left_file, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(framerate)
            wav_out.writeframes(left_channel.tobytes())
        
        # Write right channel (Broker)
        with wave.open(right_file, 'wb') as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(sample_width)
            wav_out.setframerate(framerate)
            wav_out.writeframes(right_channel.tobytes())
        
        print(f"✅ Split complete:")
        print(f"   📞 Left → {left_file} (UNDERWRITER)")
        print(f"   📱 Right → {right_file} (BROKER)")
        
        return left_file, right_file
        
    except Exception as e:
        print(f"❌ Error splitting audio: {e}")
        return None, None

def transcribe_with_rtx4090(model, audio_file, speaker_role):
    """Transcribe using RTX 4090 optimized settings"""
    print(f"\n🎙️  Transcribing {speaker_role} channel...")
    print(f"   Using RTX 4090 with 24GB VRAM")
    
    # RTX 4090 can handle aggressive settings
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        best_of=5,  # Can afford better quality with 24GB
        patience=2.0,
        length_penalty=1.0,
        temperature=0.0,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
        no_speech_threshold=0.6,
        condition_on_previous_text=True,
        initial_prompt=f"This is a {speaker_role} speaking in a loan underwriting call.",
        vad_filter=True,
        vad_parameters=dict(
            threshold=0.5,
            min_speech_duration_ms=250,
            max_speech_duration_s=float('inf'),
            min_silence_duration_ms=500,
            window_size_samples=1024,
            speech_pad_ms=400
        )
    )
    
    # Collect segments
    segments_list = []
    word_count = 0
    
    for segment in segments:
        segments_list.append({
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.strip(),
            'speaker': speaker_role,
            'avg_logprob': segment.avg_logprob,
            'no_speech_prob': segment.no_speech_prob
        })
        word_count += len(segment.text.split())
    
    print(f"✅ Transcribed {len(segments_list)} segments, {word_count} words")
    return segments_list, info

def create_screenplay_format(underwriter_segments, broker_segments, audio_file):
    """Create professional screenplay format"""
    # Merge and sort by time
    all_segments = underwriter_segments + broker_segments
    all_segments.sort(key=lambda x: x['start'])
    
    # Create output directory
    output_dir = Path("screenplay_output")
    output_dir.mkdir(exist_ok=True)
    
    base_name = Path(audio_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Professional screenplay format
    screenplay = []
    screenplay.append("LOAN UNDERWRITING CALL TRANSCRIPT")
    screenplay.append("="*50)
    screenplay.append(f"File: {base_name}")
    screenplay.append(f"Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    screenplay.append(f"Parties: UNDERWRITER (Left Channel) | BROKER (Right Channel)")
    screenplay.append("="*50)
    screenplay.append("")
    
    # Group consecutive segments by speaker
    current_speaker = None
    current_text = []
    current_start = None
    
    for segment in all_segments:
        if segment['speaker'] != current_speaker:
            # Output previous speaker's text
            if current_speaker and current_text:
                screenplay.append(f"\n{current_speaker} [{format_time(current_start)}]:")
                screenplay.append(f"{' '.join(current_text)}")
            
            # Start new speaker
            current_speaker = segment['speaker']
            current_text = [segment['text']]
            current_start = segment['start']
        else:
            # Continue with same speaker
            current_text.append(segment['text'])
    
    # Don't forget last speaker
    if current_text:
        screenplay.append(f"\n{current_speaker} [{format_time(current_start)}]:")
        screenplay.append(f"{' '.join(current_text)}")
    
    # Save screenplay
    screenplay_file = output_dir / f"{base_name}_screenplay_{timestamp}.txt"
    with open(screenplay_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(screenplay))
    
    print(f"\n📝 Screenplay saved: {screenplay_file}")
    
    # Also create detailed version with all timestamps
    detailed = []
    detailed.append("DETAILED TRANSCRIPT WITH TIMESTAMPS")
    detailed.append("="*50)
    detailed.append("")
    
    for seg in all_segments:
        detailed.append(f"[{format_time(seg['start'])} - {format_time(seg['end'])}] {seg['speaker']}:")
        detailed.append(f"  {seg['text']}")
        detailed.append(f"  (confidence: {1 - seg['no_speech_prob']:.2%})")
        detailed.append("")
    
    detailed_file = output_dir / f"{base_name}_detailed_{timestamp}.txt"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(detailed))
    
    # Save JSON for further processing
    json_data = {
        'file': base_name,
        'timestamp': timestamp,
        'duration': all_segments[-1]['end'] if all_segments else 0,
        'underwriter_segments': len(underwriter_segments),
        'broker_segments': len(broker_segments),
        'total_segments': len(all_segments),
        'segments': all_segments
    }
    
    json_file = output_dir / f"{base_name}_data_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    return screenplay_file, detailed_file, json_file

def format_time(seconds):
    """Format seconds to MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def cleanup_temp_files(left_file, right_file):
    """Remove temporary audio files"""
    try:
        if left_file and os.path.exists(left_file):
            os.remove(left_file)
        if right_file and os.path.exists(right_file):
            os.remove(right_file)
        print("🧹 Cleaned up temporary files")
    except:
        pass

def main():
    print_rtx_banner()
    
    if len(sys.argv) < 2:
        print("Usage: python rtx4090_screenplay_stereo.py <stereo_audio.wav>")
        print("\nExample:")
        print("  python rtx4090_screenplay_stereo.py loan_call_12345.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    # Load model with RTX 4090 optimizations
    print(f"\n🚀 Loading Whisper model for RTX 4090...")
    print(f"   Model: {MODEL_PATH}")
    print(f"   Device: CUDA (RTX 4090 24GB)")
    
    model = WhisperModel(
        MODEL_PATH, 
        device=DEVICE, 
        compute_type=COMPUTE_TYPE,
        num_workers=4,  # RTX 4090 can handle multiple workers
        download_root="models"
    )
    print("✅ Model loaded and ready!")
    
    # Split stereo channels
    left_file, right_file = split_stereo_to_mono(audio_file)
    
    if not left_file or not right_file:
        print("❌ Failed to split stereo audio")
        sys.exit(1)
    
    try:
        # Transcribe both channels
        underwriter_segments, uw_info = transcribe_with_rtx4090(model, left_file, "UNDERWRITER")
        broker_segments, broker_info = transcribe_with_rtx4090(model, right_file, "BROKER")
        
        # Create screenplay outputs
        screenplay, detailed, json_file = create_screenplay_format(
            underwriter_segments, 
            broker_segments, 
            audio_file
        )
        
        # Summary
        print("\n" + "="*50)
        print("✅ TRANSCRIPTION COMPLETE!")
        print("="*50)
        print(f"Total segments: {len(underwriter_segments) + len(broker_segments)}")
        print(f"Underwriter: {len(underwriter_segments)} segments")
        print(f"Broker: {len(broker_segments)} segments")
        print(f"\nOutputs saved:")
        print(f"  📝 {screenplay}")
        print(f"  📊 {detailed}")
        print(f"  💾 {json_file}")
        
    finally:
        # Always cleanup
        cleanup_temp_files(left_file, right_file)

if __name__ == "__main__":
    main()