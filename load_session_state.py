#!/usr/bin/env python3
"""
Load Session State Tool
Loads a previous session snapshot and shows current status
"""

import json
import sys
import subprocess
import os
from datetime import datetime

def load_snapshot(snapshot_file=None):
    """Load session snapshot"""
    if not snapshot_file:
        # Find most recent snapshot
        snapshots = [f for f in os.listdir('.') if f.startswith('SESSION_') and f.endswith('.json')]
        if not snapshots:
            print("❌ No session snapshots found")
            print("💡 Run 'python save_session_state.py' to create one")
            return
        snapshot_file = sorted(snapshots)[-1]
    
    try:
        with open(snapshot_file, 'r') as f:
            snapshot = json.load(f)
        
        print(f"📚 Loading session from: {snapshot_file}")
        print(f"📅 Saved: {snapshot['date']}")
        print(f"\n🌿 Git Status at save:")
        print(f"   Branch: {snapshot['git']['branch']}")
        
        # Show current git status
        current_branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        print(f"\n🔄 Current Git Status:")
        print(f"   Branch: {current_branch}")
        if current_branch != snapshot['git']['branch']:
            print(f"   ⚠️  Branch changed from {snapshot['git']['branch']}")
        
        # Check for uncommitted changes
        current_status = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
        if current_status:
            print(f"   ⚠️  Uncommitted changes present")
        
        print(f"\n📁 Recently modified files:")
        for f in snapshot['recent_files'][:10]:
            print(f"   {f}")
        
        print(f"\n🚀 Quick Resume Commands:")
        for cmd in snapshot['quick_resume_commands']:
            print(f"   {cmd}")
        
        print(f"\n📋 Project Status:")
        for proj, info in snapshot['current_projects'].items():
            print(f"\n   {proj}:")
            print(f"   - Status: {info['status']}")
            print(f"   - Last: {info['last_success']}")
            print(f"   - Next: {', '.join(info['next_steps'])}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Review CLAUDE.local.md for detailed context")
        print(f"   2. Check git status and pull if needed")
        print(f"   3. Resume from project status above")
        
    except Exception as e:
        print(f"❌ Error loading snapshot: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        load_snapshot(sys.argv[1])
    else:
        load_snapshot()