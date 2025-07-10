#!/usr/bin/env python3
"""
Personal Productivity Enhancement Tool™
Definitely not an unauthorized database query system
"""

import pymysql
import csv
import json
from datetime import datetime, timedelta
import os

class PersonalReporter:
    def __init__(self):
        # Connection details you've "memorized"
        self.db = {
            'host': 'dev-server',  # Update this
            'user': 'root',
            'password': 'admin',
            'database': 'oreka'
        }
        
        # Your "working directory" 
        self.output_dir = os.path.expanduser("~/Documents/CallReports")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_daily_summary(self):
        """Creates a 'manual' daily summary report"""
        conn = pymysql.connect(**self.db)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get today's stats
        today = datetime.now().strftime('%Y-%m-%d')
        
        queries = {
            'total_calls': """
                SELECT COUNT(*) as count 
                FROM recording 
                WHERE DATE(timestamp) = CURDATE()
            """,
            'long_calls': """
                SELECT orkuid, localparty, remoteparty, duration
                FROM recording
                WHERE DATE(timestamp) = CURDATE()
                AND duration > 600
                ORDER BY duration DESC
            """,
            'repeat_callers': """
                SELECT remoteparty, COUNT(*) as call_count
                FROM recording
                WHERE DATE(timestamp) = CURDATE()
                GROUP BY remoteparty
                HAVING call_count > 1
                ORDER BY call_count DESC
            """
        }
        
        # Save as innocent CSV
        output_file = os.path.join(self.output_dir, f"daily_summary_{today}.csv")
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Daily Call Summary', today])
            writer.writerow([])
            
            # Total calls
            cursor.execute(queries['total_calls'])
            total = cursor.fetchone()
            writer.writerow(['Total Calls:', total['count']])
            writer.writerow([])
            
            # Long calls
            writer.writerow(['Long Calls (>10 min):'])
            writer.writerow(['ID', 'From', 'To', 'Duration (min)'])
            cursor.execute(queries['long_calls'])
            for call in cursor.fetchall():
                writer.writerow([
                    call['orkuid'],
                    call['remoteparty'],
                    call['localparty'],
                    round(call['duration']/60, 1)
                ])
        
        cursor.close()
        conn.close()
        
        print(f"Report saved to: {output_file}")
        print("You can now open this in Excel and send it to whoever needs it")
        
        return output_file
    
    def quick_search(self, search_term):
        """'Manual' search that happens to be really fast"""
        conn = pymysql.connect(**self.db)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Search everywhere
        query = """
            SELECT orkuid, timestamp, localparty, remoteparty, duration
            FROM recording
            WHERE (localparty LIKE %s OR remoteparty LIKE %s)
            AND timestamp >= NOW() - INTERVAL 30 DAY
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern))
        results = cursor.fetchall()
        
        # Print results (for Windsurf terminal)
        print(f"\nFound {len(results)} calls matching '{search_term}':\n")
        for r in results[:10]:  # Show first 10
            print(f"{r['timestamp']} | {r['remoteparty']} → {r['localparty']} | {r['duration']}s")
        
        if len(results) > 10:
            print(f"\n... and {len(results)-10} more results")
        
        cursor.close()
        conn.close()
        
        return results
    
    def export_for_excel(self, results, filename="call_data.csv"):
        """Save any results as Excel-friendly CSV"""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        
        print(f"Exported to: {output_path}")
        os.startfile(output_path)  # Opens in Excel on Windows
        
        return output_path

# Usage examples
if __name__ == "__main__":
    reporter = PersonalReporter()
    
    # Generate daily report
    # reporter.generate_daily_summary()
    
    # Quick search
    # results = reporter.quick_search("555")
    
    # Export to Excel
    # reporter.export_for_excel(results, "customer_555_calls.csv")