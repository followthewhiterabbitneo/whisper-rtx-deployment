#!/usr/bin/env python3
"""
Loan Officer Performance Dashboard
Shows key metrics for each loan officer
"""

import pymysql
import json
from datetime import datetime, timedelta
from collections import defaultdict

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def generate_dashboard():
    """Generate loan officer performance metrics"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    print("="*80)
    print("LOAN OFFICER PERFORMANCE DASHBOARD")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. Get all loan officers with significant activity
    cursor.execute("""
        SELECT 
            t.remoteParty as phone_number,
            COUNT(DISTINCT ct.orkuid) as total_calls,
            COUNT(DISTINCT ct.loan_numbers) as unique_loan_sets,
            SUM(t.duration) as total_duration,
            MIN(t.timestamp) as first_call,
            MAX(t.timestamp) as last_call
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        GROUP BY t.remoteParty
        HAVING total_calls >= 10
        ORDER BY total_calls DESC
    """)
    
    officers = cursor.fetchall()
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Active loan officers: {len(officers)}")
    
    # 2. Detailed metrics for each officer
    print(f"\n👥 TOP LOAN OFFICERS:\n")
    
    for idx, officer in enumerate(officers[:10], 1):
        print(f"{idx}. Phone: {officer['phone_number']}")
        print(f"   📞 Total calls: {officer['total_calls']}")
        print(f"   ⏱️  Total time: {officer['total_duration']/60:.1f} minutes")
        print(f"   📅 Active period: {officer['first_call'].date()} to {officer['last_call'].date()}")
        
        # Get unique loans for this officer
        cursor.execute("""
            SELECT ct.loan_numbers
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            WHERE t.remoteParty = %s
            AND ct.loan_numbers != '[]'
        """, (officer['phone_number'],))
        
        all_loans = set()
        for row in cursor.fetchall():
            loans = json.loads(row['loan_numbers'])
            all_loans.update(loans)
        
        print(f"   💰 Unique loans handled: {len(all_loans)}")
        print(f"   📈 Avg calls per loan: {officer['total_calls']/len(all_loans):.1f}")
        
        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) as recent_calls
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            WHERE t.remoteParty = %s
            AND ct.loan_numbers != '[]'
            AND t.timestamp >= %s
        """, (officer['phone_number'], datetime.now() - timedelta(days=7)))
        
        recent = cursor.fetchone()['recent_calls']
        print(f"   🔥 Last 7 days: {recent} calls")
        
        # Customer reach
        cursor.execute("""
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN t.remoteParty = %s THEN t.localParty 
                    ELSE t.remoteParty 
                END
            ) as unique_customers
            FROM orktape t
            JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            WHERE (t.remoteParty = %s OR t.localParty = %s)
            AND ct.loan_numbers != '[]'
        """, (officer['phone_number'], officer['phone_number'], officer['phone_number']))
        
        customers = cursor.fetchone()['unique_customers']
        print(f"   👤 Unique customers: {customers}")
        print()
    
    # 3. Trending analysis
    print("\n📈 TRENDING (Last 30 days):")
    
    cursor.execute("""
        SELECT 
            DATE(t.timestamp) as call_date,
            COUNT(DISTINCT ct.orkuid) as calls,
            COUNT(DISTINCT t.remoteParty) as active_officers
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(t.timestamp)
        ORDER BY call_date DESC
        LIMIT 7
    """)
    
    print("\n   Last 7 days:")
    for row in cursor.fetchall():
        print(f"   {row['call_date']}: {row['calls']} loan calls by {row['active_officers']} officers")
    
    # 4. Efficiency metrics
    print("\n⚡ EFFICIENCY METRICS:")
    
    # Average call duration by officer
    cursor.execute("""
        SELECT 
            t.remoteParty as phone_number,
            AVG(t.duration) as avg_duration,
            COUNT(*) as call_count
        FROM orktape t
        JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        WHERE ct.loan_numbers != '[]'
        GROUP BY t.remoteParty
        HAVING call_count >= 20
        ORDER BY avg_duration ASC
        LIMIT 5
    """)
    
    print("\n   Most efficient (shortest avg calls):")
    for row in cursor.fetchall():
        print(f"   {row['phone_number']}: {row['avg_duration']:.0f}s avg ({row['call_count']} calls)")
    
    cursor.close()
    conn.close()
    
    print("\n\n✅ Dashboard complete!")

if __name__ == "__main__":
    generate_dashboard()