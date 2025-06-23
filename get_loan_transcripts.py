#!/usr/bin/env python3
"""
Get all transcripts for a specific loan number
"""

import pymysql
import json
import os
import sys

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def get_transcripts_for_loan(loan_number):
    """Get all transcript content for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all recordings for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.transcript_path,
            ct.loan_numbers,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            COALESCE(u.firstname + ' ' + u.lastname, 
                     COALESCE(t.localParty, t.remoteParty)) as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    recordings = cursor.fetchall()
    
    print(f"TRANSCRIPTS FOR LOAN #{loan_number}")
    print("=" * 80)
    print(f"Found {len(recordings)} recordings\n")
    
    # Create output directory
    output_dir = f"loan_{loan_number}_transcripts"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save summary file
    summary_file = os.path.join(output_dir, "summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"LOAN #{loan_number} - TRANSCRIPT SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Recordings: {len(recordings)}\n\n")
        
        for i, rec in enumerate(recordings, 1):
            orkuid = rec['orkuid']
            transcript_path = rec['transcript_path']
            timestamp = rec['timestamp']
            duration = rec['duration']
            parties = f"{rec['localParty']} <-> {rec['remoteParty']}"
            
            print(f"{i}. {orkuid}")
            print(f"   Date: {timestamp}")
            print(f"   Duration: {duration}s ({duration/60:.1f}m)")
            print(f"   Parties: {parties}")
            print(f"   Path: {transcript_path}")
            
            f.write(f"\n{i}. Recording: {orkuid}\n")
            f.write(f"   Date: {timestamp}\n")
            f.write(f"   Duration: {duration/60:.1f} minutes\n")
            f.write(f"   Parties: {parties}\n")
            
            # Try to read transcript
            transcript_content = None
            
            # Try original path
            if transcript_path and os.path.exists(transcript_path):
                with open(transcript_path, 'r', encoding='utf-8') as tf:
                    transcript_content = tf.read()
            # Try Windows path conversion
            elif transcript_path:
                win_path = transcript_path.replace('/', '\\')
                if os.path.exists(win_path):
                    with open(win_path, 'r', encoding='utf-8') as tf:
                        transcript_content = tf.read()
            
            if transcript_content:
                # Save individual transcript
                individual_file = os.path.join(output_dir, f"{i}_{orkuid}.txt")
                with open(individual_file, 'w', encoding='utf-8') as tf:
                    tf.write(f"Recording: {orkuid}\n")
                    tf.write(f"Date: {timestamp}\n")
                    tf.write(f"Duration: {duration/60:.1f} minutes\n")
                    tf.write(f"Parties: {parties}\n")
                    tf.write("-" * 80 + "\n\n")
                    tf.write(transcript_content)
                
                print(f"   ✓ Transcript saved")
                
                # Add preview to summary
                preview = transcript_content[:300].replace('\n', ' ')
                f.write(f"   Preview: {preview}...\n")
            else:
                print(f"   ✗ Transcript not found")
                f.write(f"   Status: Transcript not found\n")
            
            print()
    
    cursor.close()
    conn.close()
    
    print(f"\nAll transcripts saved to: {output_dir}/")
    print(f"Summary file: {summary_file}")
    
    # Also create a combined file
    combined_file = os.path.join(output_dir, "all_transcripts_combined.txt")
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write(f"LOAN #{loan_number} - ALL TRANSCRIPTS COMBINED\n")
        f.write("=" * 80 + "\n\n")
        
        for i in range(1, len(recordings) + 1):
            individual_file = os.path.join(output_dir, f"{i}_{recordings[i-1]['orkuid']}.txt")
            if os.path.exists(individual_file):
                with open(individual_file, 'r', encoding='utf-8') as tf:
                    f.write(tf.read())
                    f.write("\n\n" + "="*80 + "\n\n")
    
    print(f"Combined file: {combined_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        loan_number = sys.argv[1]
    else:
        loan_number = input("Enter loan number: ")
    
    get_transcripts_for_loan(loan_number)