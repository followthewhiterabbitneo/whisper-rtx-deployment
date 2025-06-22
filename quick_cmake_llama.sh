#!/bin/bash
# Quick CMake build for llama.cpp on RHEL8

echo "=== QUICK CMAKE BUILD FOR LLAMA.CPP ==="
echo "Run this on the RHEL8 server (s01vpsromuls001)"
echo

cat << 'INSTRUCTIONS'
Steps to run on RHEL8:

1. First, push this to GitHub from local:
   git add .
   git commit -m "Add CMake build script for llama.cpp"
   git push

2. Then on RHEL8 server:
   cd /moneyball/whisper-rtx-deployment
   git pull
   ./build_llama_cpp_cmake_rhel8.sh

3. If cmake fails, try:
   # Check if cmake3 is available
   which cmake3
   
   # If yes, edit the script to use cmake3:
   sed -i 's/cmake /cmake3 /g' build_llama_cpp_cmake_rhel8.sh
   
   # Run again
   ./build_llama_cpp_cmake_rhel8.sh

4. Quick test after build:
   /moneyball/llama_gpu.sh "What is 2+2?"

INSTRUCTIONS

echo
echo "Alternative: Manual CMake build"
echo "==============================="
cat << 'MANUAL'
cd /moneyball/llama.cpp
rm -rf build
mkdir build && cd build

# Try with cmake3 if cmake fails
cmake3 .. -DLLAMA_CUDA=ON -DCMAKE_BUILD_TYPE=Release

# Or without CUDA if that fails
cmake3 .. -DLLAMA_CUDA=OFF -DCMAKE_BUILD_TYPE=Release

# Build
make -j$(nproc)

# Test
./bin/main --version
MANUAL