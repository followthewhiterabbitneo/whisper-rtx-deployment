#!/usr/bin/env python3
"""
LOAN JOURNEY TRACKER - Follow the bouncing ball from submission to CTC
Track processor assistants (947-242-1000 to 947-242-1099)
"""

import pymysql
import json
from datetime import datetime, timedelta
import os

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def track_loan_journey(loan_number):
    """Track a loan from first mention to last, following the bouncing ball"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print(f"\n🎯 TRACKING LOAN {loan_number} JOURNEY")
    print("=" * 60)
    
    # Step 1: Find FIRST mention of loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.loan_numbers
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp ASC
        LIMIT 1
    """, (f'%{loan_number}%',))
    
    first_call = cursor.fetchone()
    if not first_call:
        print("No calls found for this loan!")
        return
    
    print(f"\n📍 FIRST MENTION:")
    print(f"   Date: {first_call['timestamp']}")
    print(f"   Local: {first_call['localParty']}")
    print(f"   Remote: {first_call['remoteParty']}")
    print(f"   Call ID: {first_call['orkuid']}")
    
    # Key players to track
    primary_party = first_call['localParty']
    secondary_party = first_call['remoteParty']
    
    # Step 2: Find LAST mention
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            ct.transcript_path
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp DESC
        LIMIT 1
    """, (f'%{loan_number}%',))
    
    last_call = cursor.fetchone()
    
    print(f"\n🏁 LAST MENTION:")
    print(f"   Date: {last_call['timestamp']}")
    print(f"   Local: {last_call['localParty']}")
    print(f"   Remote: {last_call['remoteParty']}")
    print(f"   Call ID: {last_call['orkuid']}")
    
    # Calculate journey duration
    journey_days = (last_call['timestamp'] - first_call['timestamp']).days
    print(f"\n⏱️  JOURNEY DURATION: {journey_days} days")
    
    # Step 3: Track ALL calls in the journey window (with 2-day buffer)
    start_date = first_call['timestamp'] - timedelta(days=2)
    end_date = last_call['timestamp'] + timedelta(days=2)
    
    print(f"\n🔍 TRACKING WINDOW: {start_date.date()} to {end_date.date()}")
    
    # Get all calls involving key parties or processor assistants
    cursor.execute("""
        SELECT 
            t.orkUid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.loan_numbers,
            CASE 
                WHEN ct.loan_numbers LIKE %s THEN 'DIRECT'
                WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 'PROCESSOR'
                ELSE 'NETWORK'
            END as call_type
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        WHERE t.timestamp BETWEEN %s AND %s
        AND (
            t.localParty = %s OR t.remoteParty = %s
            OR t.localParty = %s OR t.remoteParty = %s
            OR t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%'
        )
        ORDER BY t.timestamp
    """, (f'%{loan_number}%', start_date, end_date, 
          primary_party, primary_party, secondary_party, secondary_party))
    
    calls = cursor.fetchall()
    
    print(f"\n📊 CALL BREAKDOWN:")
    direct_calls = [c for c in calls if c['call_type'] == 'DIRECT']
    processor_calls = [c for c in calls if c['call_type'] == 'PROCESSOR']
    network_calls = [c for c in calls if c['call_type'] == 'NETWORK']
    
    print(f"   Direct mentions: {len(direct_calls)}")
    print(f"   Processor calls: {len(processor_calls)}")
    print(f"   Network calls: {len(network_calls)}")
    print(f"   TOTAL: {len(calls)}")
    
    # Step 4: Create journey timeline
    print(f"\n🚀 JOURNEY TIMELINE:")
    print("-" * 80)
    print(f"{'Date':<12} {'Time':<8} {'Type':<10} {'From':<15} {'To':<15} {'Loan?':<6}")
    print("-" * 80)
    
    transcript_paths = []
    
    for call in calls:
        date_str = call['timestamp'].strftime('%m/%d/%Y')
        time_str = call['timestamp'].strftime('%I:%M %p')
        
        # Check if this specific call mentions the loan
        has_loan = False
        if call.get('loan_numbers'):
            try:
                loans = json.loads(call['loan_numbers'])
                has_loan = loan_number in loans
            except:
                pass
        
        # Mark processor assistant calls
        if call['localParty'].startswith('19472421') or call['remoteParty'].startswith('19472421'):
            call_type = "PROCESSOR"
        elif has_loan:
            call_type = "DIRECT"
        else:
            call_type = "network"
        
        loan_marker = "✓" if has_loan else ""
        
        print(f"{date_str:<12} {time_str:<8} {call_type:<10} {call['localParty']:<15} {call['remoteParty']:<15} {loan_marker:<6}")
        
        # Collect transcript paths
        if call.get('transcript_path'):
            transcript_paths.append({
                'timestamp': call['timestamp'],
                'path': call['transcript_path'],
                'has_loan': has_loan,
                'call_type': call_type
            })
    
    # Step 5: Create combined transcript file
    output_file = f"loan_{loan_number}_journey.txt"
    print(f"\n📝 CREATING COMBINED TRANSCRIPT: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"LOAN {loan_number} JOURNEY TRANSCRIPT\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Journey: {first_call['timestamp']} to {last_call['timestamp']} ({journey_days} days)\n")
        f.write(f"Total Calls: {len(calls)}\n")
        f.write("=" * 80 + "\n\n")
        
        for tp in transcript_paths:
            f.write(f"\n{'='*80}\n")
            f.write(f"CALL DATE: {tp['timestamp']}\n")
            f.write(f"TYPE: {tp['call_type']}\n")
            f.write(f"HAS LOAN: {'YES' if tp['has_loan'] else 'NO'}\n")
            f.write(f"PATH: {tp['path']}\n")
            f.write(f"{'='*80}\n\n")
            
            # Here you would read the actual transcript if available
            f.write("[Transcript content would go here]\n\n")
    
    print(f"✅ Journey transcript saved to: {output_file}")
    
    # Step 6: Key insights
    print(f"\n💡 KEY INSIGHTS:")
    
    # Find processor assistant involvement
    processor_numbers = set()
    for call in calls:
        for party in [call['localParty'], call['remoteParty']]:
            if party.startswith('19472421'):
                processor_numbers.add(party)
    
    if processor_numbers:
        print(f"   Processor Assistants involved: {', '.join(sorted(processor_numbers))}")
    
    # Most active parties
    party_counts = {}
    for call in calls:
        for party in [call['localParty'], call['remoteParty']]:
            party_counts[party] = party_counts.get(party, 0) + 1
    
    top_parties = sorted(party_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\n   Most Active Numbers:")
    for party, count in top_parties:
        print(f"     {party}: {count} calls")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Track our favorite loan
    loan_number = "1225237672"
    
    print("🏦 LOAN JOURNEY TRACKER")
    print("Following the bouncing ball from submission to CTC")
    
    track_loan_journey(loan_number)