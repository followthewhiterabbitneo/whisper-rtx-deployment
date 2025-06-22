#!/bin/bash
# Check what's using GPU memory

echo "=== GPU Memory Analysis ==="
echo

# 1. Current GPU status
echo "1. Current GPU Memory Usage:"
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader,nounits
echo

# 2. Processes using GPU
echo "2. Processes using GPU memory:"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
echo

# 3. Detailed process view
echo "3. Detailed GPU processes:"
nvidia-smi
echo

# 4. Check for other users
echo "4. Checking for other users' processes:"
ps aux | grep -E "cuda|nvidia|gpu" | grep -v grep | head -10

# 5. Memory breakdown
echo
echo "5. Memory Summary:"
echo "   Total VRAM: 8192 MiB (8 GB)"
echo "   Base usage: ~5305 MiB (other processes/overhead)"
echo "   Model size: ~1840 MiB (7145-5305)"
echo "   Free after model: ~1047 MiB"
echo
echo "The 5.3GB base usage might be:"
echo "- vGPU overhead/reservation"
echo "- Display manager/X server"
echo "- Other users' processes"
echo "- CUDA context overhead"