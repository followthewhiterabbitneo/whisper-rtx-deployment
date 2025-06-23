#!/usr/bin/env python3
"""
Process the Eric Rawlins recording directly - we know it exists!
orkUid: 20250620_145645_LOLW
"""

import subprocess
import sys

print("=" * 80)
print("PROCESSING ERIC RAWLINS RECORDING DIRECTLY")
print("=" * 80)

# We know this recording exists from your data
orkuid = "20250620_145645_LOLW"

print(f"\nProcessing known recording: {orkuid}")
print("File: 2025/06/20/14/20250620_145645_LOLW.wav")
print("Duration: 197 seconds")
print("Parties: +15550086152 <-> 12817272500")

# Run the hybrid pipeline directly
cmd = [sys.executable, "scream_hybrid_pipeline.py", orkuid, "temp_audio.wav"]

print(f"\nNote: This will download the audio file via SCP")
print("The scream_hybrid_pipeline.py will handle the download\n")

# Actually, let's use the simpler process_any_recording.py script
cmd = [sys.executable, "process_any_recording.py", orkuid]

print("Running: " + " ".join(cmd))
print("-" * 80)

subprocess.run(cmd)