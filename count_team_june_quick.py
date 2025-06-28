#!/usr/bin/env python3
"""
Quick count for specific team - June 28 back to June 1
Modify the team_names list with your 2 people
"""

import pymysql
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka'
}

# MODIFY THIS WITH YOUR TEAM OF 2
team_names = [
    "Eric Rawlins",      # Team member 1
    "Jonathan Boatright" # Team member 2
]

def count_team_recordings():
    """Count recordings for the team in June"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # First, find the user IDs
    print("🔍 Finding team members...")
    team_ids = []
    
    for name in team_names:
        parts = name.split()
        cursor.execute("""
            SELECT id, firstname, lastname 
            FROM orkuser 
            WHERE firstname = %s AND lastname = %s
        """, (parts[0], parts[1] if len(parts) > 1 else ''))
        
        user = cursor.fetchone()
        if user:
            team_ids.append(user['id'])
            print(f"✓ Found: {user['firstname']} {user['lastname']} (ID: {user['id']})")
        else:
            print(f"❌ Not found: {name}")
    
    if len(team_ids) != 2:
        print("\n⚠️  Could not find both team members!")
        return
    
    # Count recordings from June 28 back to June 1
    print(f"\n📊 Counting recordings for June 2024...")
    
    query = """
    SELECT 
        DATE(t.timestamp) as date,
        COUNT(DISTINCT t.orkUid) as total_calls,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NOT NULL THEN t.orkUid END) as transcribed,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NULL THEN t.orkUid END) as untranscribed,
        SUM(t.duration)/60 as total_minutes
    FROM orktape t
    JOIN orksegment s ON t.id = s.tape_id
    LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
    WHERE s.user_id IN (%s, %s)
    AND t.timestamp >= '2024-06-01'
    AND t.timestamp < '2024-06-29'
    AND t.duration >= 30
    GROUP BY DATE(t.timestamp)
    ORDER BY date DESC
    """
    
    cursor.execute(query, tuple(team_ids))
    daily = cursor.fetchall()
    
    # Get totals
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT t.orkUid) as total,
            COUNT(DISTINCT CASE WHEN ct.transcript_path IS NULL THEN t.orkUid END) as need_transcription,
            SUM(t.duration)/3600 as total_hours
        FROM orktape t
        JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        WHERE s.user_id IN (%s, %s)
        AND t.timestamp >= '2024-06-01'
        AND t.timestamp < '2024-06-29'
        AND t.duration >= 30
    """, tuple(team_ids))
    
    totals = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # Display results
    print("\n" + "="*70)
    print(f"TEAM: {' & '.join(team_names)}")
    print("="*70)
    print("\nDAILY BREAKDOWN (June 28 → June 1):")
    print("-"*70)
    print("Date       | Total | Transcribed | Need Trans | Minutes")
    print("-"*70)
    
    for day in daily:
        print(f"{day['date']} |  {day['total_calls']:4d} | {day['transcribed']:11d} | {day['untranscribed']:10d} | {day['total_minutes']:7.0f}")
    
    print("\n" + "="*70)
    print("JUNE TOTALS:")
    print("="*70)
    print(f"Total Recordings: {totals['total']:,}")
    print(f"Need Transcription: {totals['need_transcription']:,}")
    print(f"Total Duration: {totals['total_hours']:.1f} hours")
    
    if totals['need_transcription'] > 0:
        est_time = totals['total_hours'] / 10  # 10x speed
        print(f"\n⏱️  Estimated RTX 4090 time: {est_time:.1f} hours (at 10x speed)")
        print(f"   That's about {est_time*60:.0f} minutes")

if __name__ == "__main__":
    count_team_recordings()