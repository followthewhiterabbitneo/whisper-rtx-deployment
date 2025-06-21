#!/usr/bin/env python3
"""
Check audio dependencies and ffmpeg installation on Windows
"""

import os
import sys
import subprocess
import shutil
import json
from datetime import datetime

def run_command(cmd):
    """Run a command and return output"""
    try:
        # For Windows, use shell=True for commands like 'where'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        return f"Exception: {str(e)}"

def check_ffmpeg():
    """Check ffmpeg installation"""
    ffmpeg_info = {}
    
    # Check if ffmpeg is in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        ffmpeg_info['installed'] = True
        ffmpeg_info['path'] = ffmpeg_path
        
        # Get version
        version = run_command('ffmpeg -version')
        if version:
            ffmpeg_info['version'] = version.split('\n')[0]
    else:
        # Check common Windows locations
        common_paths = [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Tools\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                ffmpeg_info['installed'] = True
                ffmpeg_info['path'] = path
                ffmpeg_info['note'] = "Found but not in PATH"
                break
        else:
            ffmpeg_info['installed'] = False
            ffmpeg_info['note'] = "Not found. Install from https://ffmpeg.org/download.html"
    
    return ffmpeg_info

def check_python_audio_packages():
    """Check Python audio-related packages"""
    packages = {}
    
    audio_packages = [
        'ffmpeg-python',
        'pydub',
        'soundfile',
        'librosa',
        'pyaudio',
        'wave',
        'scipy'
    ]
    
    for package in audio_packages:
        try:
            module = __import__(package.replace('-', '_'))
            version = getattr(module, '__version__', 'Unknown')
            packages[package] = {
                'installed': True,
                'version': version
            }
        except ImportError:
            packages[package] = {
                'installed': False,
                'install_cmd': f'pip install {package}'
            }
    
    return packages

def check_cuda_cudnn():
    """Check CUDA and cuDNN versions"""
    cuda_info = {}
    
    # Check CUDA
    nvcc_output = run_command('nvcc --version')
    if nvcc_output:
        # Extract version from nvcc output
        for line in nvcc_output.split('\n'):
            if 'release' in line:
                cuda_info['cuda_version'] = line.strip()
                break
    
    # Check cuDNN (if available)
    cudnn_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\include\cudnn_version.h",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\include\cudnn_version.h",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include\cudnn_version.h"
    ]
    
    for path in cudnn_paths:
        if os.path.exists(path):
            cuda_info['cudnn_header_found'] = path
            break
    
    return cuda_info

def check_whisper_models():
    """Check for downloaded Whisper models"""
    model_info = {}
    
    # Check Hugging Face cache
    hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
    if os.path.exists(hf_cache):
        whisper_models = [d for d in os.listdir(hf_cache) if 'whisper' in d.lower()]
        model_info['huggingface_cache'] = whisper_models
    
    # Check faster-whisper cache
    fw_cache = os.path.expanduser("~/.cache/whisper")
    if os.path.exists(fw_cache):
        model_info['faster_whisper_cache'] = os.listdir(fw_cache)
    
    return model_info

def main():
    """Run all checks and save results"""
    print("Checking audio dependencies and Whisper setup...")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'ffmpeg': check_ffmpeg(),
        'python_audio_packages': check_python_audio_packages(),
        'cuda_cudnn': check_cuda_cudnn(),
        'whisper_models': check_whisper_models()
    }
    
    # Save results
    output_file = 'audio_deps_check.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nResults saved to: {output_file}")
    print("\nSummary:")
    print(f"- FFmpeg: {'Installed' if results['ffmpeg'].get('installed') else 'Not installed'}")
    
    missing_packages = [pkg for pkg, info in results['python_audio_packages'].items() 
                       if not info['installed']]
    if missing_packages:
        print(f"- Missing Python packages: {', '.join(missing_packages)}")
        print(f"  Install with: pip install {' '.join(missing_packages)}")
    else:
        print("- All Python audio packages installed")
    
    if results['whisper_models']:
        print(f"- Found Whisper models in cache")

if __name__ == "__main__":
    main()