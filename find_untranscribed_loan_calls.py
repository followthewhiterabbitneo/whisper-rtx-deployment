#!/usr/bin/env python3
"""
Find loan-related calls that haven't been transcribed yet
Prioritizes by loan officer activity and call duration
"""

import pymysql
import json
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def find_untranscribed_calls():
    """Find calls that need transcription, prioritized by importance"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("FINDING UNTRANSCRIBED LOAN-RELATED CALLS")
    print("="*80)
    
    # 1. First, identify top loan officers
    print("\n1. Identifying top loan officers...")
    cursor.execute("""
        SELECT 
            t.remoteParty as phone_number,
            COUNT(DISTINCT ct.orkuid) as transcribed_calls,
            COUNT(DISTINCT JSON_UNQUOTE(JSON_EXTRACT(ct.loan_numbers, '$[0]'))) as unique_loans
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        GROUP BY t.remoteParty
        HAVING transcribed_calls >= 5
        ORDER BY unique_loans DESC
        LIMIT 10
    """)
    
    loan_officers = [row['phone_number'] for row in cursor.fetchall()]
    print(f"   Found {len(loan_officers)} active loan officers")
    
    # 2. Find untranscribed calls from these loan officers
    print("\n2. Finding untranscribed calls from loan officers...")
    
    placeholders = ','.join(['%s'] * len(loan_officers))
    cursor.execute(f"""
        SELECT 
            t.orkUid,
            t.filename,
            t.duration,
            t.timestamp,
            t.localParty,
            t.remoteParty,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM orktape t
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        WHERE ct.orkuid IS NULL  -- Not transcribed
        AND (t.remoteParty IN ({placeholders}) OR t.localParty IN ({placeholders}))
        AND t.duration >= 30  -- At least 30 seconds
        AND t.timestamp >= %s  -- Last 30 days
        ORDER BY t.duration DESC, t.timestamp DESC
        LIMIT 100
    """, loan_officers + loan_officers + [datetime.now() - timedelta(days=30)])
    
    untranscribed = cursor.fetchall()
    
    print(f"\n📊 UNTRANSCRIBED CALLS SUMMARY:")
    print(f"   Total found: {len(untranscribed)}")
    
    if untranscribed:
        total_duration = sum(call['duration'] for call in untranscribed)
        print(f"   Total duration: {total_duration/60:.1f} minutes")
        print(f"   Average duration: {total_duration/len(untranscribed):.1f} seconds")
    
    # 3. Group by loan officer
    print("\n3. Breakdown by loan officer:")
    officer_calls = {}
    for call in untranscribed:
        for officer in loan_officers:
            if officer in [call['localParty'], call['remoteParty']]:
                if officer not in officer_calls:
                    officer_calls[officer] = []
                officer_calls[officer].append(call)
                break
    
    for officer, calls in sorted(officer_calls.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        total_duration = sum(c['duration'] for c in calls)
        print(f"\n   📞 {officer}:")
        print(f"      Untranscribed calls: {len(calls)}")
        print(f"      Total duration: {total_duration/60:.1f} minutes")
        print(f"      Priority calls (>2 min): {sum(1 for c in calls if c['duration'] > 120)}")
    
    # 4. Export high-priority calls
    high_priority = [c for c in untranscribed if c['duration'] > 120]  # Over 2 minutes
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_untranscribed': len(untranscribed),
        'high_priority_count': len(high_priority),
        'loan_officers': loan_officers,
        'high_priority_calls': []
    }
    
    for call in high_priority[:20]:  # Top 20
        output['high_priority_calls'].append({
            'orkuid': call['orkUid'],
            'filename': call['filename'],
            'duration': call['duration'],
            'timestamp': call['timestamp'].isoformat() if call['timestamp'] else None,
            'parties': f"{call['localParty']} ↔ {call['remoteParty']}",
            'user': call['user_name']
        })
    
    # Save to file
    with open('untranscribed_loan_calls.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\n✅ Saved {len(high_priority)} high-priority calls to untranscribed_loan_calls.json")
    print(f"\n🎯 RECOMMENDED NEXT STEPS:")
    print(f"   1. Transcribe the {len(high_priority)} high-priority calls (>2 min)")
    print(f"   2. Focus on top loan officers first")
    print(f"   3. Use process_loan_networks.py to batch process")
    
    cursor.close()
    conn.close()
    
    return len(untranscribed)

if __name__ == "__main__":
    count = find_untranscribed_calls()
    print(f"\n📈 Total untranscribed loan-related calls: {count}")