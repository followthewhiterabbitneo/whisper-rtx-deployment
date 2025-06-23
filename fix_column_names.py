#!/usr/bin/env python3
"""
Fix column names in all scripts - orktape uses different column names
"""

import os
import re

print("=" * 80)
print("FIXING COLUMN NAMES")
print("=" * 80)

# Files to update
files_to_update = [
    'find_eric_rawlins_calls.py',
    'find_any_recordings.py',
    'explore_core_tables.py',
    'scream_batch_processor.py',
    'scream_hybrid_pipeline.py',
    'create_hybrid_schema_mariadb55.py'
]

# Column name mappings
replacements = [
    # orktape columns
    ('r.orkuid', 'r.orkUid'),
    ('t.uid', 't.orkUid'),
    ('t.localparty', 't.localParty'),
    ('t.remoteparty', 't.remoteParty'),
    ('r.localparty', 'r.localParty'),
    ('r.remoteparty', 'r.remoteParty'),
    ("'orkuid'", "'orkUid'"),
    ('localparty', 'localParty'),  # for SELECT statements
    ('remoteparty', 'remoteParty'),
    
    # orksegment foreign keys
    ('s.fktape', 's.tape_id'),
    ('s.fkuser', 's.user_id'),
    ('s.fkrecordings', 's.tape_id'),
    ('s.fkorkusers', 's.user_id'),
    
    # orkuser columns
    ('u.uid', 'u.id'),
    
    # Fix table aliases
    ('orktape.uid', 'orktape.orkUid'),
    ('FROM recordings', 'FROM orktape'),
    ('JOIN recordings', 'JOIN orktape'),
    
    # Fix incorrect references
    ('on t.uid = ct.orkuid', 'on t.orkUid = ct.orkuid'),
    ('ct.uid', 'ct.orkuid'),
]

print("\nProcessing files...")
print("-" * 40)

for filename in files_to_update:
    if os.path.exists(filename):
        print(f"\n✓ Processing {filename}...")
        
        # Read file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track changes
        changes = 0
        
        # Apply replacements
        for old, new in replacements:
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                changes += count
                print(f"  Replaced '{old}' with '{new}' ({count} times)")
        
        # Special case for 'uid' in SELECT (case-sensitive)
        # Replace 'SELECT uid' with 'SELECT orkUid as orkuid'
        content = re.sub(r'SELECT\s+uid\b', 'SELECT orkUid as orkuid', content)
        content = re.sub(r'SELECT\s+t\.uid\b', 'SELECT t.orkUid as orkuid', content)
        content = re.sub(r'SELECT\s+r\.uid\b', 'SELECT r.orkUid as orkuid', content)
        
        # Write back if changes made
        if changes > 0 or 'SELECT orkUid as orkuid' in content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Updated with {changes} replacements")
        else:
            print(f"  No changes needed")
    else:
        print(f"\n✗ File not found: {filename}")

print("\n" + "=" * 80)
print("Column names fixed!")
print("Now run: git add -A && git commit -m 'Fix column names for orktape/orksegment tables'")
print("git push")