#!/usr/bin/env python3
"""
Analyze inventory results from RTX workstation
Reads the project_inventory JSON file and provides detailed cleanup recommendations
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def format_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def analyze_inventory(json_file):
    """Analyze the inventory JSON and provide recommendations"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("📊 RTX PROJECT INVENTORY ANALYSIS")
    print("=" * 80)
    
    # Basic stats
    print(f"\n📁 PROJECT OVERVIEW:")
    print(f"Location: {data.get('project_path', 'Unknown')}")
    print(f"Scan time: {data.get('scan_timestamp', 'Unknown')}")
    print(f"Total files: {data.get('total_files', 0):,}")
    print(f"Total size: {data.get('total_size_readable', 'Unknown')}")
    
    # Disk usage
    if 'disk_usage' in data and data['disk_usage']:
        disk = data['disk_usage']
        used_percent = (disk['used'] / disk['total']) * 100 if disk['total'] > 0 else 0
        print(f"\n💾 DISK USAGE:")
        print(f"Total disk: {format_size(disk['total'])}")
        print(f"Used: {format_size(disk['used'])} ({used_percent:.1f}%)")
        print(f"Free: {format_size(disk['free'])}")
    
    # File types breakdown
    if 'file_types' in data:
        print(f"\n📄 TOP FILE TYPES BY COUNT:")
        sorted_types = sorted(data['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]
        for ext, count in sorted_types:
            if ext == '':
                ext = '(no extension)'
            print(f"  {ext}: {count} files")
    
    # Large files
    if 'large_files' in data and data['large_files']:
        print(f"\n💾 LARGE FILES (>50MB):")
        total_large = sum(size for _, size in data['large_files'])
        print(f"Total: {format_size(total_large)} in {len(data['large_files'])} files")
        for path, size in data['large_files'][:5]:
            print(f"  {path}: {format_size(size)}")
        if len(data['large_files']) > 5:
            print(f"  ... and {len(data['large_files']) - 5} more")
    
    # Model files
    if 'model_files' in data and data['model_files']:
        print(f"\n🤖 MODEL FILES:")
        total_models = sum(size for _, size in data['model_files'])
        print(f"Total: {format_size(total_models)} in {len(data['model_files'])} files")
        for path, size in data['model_files'][:5]:
            print(f"  {path}: {format_size(size)}")
    
    # Audio files
    if 'audio_files' in data and data['audio_files']:
        print(f"\n🎵 AUDIO FILES:")
        total_audio = sum(size for _, size in data['audio_files'])
        print(f"Total: {format_size(total_audio)} in {len(data['audio_files'])} files")
        
    # Cleanup opportunities
    print(f"\n🧹 CLEANUP OPPORTUNITIES:")
    
    total_cleanup = 0
    
    # Duplicate space
    if 'duplicate_space_wasted' in data:
        dup_space = data['duplicate_space_wasted']
        if dup_space > 0:
            print(f"\n📋 Duplicate files: {format_size(dup_space)}")
            total_cleanup += dup_space
    
    # Temp files
    if 'temp_file_space' in data:
        temp_space = data['temp_file_space']
        if temp_space > 0:
            print(f"🗑️  Temporary files: {format_size(temp_space)}")
            total_cleanup += temp_space
    
    # Check temp files list
    if 'temp_files' in data and data['temp_files']:
        print(f"   Found {len(data['temp_files'])} temp files:")
        for path, size in data['temp_files'][:5]:
            print(f"   - {path}: {format_size(size)}")
        if len(data['temp_files']) > 5:
            print(f"   ... and {len(data['temp_files']) - 5} more")
    
    # Python cache
    pyc_count = data.get('file_types', {}).get('.pyc', 0)
    if pyc_count > 0:
        print(f"🐍 Python cache files: {pyc_count} .pyc files")
    
    print(f"\n💰 TOTAL POTENTIAL SAVINGS: {format_size(total_cleanup)}")
    
    # Recommendations
    if 'recommendations' in data and data['recommendations']:
        print(f"\n📋 AUTOMATED RECOMMENDATIONS:")
        for rec in data['recommendations']:
            print(f"  {rec}")
    
    # Additional recommendations based on analysis
    print(f"\n🎯 CLEANUP ACTIONS:")
    print("1. Run cleanup script in dry-run mode first:")
    print("   python rtx_cleanup_helper.py --dry-run")
    
    if 'duplicate_space_wasted' in data and data['duplicate_space_wasted'] > 0:
        print("\n2. Remove duplicate files:")
        print("   python rtx_cleanup_helper.py --category duplicate_downloads")
    
    if 'temp_file_space' in data and data['temp_file_space'] > 0:
        print("\n3. Clean temporary files:")
        print("   python rtx_cleanup_helper.py --category temp_files")
    
    if pyc_count > 0:
        print("\n4. Clear Python cache:")
        print("   python rtx_cleanup_helper.py --category pycache")
    
    # Model optimization
    if 'model_files' in data and data['model_files']:
        model_size = sum(size for _, size in data['model_files'])
        if model_size > 5 * 1024 * 1024 * 1024:  # 5GB
            print("\n5. Model files are using significant space. Consider:")
            print("   - Removing older model versions if you have multiple")
            print("   - Using symlinks if models are duplicated across projects")
    
    # Completion
    print("\n✅ Analysis complete!")
    
    # Save summary
    summary_file = f"inventory_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"RTX Project Inventory Summary\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total files: {data.get('total_files', 0):,}\n")
        f.write(f"Total size: {data.get('total_size_readable', 'Unknown')}\n")
        f.write(f"Potential savings: {format_size(total_cleanup)}\n")
    
    print(f"\n📝 Summary saved to: {summary_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_inventory_results.py <inventory_json_file>")
        print("Example: python analyze_inventory_results.py project_inventory_20250621_172132.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found!")
        sys.exit(1)
    
    analyze_inventory(json_file)