#!/usr/bin/env python3
"""
Update all database host references from s01vdsoxweb047 to s40vpsoxweb002
"""

import os
import re

print("=" * 80)
print("DATABASE HOST UPDATE")
print("=" * 80)

# Files to update
files_to_update = [
    'connect_mariadb_direct.py',
    'connect_mariadb_ssh_tunnel.py',
    'find_eric_rawlins_calls.py',
    'create_hybrid_schema.py',
    'create_hybrid_schema_mariadb55.py',
    'extract_database_schema.py',
    'extract_database_schema_fixed.py',
    'visualize_database_erd.py',
    'explore_oreka_db.py',
    'explore_core_tables.py',
    'scream_batch_processor.py',
    'scream_hybrid_pipeline.py'
]

old_host = 's01vdsoxweb047'
new_host = 's40vpsoxweb002'

print(f"\nUpdating database host from {old_host} to {new_host}")
print("-" * 80)

updated_count = 0

for filename in files_to_update:
    if os.path.exists(filename):
        print(f"\n✓ Processing {filename}...")
        
        # Read file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count occurrences
        occurrences = content.count(old_host)
        
        if occurrences > 0:
            # Replace host
            new_content = content.replace(old_host, new_host)
            
            # Write back
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  Updated {occurrences} occurrences")
            updated_count += 1
        else:
            print(f"  No changes needed")
    else:
        print(f"\n✗ File not found: {filename}")

print("\n" + "=" * 80)
print(f"✅ Updated {updated_count} files")
print(f"   Old host: {old_host}")
print(f"   New host: {new_host}")
print("=" * 80)
print("\nRun this script on your laptop, then:")
print("git add -A && git commit -m 'Update database host to s40vpsoxweb002'")
print("git push")