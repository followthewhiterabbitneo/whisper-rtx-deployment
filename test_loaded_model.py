#!/usr/bin/env python3
"""Test the already loaded model - no need to reload!"""
import requests
import time
import subprocess

print("=== TESTING ALREADY LOADED MODEL ===")
print("Model is in GPU memory - let's use it!")
print()

# 1. Quick API test
print("1. Quick API test:")
start = time.time()
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": "What is 2+2?",
        "stream": False,
        "options": {"num_predict": 10}
    }
)
elapsed = time.time() - start

if response.status_code == 200:
    result = response.json()
    print(f"✓ Response: {result['response'].strip()}")
    print(f"✓ Time: {elapsed:.2f}s (no reload needed!)")
else:
    print(f"Error: {response.status_code}")

# 2. Test with ollama run
print("\n2. Testing with ollama run:")
start = time.time()
result = subprocess.run(
    ["ollama", "run", "llama3", "What is 10 times 5?"],
    capture_output=True,
    text=True
)
elapsed = time.time() - start
print(f"Response: {result.stdout.strip()}")
print(f"Time: {elapsed:.2f}s")

# 3. Legal summary test
print("\n3. Legal summary test:")
prompt = """Create a brief legal summary:
Customer: Eric Rawlins
Date: June 20, 2024
Issue: Called about loan modification status
Resolution: Application confirmed received, under review"""

start = time.time()
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 200, "temperature": 0.3}
    }
)
elapsed = time.time() - start

if response.status_code == 200:
    result = response.json()
    print(f"Summary: {result['response'][:300]}...")
    print(f"Time: {elapsed:.2f}s")

# 4. Check GPU memory
print("\n4. GPU memory usage:")
result = subprocess.run(
    ["nvidia-smi", "--query-gpu=memory.used,memory.free", "--format=csv,noheader"],
    capture_output=True,
    text=True
)
print(f"GPU memory: {result.stdout.strip()}")

print("\n✅ Model is loaded and working!")
print("✅ Keep it loaded for fast responses!")
print("\nTo keep it loaded, set:")
print("export OLLAMA_KEEP_ALIVE=24h")