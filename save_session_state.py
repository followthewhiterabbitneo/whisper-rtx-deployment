#!/usr/bin/env python3
"""
Session State Snapshot Tool
Creates a timestamped snapshot of current work state for easy resumption
"""

import datetime
import json
import subprocess
import os

def get_git_status():
    """Get current git status"""
    try:
        status = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
        branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        return {'branch': branch, 'changes': status}
    except:
        return {'branch': 'unknown', 'changes': ''}

def get_recent_files():
    """Get recently modified files"""
    try:
        # Find files modified in last 24 hours
        cmd = ['find', '.', '-type', 'f', '-mtime', '-1', '-not', '-path', './.git/*']
        files = subprocess.check_output(cmd, text=True).strip().split('\n')
        return [f for f in files if f and not f.startswith('./SESSION_')]
    except:
        return []

def create_snapshot():
    """Create session snapshot"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_file = f"SESSION_{timestamp}.json"
    
    snapshot = {
        'timestamp': timestamp,
        'date': datetime.datetime.now().isoformat(),
        'git': get_git_status(),
        'recent_files': get_recent_files()[:20],  # Top 20 recent files
        'current_projects': {
            'whisper_rtx': {
                'status': 'Transcription working, Gemma 2 pending extraction',
                'last_success': 'Eric Rawlins transcription',
                'next_steps': ['Extract Gemma 2 model', 'Implement batch processing']
            }
        },
        'environments': {
            'local': os.getcwd(),
            'remote': '/moneyball/whisper-rtx-deployment',
            'rtx': 'C:\\Users\\estillmane\\.aria\\whisper-rtx-deployment'
        },
        'quick_resume_commands': [
            'git pull',
            'python test_ssh_connection.py',
            'python process_one_recording.py',
            'cd /moneyball/whisper-rtx-deployment && source /moneyball/gemma-env/bin/activate'
        ]
    }
    
    # Write snapshot
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    # Also append key info to CLAUDE.local.md
    with open('CLAUDE.local.md', 'a') as f:
        f.write(f"\n\n# Session Snapshot {timestamp}\n")
        f.write(f"- Git branch: {snapshot['git']['branch']}\n")
        f.write(f"- Recent files: {len(snapshot['recent_files'])}\n")
        f.write(f"- Snapshot saved: {snapshot_file}\n")
    
    print(f"✅ Session snapshot saved to: {snapshot_file}")
    print(f"✅ CLAUDE.local.md updated")
    print(f"\n📋 To resume next session:")
    print(f"   1. python load_session_state.py {snapshot_file}")
    print(f"   2. Check CLAUDE.local.md for context")
    print(f"   3. git pull (if needed)")

if __name__ == "__main__":
    create_snapshot()