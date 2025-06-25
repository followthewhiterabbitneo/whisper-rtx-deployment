#!/usr/bin/env python3
"""
LOAN SURGICAL TRACKER - Track ONLY calls that mention the loan
Plus processor assistants who work on it
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

def track_loan_surgical(loan_number):
    """Track ONLY calls that actually mention this loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n🎯 SURGICAL TRACKING FOR LOAN {loan_number}")
    print("=" * 60)
    
    # Get ALL calls that mention this loan - PERIOD
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.loan_numbers,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    
    if not calls:
        print("No calls found for this loan!")
        return
    
    print(f"\n📞 Found {len(calls)} calls that mention loan {loan_number}")
    
    # Analyze the calls
    first_call = calls[0]
    last_call = calls[-1]
    
    print(f"\n📍 FIRST MENTION: {first_call['timestamp']}")
    print(f"📍 LAST MENTION: {last_call['timestamp']}")
    print(f"📍 JOURNEY: {(last_call['timestamp'] - first_call['timestamp']).days} days")
    
    # Track who's involved
    parties = {}
    processor_calls = []
    
    print(f"\n📊 CALL TIMELINE:")
    print("-" * 100)
    print(f"{'#':<3} {'Date':<10} {'Time':<8} {'From':<15} {'To':<15} {'Duration':<10} {'User':<20}")
    print("-" * 100)
    
    for idx, call in enumerate(calls, 1):
        # Track parties
        for party in [call['localParty'], call['remoteParty']]:
            parties[party] = parties.get(party, 0) + 1
            
        # Check if processor assistant
        is_processor = False
        if call['localParty'].startswith('19472421') or call['remoteParty'].startswith('19472421'):
            is_processor = True
            processor_calls.append(call)
        
        # Print call info
        date_str = call['timestamp'].strftime('%m/%d/%Y')
        time_str = call['timestamp'].strftime('%I:%M %p')
        duration_str = f"{call['duration']}s"
        
        print(f"{idx:<3} {date_str:<10} {time_str:<8} {call['localParty']:<15} {call['remoteParty']:<15} {duration_str:<10} {call['user_name']:<20}")
    
    # Find the loan officer (most frequent non-processor party)
    print(f"\n👥 PARTIES INVOLVED:")
    loan_officer = None
    max_count = 0
    
    for party, count in sorted(parties.items(), key=lambda x: x[1], reverse=True):
        party_type = ""
        if party.startswith('19472421'):
            party_type = " [PROCESSOR]"
        elif party.startswith('1800') or party.startswith('1855') or party.startswith('1866'):
            party_type = " [TOLL-FREE]"
        else:
            if count > max_count and not party.startswith('19472421'):
                loan_officer = party
                max_count = count
        
        print(f"   {party}{party_type}: {count} calls")
    
    print(f"\n🏆 LIKELY LOAN OFFICER: {loan_officer} ({max_count} calls)")
    
    # Processor assistant analysis
    if processor_calls:
        print(f"\n🤖 PROCESSOR ASSISTANT INVOLVEMENT:")
        print(f"   Total processor calls: {len(processor_calls)}")
        first_processor = processor_calls[0]['timestamp']
        last_processor = processor_calls[-1]['timestamp']
        print(f"   First processor call: {first_processor}")
        print(f"   Last processor call: {last_processor}")
        print(f"   Processor window: {(last_processor - first_processor).days} days")
    
    # Create focused transcript
    output_file = f"loan_{loan_number}_surgical.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"SURGICAL TRANSCRIPT FOR LOAN {loan_number}\n")
        f.write(f"Only calls that mention this loan\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total Calls: {len(calls)}\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, call in enumerate(calls, 1):
            f.write(f"\nCALL #{idx}\n")
            f.write(f"Date/Time: {call['timestamp']}\n")
            f.write(f"From: {call['localParty']} To: {call['remoteParty']}\n")
            f.write(f"Duration: {call['duration']}s\n")
            f.write(f"User: {call['user_name']}\n")
            f.write(f"Transcript: {call.get('transcript_path', 'N/A')}\n")
            f.write("-" * 40 + "\n")
    
    print(f"\n✅ Surgical transcript saved to: {output_file}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Track our test loan
    loan_number = "1225237672"
    
    print("🔬 LOAN SURGICAL TRACKER")
    print("Tracking ONLY calls that mention the loan")
    
    track_loan_surgical(loan_number)