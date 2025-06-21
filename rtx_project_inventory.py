#!/usr/bin/env python3
"""
RTX Project Inventory Script
Analyzes the whisper-rtx-deployment project structure on Windows RTX workstation
Identifies files, sizes, types, and potential cleanup candidates
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import shutil

def get_file_hash(filepath, chunk_size=8192):
    """Calculate MD5 hash of a file for duplicate detection"""
    try:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def format_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def analyze_project(root_path="."):
    """Analyze project structure and contents"""
    
    # Data structures for analysis
    file_types = defaultdict(list)
    file_sizes = defaultdict(int)
    duplicate_candidates = defaultdict(list)
    large_files = []
    temp_files = []
    model_files = []
    audio_files = []
    transcription_files = []
    
    # Scan configuration
    large_file_threshold = 50 * 1024 * 1024  # 50MB
    temp_patterns = ['tmp', 'temp', '~', '.bak', '.old', '(1)', '(2)', '.pyc', '__pycache__']
    model_extensions = ['.bin', '.safetensors', '.onnx', '.pt', '.pth', '.ckpt', '.h5']
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma', '.aac']
    
    total_files = 0
    total_size = 0
    
    print(f"Scanning project directory: {os.path.abspath(root_path)}")
    print("-" * 80)
    
    # Walk through directory tree
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(filepath, root_path)
            
            try:
                file_stat = os.stat(filepath)
                file_size = file_stat.st_size
                file_ext = Path(filename).suffix.lower()
                
                total_files += 1
                total_size += file_size
                
                # Categorize by extension
                file_types[file_ext].append((relative_path, file_size))
                file_sizes[file_ext] += file_size
                
                # Check for large files
                if file_size > large_file_threshold:
                    large_files.append((relative_path, file_size))
                
                # Check for temp files
                if any(pattern in filename.lower() for pattern in temp_patterns):
                    temp_files.append((relative_path, file_size))
                
                # Check for model files
                if file_ext in model_extensions or 'model' in filename.lower():
                    model_files.append((relative_path, file_size))
                
                # Check for audio files
                if file_ext in audio_extensions:
                    audio_files.append((relative_path, file_size))
                
                # Check for transcription files
                if 'transcription' in filepath.lower() or relative_path.startswith('transcriptions'):
                    transcription_files.append((relative_path, file_size))
                
                # Calculate hash for duplicate detection (only for files < 100MB)
                if file_size < 100 * 1024 * 1024 and file_size > 0:
                    file_hash = get_file_hash(filepath)
                    if file_hash:
                        duplicate_candidates[file_hash].append((relative_path, file_size))
                
            except Exception as e:
                print(f"Error processing {relative_path}: {e}")
    
    # Generate report
    report = {
        "scan_timestamp": datetime.now().isoformat(),
        "project_path": os.path.abspath(root_path),
        "total_files": total_files,
        "total_size": total_size,
        "total_size_readable": format_size(total_size),
        "disk_usage": shutil.disk_usage(root_path)._asdict() if os.path.exists(root_path) else None
    }
    
    # Print summary
    print(f"\n📊 PROJECT SUMMARY")
    print(f"Total files: {total_files}")
    print(f"Total size: {format_size(total_size)}")
    
    # Directory structure
    print(f"\n📁 KEY DIRECTORIES:")
    key_dirs = ['models', 'wav', 'transcriptions', 'downloads', 'logs', 'cache']
    for dir_name in key_dirs:
        dir_path = os.path.join(root_path, dir_name)
        if os.path.exists(dir_path):
            dir_size = sum(os.path.getsize(os.path.join(dp, f)) 
                          for dp, dn, fn in os.walk(dir_path) for f in fn)
            print(f"  /{dir_name}: {format_size(dir_size)}")
    
    # File type analysis
    print(f"\n📄 FILE TYPES:")
    sorted_types = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)[:10]
    for ext, size in sorted_types:
        count = len(file_types[ext])
        if ext == '':
            ext = '(no extension)'
        print(f"  {ext}: {count} files, {format_size(size)}")
    
    # Model files
    if model_files:
        print(f"\n🤖 MODEL FILES ({len(model_files)}):")
        for path, size in sorted(model_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {path}: {format_size(size)}")
    
    # Audio files
    if audio_files:
        print(f"\n🎵 AUDIO FILES ({len(audio_files)}):")
        for path, size in sorted(audio_files, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {path}: {format_size(size)}")
    
    # Transcription files
    if transcription_files:
        print(f"\n📝 TRANSCRIPTION FILES ({len(transcription_files)}):")
        for path, size in transcription_files[:10]:
            print(f"  {path}: {format_size(size)}")
    
    # Large files
    if large_files:
        print(f"\n💾 LARGE FILES (>{format_size(large_file_threshold)}):")
        for path, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {path}: {format_size(size)}")
    
    # Potential duplicates
    duplicates = [(hash_val, files) for hash_val, files in duplicate_candidates.items() if len(files) > 1]
    if duplicates:
        print(f"\n🔄 POTENTIAL DUPLICATES:")
        total_wasted = 0
        for hash_val, files in duplicates[:10]:
            if len(files) > 1:
                wasted_space = sum(f[1] for f in files[1:])
                total_wasted += wasted_space
                print(f"  Duplicate set ({format_size(files[0][1])} each, {format_size(wasted_space)} wasted):")
                for path, size in files:
                    print(f"    - {path}")
        report["duplicate_space_wasted"] = total_wasted
        print(f"\n  Total duplicate space: {format_size(total_wasted)}")
    
    # Temporary files
    if temp_files:
        print(f"\n🗑️ TEMPORARY/BACKUP FILES:")
        temp_total = sum(size for _, size in temp_files)
        for path, size in temp_files[:10]:
            print(f"  {path}: {format_size(size)}")
        print(f"  Total temporary file space: {format_size(temp_total)}")
        report["temp_file_space"] = temp_total
    
    # Cleanup recommendations
    print(f"\n🧹 CLEANUP RECOMMENDATIONS:")
    recommendations = []
    
    if duplicates:
        recommendations.append(f"- Remove duplicate files to save {format_size(total_wasted)}")
    
    if temp_files:
        temp_total = sum(size for _, size in temp_files)
        recommendations.append(f"- Clean temporary files to save {format_size(temp_total)}")
    
    # Check for old logs
    log_files = [f for f in file_types.get('.log', [])]
    if len(log_files) > 10:
        recommendations.append(f"- Archive or remove old log files ({len(log_files)} found)")
    
    # Check for __pycache__
    pycache_size = sum(size for path, size in file_types.get('.pyc', []))
    if pycache_size > 0:
        recommendations.append(f"- Clean Python cache files to save {format_size(pycache_size)}")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("  No immediate cleanup needed!")
    
    # Save detailed report
    report_file = f"project_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report["file_types"] = {ext: len(files) for ext, files in file_types.items()}
    report["large_files"] = [(p, s) for p, s in large_files]
    report["model_files"] = model_files
    report["audio_files"] = audio_files
    report["temp_files"] = temp_files
    report["recommendations"] = recommendations
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📊 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    import sys
    
    # Use provided path or current directory
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    if not os.path.exists(project_path):
        print(f"Error: Path '{project_path}' does not exist!")
        sys.exit(1)
    
    # Run analysis
    report = analyze_project(project_path)