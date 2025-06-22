#!/usr/bin/env python3
"""
Simple summary using whatever Ollama is available
"""
import subprocess
import os

# Try both ports
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def try_ollama(port=None):
    """Try to use Ollama on specified port"""
    env = os.environ.copy()
    if port:
        env['OLLAMA_HOST'] = f'localhost:{port}'
        print(f"Trying port {port}...")
    else:
        print("Trying default port...")
    
    # Simple test
    result = subprocess.run(
        ["ollama", "run", "gemma2-legal", "Hello"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env,
        timeout=10
    )
    
    if result.returncode == 0:
        print(f"✓ Ollama working on port {port or 11434}")
        return True, port or 11434, env
    else:
        print(f"✗ Failed on port {port or 11434}")
        return False, None, None

def main():
    print("=== Finding Working Ollama ===")
    
    # Try default port first
    success, port, env = try_ollama()
    
    # Try alternate port
    if not success:
        success, port, env = try_ollama(11435)
    
    if not success:
        print("\nNo working Ollama found!")
        print("Run: ./fix_ollama_port.sh")
        return
    
    # Create summary
    print(f"\n=== Creating Summary (Port {port}) ===")
    
    # Simple test transcript
    transcript = """Eric Rawlins loan modification call:
    - Application submitted June 1st
    - Under review by underwriting
    - Decision expected in 7-10 days
    - Forbearance options offered
    - Reference: SR-2025-0620-3847"""
    
    prompt = f"Create a brief legal summary:\n{transcript}"
    
    print("Generating summary...")
    result = subprocess.run(
        ["ollama", "run", "gemma2-legal", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env if env else None,
        timeout=60
    )
    
    if result.returncode == 0:
        print("\n=== SUMMARY ===")
        print(result.stdout)
        
        # Save
        with open("/moneyball/whisper-rtx-deployment/quick_summary.txt", "w") as f:
            f.write(f"Legal Summary (Gemma 2 9B)\n")
            f.write(f"Port: {port}\n")
            f.write("="*50 + "\n")
            f.write(result.stdout)
        print("\nSaved to: quick_summary.txt")
    else:
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    main()