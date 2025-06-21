#!/usr/bin/env python3
"""
Test Whisper on RTX 4090 with turbo model
Benchmark speed and quality
"""

import os
import time
import torch
from faster_whisper import WhisperModel

def test_whisper_performance(audio_file="test.wav"):
    """Test Whisper model performance on RTX 4090"""
    
    print("=== Whisper RTX 4090 Performance Test ===\n")
    
    # Check GPU
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("❌ No GPU detected!")
        return
    
    # Test different model configurations
    configs = [
        # Model size, compute type, description
        ("base", "int8", "Fastest - good for real-time"),
        ("large-v3", "int8", "Turbo mode - balanced"),
        ("large-v3", "float16", "Highest quality - slower"),
    ]
    
    results = []
    
    for model_size, compute_type, description in configs:
        print(f"\n📊 Testing: {model_size} ({compute_type}) - {description}")
        
        try:
            # Load model
            start = time.time()
            model = WhisperModel(
                model_size, 
                device="cuda", 
                compute_type=compute_type,
                num_workers=4,  # Use multiple workers
                download_root=None  # Use default cache
            )
            load_time = time.time() - start
            print(f"   Model load time: {load_time:.2f}s")
            
            # Create a simple test if no audio file exists
            if not os.path.exists(audio_file):
                print(f"   ⚠️  No audio file found at {audio_file}")
                print("   Create test audio: ffmpeg -f lavfi -i sine=frequency=1000:duration=5 test.wav")
                continue
            
            # Transcribe
            start = time.time()
            segments, info = model.transcribe(
                audio_file,
                beam_size=5,
                best_of=5,
                temperature=0,  # Deterministic
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Process results
            text = " ".join([segment.text for segment in segments])
            transcribe_time = time.time() - start
            
            # Calculate real-time factor
            audio_duration = info.duration
            rtf = transcribe_time / audio_duration if audio_duration > 0 else 0
            
            results.append({
                "model": f"{model_size} ({compute_type})",
                "load_time": load_time,
                "transcribe_time": transcribe_time,
                "audio_duration": audio_duration,
                "rtf": rtf,
                "text_preview": text[:100] + "..." if len(text) > 100 else text
            })
            
            print(f"   Transcription time: {transcribe_time:.2f}s")
            print(f"   Audio duration: {audio_duration:.2f}s")
            print(f"   Real-time factor: {rtf:.2f}x")
            print(f"   Text: {text[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n=== Performance Summary ===")
    print(f"{'Model':<25} {'Load(s)':<10} {'Trans(s)':<10} {'RTF':<10}")
    print("-" * 55)
    for r in results:
        print(f"{r['model']:<25} {r['load_time']:<10.2f} {r['transcribe_time']:<10.2f} {r['rtf']:<10.2f}x")
    
    # Recommendations
    print("\n💡 Recommendations for RTX 4090:")
    print("- For real-time: Use 'base' with int8")
    print("- For quality: Use 'large-v3' with float16")
    print("- For balanced: Use 'large-v3' with int8 (turbo mode)")
    
    # Save results
    import json
    with open("whisper_rtx_benchmark.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📁 Results saved to: whisper_rtx_benchmark.json")

if __name__ == "__main__":
    import sys
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test.wav"
    test_whisper_performance(audio_file)