#!/usr/bin/env python3
"""
Find existing llama.cpp installation and run Gemma model
"""
import os
import subprocess
from pathlib import Path

def find_llamacpp():
    """Find llama.cpp installation"""
    print("=== Finding llama.cpp Installation ===")
    
    # Common locations
    possible_paths = [
        Path.home() / "llama.cpp",
        Path("/moneyball/llama.cpp"),
        Path("/opt/llama.cpp"),
        Path.cwd() / "llama.cpp",
        Path.home() / "projects" / "llama.cpp",
        Path("/moneyball/projects/llama.cpp")
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"✓ Found llama.cpp at: {path}")
            
            # Check for executables
            main_exe = path / "main"
            server_exe = path / "server"
            
            if main_exe.exists():
                print(f"  - main executable: {main_exe}")
            if server_exe.exists():
                print(f"  - server executable: {server_exe}")
                
            return path
    
    # Search using find
    print("\nSearching filesystem...")
    result = subprocess.run(
        ["find", "/moneyball", "-name", "llama.cpp", "-type", "d", "2>/dev/null"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    )
    
    if result.stdout:
        found_paths = result.stdout.strip().split('\n')
        for path in found_paths:
            if path:
                print(f"✓ Found: {path}")
                return Path(path)
    
    return None

def run_gemma_with_llamacpp(llamacpp_path):
    """Create scripts to run Gemma"""
    print("\n=== Running Gemma with llama.cpp ===")
    
    model_path = "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf"
    
    # Create run script
    run_script = f"""#!/bin/bash
# Run Gemma model with llama.cpp

LLAMA_PATH="{llamacpp_path}"
MODEL_PATH="{model_path}"

echo "=== Running Gemma 2 9B ==="

# Test with main executable
if [ -f "$LLAMA_PATH/main" ]; then
    echo "Testing with main..."
    $LLAMA_PATH/main -m $MODEL_PATH -n 128 -p "Summarize in one sentence: The quick brown fox jumps over the lazy dog."
else
    echo "main executable not found"
fi

# Run server
if [ -f "$LLAMA_PATH/server" ]; then
    echo ""
    echo "Starting server on port 8080..."
    echo "Once started, test with:"
    echo "curl http://localhost:8080/completion -H 'Content-Type: application/json' -d '{{\\"prompt\\": \\"Hello\\", \\"n_predict\\": 50}}'"
    echo ""
    $LLAMA_PATH/server -m $MODEL_PATH -c 2048 --host 0.0.0.0 --port 8080
else
    echo "server executable not found"
fi
"""
    
    with open("run_gemma_server.sh", "w") as f:
        f.write(run_script)
    os.chmod("run_gemma_server.sh", 0o755)
    
    print("Created: run_gemma_server.sh")
    print("\nTo run Gemma:")
    print("1. ./run_gemma_server.sh")
    print("2. In another terminal: python gemma_legal_summarizer_api.py")

def create_test_script():
    """Create a simple test script"""
    test_script = """#!/usr/bin/env python3
import subprocess
import time

print("Testing Gemma model...")

# Test prompt
prompt = "Summarize this legal call: Customer Eric Rawlins called about loan modification status. Application submitted June 1st. Currently under review. 7-10 business days for decision."

# Run llama.cpp main
cmd = [
    "./llama.cpp/main",
    "-m", "/moneyball/whisper-rtx-deployment/models/gemma-2-9b-it-Q5_K_M.gguf",
    "-n", "100",
    "-p", prompt
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Output:", result.stdout)
except Exception as e:
    print(f"Error: {e}")
"""
    
    with open("test_gemma_direct.py", "w") as f:
        f.write(test_script)
    
    print("\nCreated: test_gemma_direct.py")

def main():
    llamacpp_path = find_llamacpp()
    
    if llamacpp_path:
        run_gemma_with_llamacpp(llamacpp_path)
        create_test_script()
        
        print("\n=== Next Steps ===")
        print("1. Run the server: ./run_gemma_server.sh")
        print("2. Or test directly: python test_gemma_direct.py")
    else:
        print("\n=== Building llama.cpp ===")
        print("cd /moneyball")
        print("git clone https://github.com/ggerganov/llama.cpp")
        print("cd llama.cpp")
        print("make")
        print("\nThen run this script again!")

if __name__ == "__main__":
    main()