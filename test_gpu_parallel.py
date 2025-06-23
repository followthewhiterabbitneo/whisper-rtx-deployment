#!/usr/bin/env python3
"""
Test if we can run multiple Whisper instances in parallel on RTX 4090
"""

import time
import threading
from faster_whisper import WhisperModel
import subprocess
import torch

def check_gpu_memory():
    """Check GPU memory usage"""
    try:
        # Check with nvidia-smi
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            used, total = map(int, result.stdout.strip().split(', '))
            return used, total
    except:
        pass
    return 0, 0

print("RTX 4090 GPU Memory Test")
print("=" * 60)

# Check initial GPU memory
used, total = check_gpu_memory()
print(f"Initial GPU Memory: {used}MB / {total}MB ({used/total*100:.1f}% used)")

# Load one model and check memory
print("\nLoading first Whisper model...")
model1 = WhisperModel(
    "models/faster-whisper-large-v3-turbo-ct2",
    device="cuda",
    compute_type="int8_float16"
)

used, total = check_gpu_memory()
print(f"After 1 model: {used}MB / {total}MB ({used/total*100:.1f}% used)")
model_size = used

# Try loading second model
print("\nTrying to load second model...")
try:
    model2 = WhisperModel(
        "models/faster-whisper-large-v3-turbo-ct2",
        device="cuda",
        compute_type="int8_float16",
        device_index=0  # Same GPU
    )
    
    used2, total = check_gpu_memory()
    print(f"After 2 models: {used2}MB / {total}MB ({used2/total*100:.1f}% used)")
    
    # Models might share weights, so let's test actual inference
    print("\nTesting parallel inference...")
    
    def transcribe_test(model, name):
        """Test transcription"""
        start = time.time()
        # Use any test audio file
        segments, info = model.transcribe("test_audio.wav", beam_size=1)
        text = " ".join([s.text for s in segments])
        elapsed = time.time() - start
        print(f"{name} completed in {elapsed:.1f}s")
        return elapsed
    
    # Test sequential first
    print("\nSequential test:")
    t1 = transcribe_test(model1, "Model 1")
    t2 = transcribe_test(model2, "Model 2")
    sequential_time = t1 + t2
    
    # Test parallel
    print("\nParallel test:")
    results = []
    threads = []
    
    start = time.time()
    for i, model in enumerate([model1, model2]):
        t = threading.Thread(target=lambda m=model, n=f"Model {i+1}": results.append(transcribe_test(m, n)))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    parallel_time = time.time() - start
    
    print(f"\nResults:")
    print(f"Sequential time: {sequential_time:.1f}s")
    print(f"Parallel time: {parallel_time:.1f}s")
    print(f"Speedup: {sequential_time/parallel_time:.2f}x")
    
except Exception as e:
    print(f"Failed to load second model: {e}")
    print("\nWhisper models might not run in true parallel on same GPU")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)

if total > 0:
    free_memory = total - used
    print(f"Free GPU memory: {free_memory}MB")
    
    # Whisper large-v3-turbo uses about 1.5-2GB per instance
    whisper_size = 2000  # MB estimate
    max_instances = free_memory // whisper_size
    
    print(f"Whisper turbo model size: ~{whisper_size}MB")
    print(f"Theoretical max instances: {max_instances}")
    
    if max_instances >= 4:
        print("\n✓ You have enough VRAM for 4 parallel instances")
    else:
        print(f"\n⚠️  You might only fit {max_instances} parallel instances")

print("\nNOTE: Even with enough VRAM, Whisper might not parallelize well")
print("due to CUDA kernel contention. Consider these alternatives:")
print("1. Process sequentially (still fast with turbo)")
print("2. Use batch processing if faster-whisper supports it")
print("3. Process in chunks with model reuse")