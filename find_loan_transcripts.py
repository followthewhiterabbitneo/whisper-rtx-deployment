#!/usr/bin/env python3
"""
Find all transcripts that contain loan numbers
"""

import os
import pymysql
import json

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def find_transcripts_with_loans():
    """Find all recordings that have loan numbers"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all recordings with loan numbers
    cursor.execute("""
        SELECT orkuid, loan_numbers, transcript_path
        FROM call_transcripts_v2
        WHERE loan_numbers IS NOT NULL 
        AND loan_numbers != '[]'
        ORDER BY created_at DESC
    """)
    
    recordings = cursor.fetchall()
    
    print(f"Found {len(recordings)} recordings with loan numbers:\n")
    
    for rec in recordings:
        loans = json.loads(rec['loan_numbers'])
        path = rec['transcript_path']
        
        print(f"orkuid: {rec['orkuid']}")
        print(f"Loans: {loans}")
        print(f"Path: {path}")
        
        # Check if file exists
        if os.path.exists(path):
            # Read first 200 chars
            with open(path, 'r', encoding='utf-8') as f:
                preview = f.read(200)
                print(f"Preview: {preview}...")
        else:
            # Try Windows path
            win_path = path.replace('/', '\\')
            if os.path.exists(win_path):
                print(f"Found at: {win_path}")
            else:
                print("File not found!")
        
        print("-" * 60)
    
    # Summary of loan numbers
    cursor.execute("""
        SELECT DISTINCT loan_number, COUNT(*) as count
        FROM loan_number_index
        GROUP BY loan_number
        ORDER BY count DESC
    """)
    
    loan_summary = cursor.fetchall()
    
    print("\nLOAN NUMBER SUMMARY:")
    print("="*40)
    for loan in loan_summary:
        print(f"Loan #{loan['loan_number']}: {loan['count']} recordings")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    find_transcripts_with_loans()