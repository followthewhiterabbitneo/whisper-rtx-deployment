#!/usr/bin/env python3
"""
COMBINE LOAN TRANSCRIPTS - Create a single chronological transcript file
Includes processor assistants (947-242-1000 to 947-242-1099)
"""

import pymysql
import json
from datetime import datetime, timedelta
import os
import re

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def read_transcript_file(transcript_path):
    """Try to read a transcript file from various possible locations"""
    if not transcript_path:
        return "[No transcript path available]"
    
    # Convert Windows path to Unix if needed
    unix_path = transcript_path.replace('\\', '/')
    
    # Try different base paths
    possible_bases = [
        '/var/log/orkaudio.prod.nfs',
        '/mnt/transcripts',
        '/data/transcripts',
        '.'
    ]
    
    for base in possible_bases:
        full_path = os.path.join(base, unix_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass
    
    return f"[Transcript file not found: {transcript_path}]"

def combine_loan_transcripts(loan_number, output_file=None):
    """Combine all transcripts for a loan journey chronologically"""
    
    if not output_file:
        output_file = f"loan_{loan_number}_combined_transcript.txt"
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n📚 COMBINING TRANSCRIPTS FOR LOAN {loan_number}")
    print("=" * 60)
    
    # Get date range for the loan
    cursor.execute("""
        SELECT 
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
    """, (f'%{loan_number}%',))
    
    date_range = cursor.fetchone()
    if not date_range:
        print("No calls found for this loan!")
        return
    
    # Get key parties from first few calls
    cursor.execute("""
        SELECT DISTINCT t.localParty, t.remoteParty
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        LIMIT 5
    """, (f'%{loan_number}%',))
    
    party_rows = cursor.fetchall()
    key_parties = set()
    for row in party_rows:
        key_parties.add(row['localParty'])
        key_parties.add(row['remoteParty'])
    
    # Expand window and get ALL relevant calls
    start_date = date_range['first_mention'] - timedelta(days=2)
    end_date = date_range['last_mention'] + timedelta(days=2)
    
    print(f"\n📅 Date Range: {start_date.date()} to {end_date.date()}")
    print(f"🔑 Key Parties: {', '.join(sorted(key_parties))}")
    
    # Build query to get all relevant calls
    party_conditions = []
    params = [f'%{loan_number}%', start_date, end_date]
    
    for party in key_parties:
        party_conditions.append("t.localParty = %s OR t.remoteParty = %s")
        params.extend([party, party])
    
    query = f"""
        SELECT 
            t.orkUid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.transcript_text,
            ct.loan_numbers,
            ct.summary,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name,
            CASE 
                WHEN ct.loan_numbers LIKE %s THEN 'DIRECT'
                WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 'PROCESSOR'
                ELSE 'NETWORK'
            END as call_type
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE t.timestamp BETWEEN %s AND %s
        AND (
            ct.loan_numbers LIKE %s
            OR ({' OR '.join(party_conditions)})
            OR t.localParty LIKE '19472421%%' 
            OR t.remoteParty LIKE '19472421%%'
        )
        ORDER BY t.timestamp
    """
    
    params.insert(3, f'%{loan_number}%')  # For the loan check in AND clause
    cursor.execute(query, params)
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"\n📞 Found {len(calls)} calls to combine")
    
    # Write combined transcript
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write(f"COMBINED TRANSCRIPT FOR LOAN {loan_number}\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Date Range: {start_date.date()} to {end_date.date()}\n")
        f.write(f"Total Calls: {len(calls)}\n")
        
        # Stats
        direct_calls = sum(1 for c in calls if c['call_type'] == 'DIRECT')
        processor_calls = sum(1 for c in calls if c['call_type'] == 'PROCESSOR')
        network_calls = sum(1 for c in calls if c['call_type'] == 'NETWORK')
        
        f.write(f"\nCall Breakdown:\n")
        f.write(f"  - Direct Mentions: {direct_calls}\n")
        f.write(f"  - Processor Calls: {processor_calls}\n")
        f.write(f"  - Network Calls: {network_calls}\n")
        f.write("=" * 80 + "\n\n")
        
        # Process each call
        for idx, call in enumerate(calls, 1):
            # Check if this call mentions the loan
            has_loan = False
            mentioned_loans = []
            if call.get('loan_numbers'):
                try:
                    mentioned_loans = json.loads(call['loan_numbers'])
                    has_loan = loan_number in mentioned_loans
                except:
                    pass
            
            # Call header
            f.write("\n" + "="*80 + "\n")
            f.write(f"CALL #{idx} - {call['call_type']} {'[MENTIONS LOAN ✓]' if has_loan else ''}\n")
            f.write("="*80 + "\n")
            f.write(f"Date/Time: {call['timestamp']}\n")
            f.write(f"Duration: {call['duration']} seconds ({call['duration']/60:.1f} minutes)\n")
            f.write(f"From: {call['localParty']}\n")
            f.write(f"To: {call['remoteParty']}\n")
            f.write(f"User: {call['user_name']}\n")
            f.write(f"Call ID: {call['orkUid']}\n")
            
            if mentioned_loans:
                f.write(f"Loans Mentioned: {', '.join(mentioned_loans)}\n")
            
            if call.get('summary'):
                f.write(f"\nSummary: {call['summary']}\n")
            
            f.write(f"\nTranscript Path: {call.get('transcript_path', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")
            
            # Transcript content
            if call.get('transcript_text'):
                f.write("TRANSCRIPT:\n")
                f.write(call['transcript_text'])
                f.write("\n")
            else:
                # Try to read from file
                transcript_content = read_transcript_file(call.get('transcript_path'))
                f.write("TRANSCRIPT:\n")
                f.write(transcript_content)
                f.write("\n")
            
            f.write("\n")
    
    print(f"\n✅ Combined transcript saved to: {output_file}")
    print(f"📄 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    # Create summary statistics
    stats_file = f"loan_{loan_number}_journey_stats.txt"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(f"LOAN {loan_number} JOURNEY STATISTICS\n")
        f.write("=" * 50 + "\n\n")
        
        journey_days = (date_range['last_mention'] - date_range['first_mention']).days
        f.write(f"Journey Duration: {journey_days} days\n")
        f.write(f"First Mention: {date_range['first_mention']}\n")
        f.write(f"Last Mention: {date_range['last_mention']}\n")
        f.write(f"\nTotal Calls: {len(calls)}\n")
        f.write(f"  - Direct Mentions: {direct_calls}\n")
        f.write(f"  - Processor Calls: {processor_calls}\n")
        f.write(f"  - Network Calls: {network_calls}\n")
        
        # Party analysis
        f.write(f"\n\nMOST ACTIVE PARTIES:\n")
        party_counts = {}
        for call in calls:
            for party in [call['localParty'], call['remoteParty']]:
                party_counts[party] = party_counts.get(party, 0) + 1
        
        for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            party_type = ""
            if party.startswith('19472421'):
                party_type = " [PROCESSOR]"
            elif party in key_parties:
                party_type = " [KEY PARTY]"
            f.write(f"  {party}{party_type}: {count} calls\n")
        
        # Timeline summary
        f.write(f"\n\nCALL TIMELINE:\n")
        for idx, call in enumerate(calls, 1):
            has_loan = "✓" if call.get('loan_numbers') and loan_number in json.loads(call.get('loan_numbers', '[]')) else " "
            f.write(f"{idx:3d}. {call['timestamp'].strftime('%m/%d %I:%M%p')} [{has_loan}] {call['localParty'][:10]} -> {call['remoteParty'][:10]} ({call['duration']}s)\n")
    
    print(f"📊 Statistics saved to: {stats_file}")

if __name__ == "__main__":
    # Process our favorite loan
    loan_number = "1225237672"
    
    print("📚 LOAN TRANSCRIPT COMBINER")
    print("Creating chronological transcript including processor assistants")
    
    combine_loan_transcripts(loan_number)