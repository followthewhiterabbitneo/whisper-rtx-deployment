#!/usr/bin/env python3
"""
Count recordings for a team of 2 people
From June 28 back to June 1, 2024
"""

import pymysql
from datetime import datetime, timedelta

# Database configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka'
}

def count_recordings_for_team(user_ids, start_date, end_date):
    """Count recordings for a team of users in date range"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Build user condition
    user_condition = " OR ".join([f"s.user_id = {uid}" for uid in user_ids])
    
    query = f"""
    SELECT 
        DATE(t.timestamp) as recording_date,
        COUNT(DISTINCT t.orkUid) as recordings,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NOT NULL THEN t.orkUid END) as transcribed,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NULL THEN t.orkUid END) as untranscribed,
        SUM(t.duration) as total_duration_seconds,
        GROUP_CONCAT(DISTINCT u.firstname, ' ', u.lastname) as users
    FROM orktape t
    JOIN orksegment s ON t.id = s.tape_id
    JOIN orkuser u ON s.user_id = u.id
    LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
    WHERE ({user_condition})
    AND t.timestamp >= %s
    AND t.timestamp < %s
    AND t.duration >= 30  -- At least 30 seconds
    GROUP BY DATE(t.timestamp)
    ORDER BY recording_date DESC
    """
    
    cursor.execute(query, (start_date, end_date))
    daily_counts = cursor.fetchall()
    
    # Get total summary
    summary_query = f"""
    SELECT 
        COUNT(DISTINCT t.orkUid) as total_recordings,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NOT NULL THEN t.orkUid END) as total_transcribed,
        COUNT(DISTINCT CASE WHEN ct.transcript_path IS NULL THEN t.orkUid END) as total_untranscribed,
        SUM(t.duration) as total_duration_seconds,
        MIN(t.timestamp) as earliest,
        MAX(t.timestamp) as latest
    FROM orktape t
    JOIN orksegment s ON t.id = s.tape_id
    LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
    WHERE ({user_condition})
    AND t.timestamp >= %s
    AND t.timestamp < %s
    AND t.duration >= 30
    """
    
    cursor.execute(summary_query, (start_date, end_date))
    summary = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return daily_counts, summary

def get_user_by_name(first_name, last_name=None):
    """Find user ID by name"""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    if last_name:
        cursor.execute("""
            SELECT id, firstname, lastname, name 
            FROM orkuser 
            WHERE firstname LIKE %s AND lastname LIKE %s
        """, (f'%{first_name}%', f'%{last_name}%'))
    else:
        cursor.execute("""
            SELECT id, firstname, lastname, name 
            FROM orkuser 
            WHERE firstname LIKE %s OR lastname LIKE %s OR name LIKE %s
        """, (f'%{first_name}%', f'%{first_name}%', f'%{first_name}%'))
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return users

def main():
    print("🎯 TEAM RECORDING COUNT - JUNE 2024")
    print("="*60)
    
    # Date range: June 1-28, 2024
    start_date = datetime(2024, 6, 1)
    end_date = datetime(2024, 6, 29)  # 29th to include all of 28th
    
    print(f"Date Range: {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}")
    print()
    
    # Get team members
    print("Enter team member names (2 people):")
    
    team_ids = []
    for i in range(2):
        while True:
            name = input(f"Team member {i+1} name (first last): ").strip()
            if not name:
                print("Please enter a name")
                continue
                
            parts = name.split()
            if len(parts) == 2:
                users = get_user_by_name(parts[0], parts[1])
            else:
                users = get_user_by_name(name)
            
            if not users:
                print(f"No user found for '{name}'")
                continue
            elif len(users) == 1:
                user = users[0]
                team_ids.append(user['id'])
                print(f"✓ Found: {user['firstname']} {user['lastname']} (ID: {user['id']})")
                break
            else:
                print(f"Multiple users found for '{name}':")
                for idx, u in enumerate(users):
                    print(f"  {idx+1}. {u['firstname']} {u['lastname']} - {u['name']}")
                choice = input("Select number: ")
                try:
                    user = users[int(choice)-1]
                    team_ids.append(user['id'])
                    print(f"✓ Selected: {user['firstname']} {user['lastname']}")
                    break
                except:
                    print("Invalid selection")
    
    print(f"\n📊 Counting recordings for user IDs: {team_ids}")
    print("="*60)
    
    # Get counts
    daily_counts, summary = count_recordings_for_team(team_ids, start_date, end_date)
    
    # Display daily breakdown
    print("\nDAILY BREAKDOWN (June 28 → June 1):")
    print("-"*60)
    print("Date       | Total | Transcribed | Untranscribed | Duration")
    print("-"*60)
    
    for day in daily_counts:
        duration_mins = day['total_duration_seconds'] / 60
        print(f"{day['recording_date']} | {day['recordings']:5d} | {day['transcribed']:11d} | {day['untranscribed']:13d} | {duration_mins:6.0f} min")
    
    # Display summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print(f"Total Recordings: {summary['total_recordings']:,}")
    print(f"Already Transcribed: {summary['total_transcribed']:,}")
    print(f"Need Transcription: {summary['total_untranscribed']:,}")
    print(f"Total Duration: {summary['total_duration_seconds']/3600:.1f} hours")
    print(f"Date Range: {summary['earliest']} to {summary['latest']}")
    
    # Estimate processing time
    if summary['total_untranscribed'] > 0:
        # Assuming 10x real-time speed on RTX 4090
        est_hours = (summary['total_duration_seconds'] / 3600) / 10
        print(f"\n⏱️  Estimated transcription time on RTX 4090: {est_hours:.1f} hours")
        print(f"   (at 10x real-time speed)")

if __name__ == "__main__":
    main()