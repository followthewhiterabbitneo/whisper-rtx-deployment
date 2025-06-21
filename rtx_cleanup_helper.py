#!/usr/bin/env python3
"""
RTX Cleanup Helper Script
Safely removes unnecessary files identified by the inventory script
Includes dry-run mode and confirmation prompts for safety
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import argparse

def format_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def find_files_to_clean(root_path="."):
    """Find files that can be safely cleaned"""
    
    cleanup_targets = {
        "temp_files": [],
        "pycache": [],
        "duplicate_downloads": [],
        "old_logs": [],
        "backup_files": []
    }
    
    total_size = 0
    
    # Patterns for temporary files
    temp_patterns = ['.bak', '.old', '.tmp', '~']
    duplicate_patterns = ['(1)', '(2)', '(3)', ' - Copy']
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Find __pycache__ directories
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            size = sum(os.path.getsize(os.path.join(pycache_path, f)) 
                      for f in os.listdir(pycache_path) if os.path.isfile(os.path.join(pycache_path, f)))
            cleanup_targets["pycache"].append((pycache_path, size))
            total_size += size
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(filepath, root_path)
            
            try:
                file_size = os.path.getsize(filepath)
                
                # Check for temp files
                if any(filename.endswith(pattern) for pattern in temp_patterns):
                    cleanup_targets["temp_files"].append((relative_path, file_size))
                    total_size += file_size
                
                # Check for duplicate downloads
                if any(pattern in filename for pattern in duplicate_patterns):
                    cleanup_targets["duplicate_downloads"].append((relative_path, file_size))
                    total_size += file_size
                
                # Check for old logs (older than 30 days)
                if filename.endswith('.log'):
                    file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))).days
                    if file_age > 30:
                        cleanup_targets["old_logs"].append((relative_path, file_size))
                        total_size += file_size
                
                # Check for backup files
                if '.backup' in filename or filename.startswith('backup_'):
                    cleanup_targets["backup_files"].append((relative_path, file_size))
                    total_size += file_size
                    
            except Exception as e:
                print(f"Error checking {relative_path}: {e}")
    
    return cleanup_targets, total_size

def safe_remove(filepath, dry_run=True):
    """Safely remove a file or directory"""
    try:
        if dry_run:
            print(f"  [DRY RUN] Would remove: {filepath}")
            return True
        else:
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
                print(f"  ✓ Removed directory: {filepath}")
            else:
                os.remove(filepath)
                print(f"  ✓ Removed file: {filepath}")
            return True
    except Exception as e:
        print(f"  ✗ Failed to remove {filepath}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean up unnecessary files in whisper-rtx-deployment")
    parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompts (use with caution!)")
    parser.add_argument("--category", choices=["temp_files", "pycache", "duplicate_downloads", "old_logs", "backup_files", "all"], 
                       default="all", help="Specific category to clean")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist!")
        return 1
    
    print(f"🔍 Scanning for cleanup targets in: {os.path.abspath(args.path)}")
    print("-" * 80)
    
    # Find files to clean
    cleanup_targets, total_size = find_files_to_clean(args.path)
    
    # Filter by category if specified
    if args.category != "all":
        cleanup_targets = {args.category: cleanup_targets[args.category]}
    
    # Display summary
    print("\n📊 CLEANUP SUMMARY:")
    categories_found = False
    
    for category, files in cleanup_targets.items():
        if files:
            categories_found = True
            category_size = sum(size for _, size in files)
            print(f"\n{category.upper().replace('_', ' ')} ({len(files)} items, {format_size(category_size)}):")
            
            # Show first 10 files as examples
            for filepath, size in files[:10]:
                print(f"  - {filepath} ({format_size(size)})")
            
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
    
    if not categories_found:
        print("\n✨ No unnecessary files found! Your project is already clean.")
        return 0
    
    print(f"\n💾 Total space that can be freed: {format_size(total_size)}")
    
    # Confirm before proceeding
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be deleted")
        proceed = True
    elif args.no_confirm:
        proceed = True
    else:
        response = input("\n⚠️  Proceed with cleanup? (yes/no): ")
        proceed = response.lower() in ['yes', 'y']
    
    if not proceed:
        print("\n❌ Cleanup cancelled.")
        return 0
    
    # Perform cleanup
    print(f"\n🧹 {'SIMULATING' if args.dry_run else 'PERFORMING'} CLEANUP...")
    
    success_count = 0
    fail_count = 0
    
    for category, files in cleanup_targets.items():
        if files:
            print(f"\n{category.upper().replace('_', ' ')}:")
            
            for filepath, size in files:
                full_path = os.path.join(args.path, filepath)
                if safe_remove(full_path, args.dry_run):
                    success_count += 1
                else:
                    fail_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    if args.dry_run:
        print(f"🔍 DRY RUN COMPLETE: Would remove {success_count} items, freeing {format_size(total_size)}")
        print("💡 Run without --dry-run to actually perform the cleanup")
    else:
        print(f"✅ CLEANUP COMPLETE: Removed {success_count} items")
        if fail_count > 0:
            print(f"⚠️  Failed to remove {fail_count} items")
        print(f"💾 Freed approximately {format_size(total_size)} of disk space")
    
    # Save cleanup log
    if not args.dry_run and success_count > 0:
        log_file = f"cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "path": os.path.abspath(args.path),
            "items_removed": success_count,
            "items_failed": fail_count,
            "space_freed": total_size,
            "space_freed_readable": format_size(total_size),
            "categories": {k: len(v) for k, v in cleanup_targets.items() if v}
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n📝 Cleanup log saved to: {log_file}")

if __name__ == "__main__":
    exit(main())