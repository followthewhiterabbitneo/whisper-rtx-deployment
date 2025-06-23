#!/usr/bin/env python3
"""
Check how many recordings are already processed
"""

import pymysql
import os

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Check database
conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

# Check processed recordings
cursor.execute("SELECT COUNT(*) as count FROM call_transcripts_v2")
result = cursor.fetchone()
print(f"Recordings in database: {result['count']}")

# Check loan index
cursor.execute("SELECT COUNT(DISTINCT orkuid) as count FROM loan_number_index")
result = cursor.fetchone()
print(f"Recordings in loan index: {result['count']}")

# Check transcripts directory
transcript_dir = "C:/transcripts" if os.name == 'nt' else "transcripts"
if os.path.exists(transcript_dir):
    count = sum(1 for root, dirs, files in os.walk(transcript_dir) for f in files if f.endswith('.txt'))
    print(f"Transcript files on disk: {count}")

cursor.close()
conn.close()