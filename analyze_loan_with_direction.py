#!/usr/bin/env python3
"""
Enhanced loan analysis with CALL DIRECTION arrows!
Shows who called whom in the network
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

def analyze_loan_with_arrows():
    """Analyze loan with directional arrows"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    loan_number = "1225237672"
    
    print("="*80)
    print(f"LOAN {loan_number} - WITH CALL DIRECTION!")
    print("="*80)
    
    # Get all calls for this loan with direction info
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            t.direction,
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
    
    print(f"\n📞 CALLS WITH DIRECTION ARROWS:\n")
    
    for idx, call in enumerate(calls, 1):
        # Determine arrow based on direction
        if call.get('direction') == 'IN':
            # Incoming call: remote → local
            arrow = "→"
            flow = f"{call['remoteParty']} {arrow} {call['localParty']}"
        elif call.get('direction') == 'OUT':
            # Outgoing call: local → remote  
            arrow = "→"
            flow = f"{call['localParty']} {arrow} {call['remoteParty']}"
        else:
            # Unknown direction
            arrow = "↔"
            flow = f"{call['localParty']} {arrow} {call['remoteParty']}"
        
        print(f"Call {idx}: {call['timestamp']}")
        print(f"  🔀 {flow}")
        print(f"  👤 User: {call['user_name']}")
        print(f"  ⏱️  Duration: {call['duration']}s ({call['duration']/60:.1f} min)")
        
        # Show who initiated
        if call.get('direction') == 'IN':
            print(f"  📲 {call['remoteParty']} called in")
        elif call.get('direction') == 'OUT':
            print(f"  📱 {call['localParty']} called out")
        
        print()
    
    # Fun stats about call patterns
    print("\n📊 CALL PATTERN ANALYSIS:")
    
    incoming = sum(1 for c in calls if c.get('direction') == 'IN')
    outgoing = sum(1 for c in calls if c.get('direction') == 'OUT')
    
    print(f"  📲 Incoming calls: {incoming}")
    print(f"  📱 Outgoing calls: {outgoing}")
    
    if incoming > outgoing:
        print(f"  💡 Customer called in more (eager/anxious?)")
    elif outgoing > incoming:
        print(f"  💡 Loan officer called out more (proactive follow-up?)")
    
    # Who talks more?
    total_duration_by_direction = {
        'IN': sum(c['duration'] for c in calls if c.get('direction') == 'IN'),
        'OUT': sum(c['duration'] for c in calls if c.get('direction') == 'OUT')
    }
    
    print(f"\n  ⏱️  Time on incoming calls: {total_duration_by_direction['IN']/60:.1f} min")
    print(f"  ⏱️  Time on outgoing calls: {total_duration_by_direction['OUT']/60:.1f} min")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_loan_with_arrows()