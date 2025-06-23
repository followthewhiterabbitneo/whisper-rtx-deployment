#!/usr/bin/env python3
"""
Quick script to process Eric Rawlins recordings
"""

import subprocess
import sys

print("=" * 80)
print("PROCESSING ERIC RAWLINS RECORDINGS")
print("=" * 80)

# Run the batch processor for Eric Rawlins
cmd = [sys.executable, "scream_batch_processor.py", "--user", "Eric", "Rawlins", "1"]

print("\nRunning: " + " ".join(cmd))
print("-" * 80)

subprocess.run(cmd)