#!/usr/bin/env python3
"""
FIND UNTRANSCRIBED CALLS - Identify calls that need transcription
"""

import pymysql
import json
from datetime import datetime

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def find_untranscribed_for_loan(loan_number):
    """Find all untranscribed calls for a specific loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n🔍 FINDING UNTRANSCRIBED CALLS FOR LOAN {loan_number}")
    print("=" * 80)
    
    # Get calls without transcripts
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            t.filename,
            ct.transcript_path,
            ct.transcript_text,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        AND (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    untranscribed = cursor.fetchall()
    
    if not untranscribed:
        print("✅ All calls have been transcribed!")
        cursor.close()
        conn.close()
        return
    
    print(f"\n⚠️ Found {len(untranscribed)} untranscribed calls:")
    print("-" * 100)
    print(f"{'#':<3} {'Date/Time':<20} {'Duration':<10} {'From':<15} {'To':<15} {'Audio File':<40}")
    print("-" * 100)
    
    total_duration = 0
    
    for idx, call in enumerate(untranscribed, 1):
        date_str = call['timestamp'].strftime('%m/%d/%Y %I:%M %p')
        duration_str = f"{call['duration']}s"
        total_duration += call['duration']
        
        # Build audio file path
        audio_file = call['filename'] or f"{call['orkuid']}.wav"
        
        print(f"{idx:<3} {date_str:<20} {duration_str:<10} {call['localParty']:<15} {call['remoteParty']:<15} {audio_file:<40}")
    
    print("-" * 100)
    print(f"\nTotal untranscribed duration: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    # Generate transcription queue file
    queue_file = f"transcribe_queue_loan_{loan_number}.txt"
    
    with open(queue_file, 'w') as f:
        f.write(f"# Transcription Queue for Loan {loan_number}\n")
        f.write(f"# Generated: {datetime.now()}\n")
        f.write(f"# Total Files: {len(untranscribed)}\n")
        f.write(f"# Total Duration: {total_duration/60:.1f} minutes\n\n")
        
        for call in untranscribed:
            # Build expected audio path
            ts = call['timestamp']
            year = ts.strftime('%Y')
            month = ts.strftime('%m')
            day = ts.strftime('%d')
            hour = ts.strftime('%H')
            
            audio_path = f"/var/log/orkaudio.prod.nfs/audio/{year}/{month}/{day}/{hour}/{call['filename'] or call['orkuid'] + '.wav'}"
            
            f.write(f"{call['orkuid']}|{audio_path}\n")
    
    print(f"\n📄 Transcription queue saved to: {queue_file}")
    
    cursor.close()
    conn.close()
    
    return untranscribed

def find_all_untranscribed():
    """Find ALL untranscribed calls in the system"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("\n🔍 FINDING ALL UNTRANSCRIBED CALLS")
    print("=" * 80)
    
    # Count total untranscribed
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM call_transcripts_v2 ct
        WHERE (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
    """)
    
    total_count = cursor.fetchone()['count']
    
    print(f"\n⚠️ Total untranscribed calls: {total_count}")
    
    # Get breakdown by loan
    cursor.execute("""
        SELECT 
            ct.loan_numbers,
            COUNT(*) as untranscribed_count,
            SUM(t.duration) as total_duration
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
        AND ct.loan_numbers != '[]'
        GROUP BY ct.loan_numbers
        ORDER BY untranscribed_count DESC
        LIMIT 20
    """)
    
    loans_needing_transcription = cursor.fetchall()
    
    print(f"\nTop loans needing transcription:")
    print("-" * 80)
    print(f"{'Loan #':<15} {'Untranscribed':<15} {'Duration (min)':<15}")
    print("-" * 80)
    
    for row in loans_needing_transcription:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:  # First loan from group
                duration_min = row['total_duration'] / 60 if row['total_duration'] else 0
                print(f"{loan:<15} {row['untranscribed_count']:<15} {duration_min:<15.1f}")
        except:
            pass
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            find_all_untranscribed()
        else:
            loan_number = sys.argv[1]
            find_untranscribed_for_loan(loan_number)
    else:
        print("Usage:")
        print("  python find_untranscribed_calls.py <loan_number>")
        print("  python find_untranscribed_calls.py --all")
        
        choice = input("\nEnter loan number (or 'all'): ").strip()
        if choice.lower() == 'all':
            find_all_untranscribed()
        else:
            find_untranscribed_for_loan(choice)