#!/usr/bin/env python3
"""
CHECK CALL DIRECTION
Analyze the direction field values (0, 1, 3 - skipping 2)
Help determine which channel is which party
"""

import pymysql

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def check_directions():
    """Check direction patterns in the database"""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("🔍 Analyzing call directions...")
    print("=" * 60)
    
    # Get sample calls with different directions
    cursor.execute("""
        SELECT 
            direction,
            COUNT(*) as count,
            localParty,
            remoteParty,
            orkUid
        FROM orktape
        WHERE direction IN (0, 1, 3)
        GROUP BY direction
        ORDER BY direction
    """)
    
    direction_counts = cursor.fetchall()
    
    print("\nDirection Value Counts:")
    for row in direction_counts:
        print(f"  Direction {row['direction']}: {row['count']} calls")
    
    # Get examples of each direction
    print("\n" + "=" * 60)
    print("SAMPLE CALLS BY DIRECTION:")
    print("=" * 60)
    
    for direction in [0, 1, 3]:
        print(f"\n📞 Direction = {direction}:")
        cursor.execute("""
            SELECT 
                localParty,
                remoteParty,
                filename,
                timestamp
            FROM orktape
            WHERE direction = %s
            AND localParty LIKE '19472421%%'
            ORDER BY timestamp DESC
            LIMIT 3
        """, (direction,))
        
        samples = cursor.fetchall()
        for s in samples:
            print(f"  Local: {s['localParty']} → Remote: {s['remoteParty']}")
    
    # Check if direction correlates with party positions
    print("\n" + "=" * 60)
    print("DIRECTION PATTERNS:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            direction,
            CASE 
                WHEN localParty LIKE '19472421%%' THEN 'UWM_IS_LOCAL'
                WHEN remoteParty LIKE '19472421%%' THEN 'UWM_IS_REMOTE'
                ELSE 'OTHER'
            END as uwm_position,
            COUNT(*) as count
        FROM orktape
        WHERE direction IN (0, 1, 3)
        AND (localParty LIKE '19472421%%' OR remoteParty LIKE '19472421%%')
        GROUP BY direction, uwm_position
        ORDER BY direction, uwm_position
    """)
    
    patterns = cursor.fetchall()
    
    current_dir = None
    for p in patterns:
        if p['direction'] != current_dir:
            print(f"\nDirection {p['direction']}:")
            current_dir = p['direction']
        print(f"  {p['uwm_position']}: {p['count']} calls")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("INTERPRETATION:")
    print("Direction 0: Usually INCOMING calls (remote → local)")
    print("Direction 1: Usually OUTGOING calls (local → remote)")  
    print("Direction 3: Special case (transfers, conferences?)")
    print("\nFor screenplay: Left channel = localParty, Right = remoteParty")
    print("=" * 60)

if __name__ == "__main__":
    check_directions()