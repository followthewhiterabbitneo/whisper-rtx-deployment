#!/usr/bin/env python3
"""
Get all transcript paths and create batch file to open them
"""

import pymysql
import json
import os

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def create_transcript_opener(loan_number):
    """Create a batch file that opens all transcripts for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all transcript paths for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            t.timestamp
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    recordings = cursor.fetchall()
    
    # Create batch file
    batch_file = f"open_loan_{loan_number}_transcripts.bat"
    with open(batch_file, 'w') as f:
        f.write(f"@echo off\n")
        f.write(f"echo Opening transcripts for loan #{loan_number}\n\n")
        
        for i, rec in enumerate(recordings, 1):
            path = rec['transcript_path']
            if path:
                # Convert to Windows path
                if path.startswith('C:/'):
                    path = path.replace('/', '\\')
                
                f.write(f"echo Opening transcript {i} of {len(recordings)}...\n")
                f.write(f'start "Transcript {rec["orkuid"]}" notepad.exe "{path}"\n')
                f.write(f"timeout /t 1 /nobreak > nul\n\n")
        
        f.write("echo All transcripts opened!\n")
        f.write("pause\n")
    
    cursor.close()
    conn.close()
    
    print(f"Created: {batch_file}")
    print(f"Double-click this file to open all {len(recordings)} transcripts in Notepad!")
    
    # Also create individual links
    links_dir = f"loan_{loan_number}_links"
    os.makedirs(links_dir, exist_ok=True)
    
    for i, rec in enumerate(recordings, 1):
        if rec['transcript_path']:
            link_file = os.path.join(links_dir, f"{i}_{rec['orkuid']}.bat")
            with open(link_file, 'w') as f:
                path = rec['transcript_path'].replace('/', '\\') if rec['transcript_path'].startswith('C:/') else rec['transcript_path']
                f.write(f'@echo off\n')
                f.write(f'notepad.exe "{path}"\n')
    
    print(f"Also created individual links in: {links_dir}/")

if __name__ == "__main__":
    loan = input("Enter loan number (default 1225290972): ") or "1225290972"
    create_transcript_opener(loan)