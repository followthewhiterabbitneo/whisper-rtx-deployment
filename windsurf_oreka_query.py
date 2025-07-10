#!/usr/bin/env python3
"""
Direct Oreka Query Tool for Windsurf
No MCP needed - just run this directly on your work laptop!
"""

import pymysql
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict

class OrekaQuery:
    def __init__(self, host='dev-server-hostname', user='root', password='admin', database='oreka'):
        """Initialize connection to Oreka database"""
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': 3306
        }
    
    def get_recent_calls(self, hours: int = 24) -> List[Dict]:
        """Get calls from the last N hours"""
        conn = pymysql.connect(**self.connection_params)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT orkuid, timestamp, duration, localparty, remoteparty, filename
                    FROM recording
                    WHERE timestamp >= NOW() - INTERVAL %s HOUR
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                cursor.execute(query, (hours,))
                return cursor.fetchall()
        finally:
            conn.close()
    
    def search_by_party(self, phone_number: str) -> List[Dict]:
        """Search calls by phone number (partial match)"""
        conn = pymysql.connect(**self.connection_params)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT orkuid, timestamp, duration, localparty, remoteparty
                    FROM recording
                    WHERE localparty LIKE %s OR remoteparty LIKE %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                search_term = f"%{phone_number}%"
                cursor.execute(query, (search_term, search_term))
                return cursor.fetchall()
        finally:
            conn.close()
    
    def get_call_details(self, orkuid: str) -> Dict:
        """Get full details for a specific call"""
        conn = pymysql.connect(**self.connection_params)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Main recording info
                cursor.execute("SELECT * FROM recording WHERE orkuid = %s", (orkuid,))
                recording = cursor.fetchone()
                
                if not recording:
                    return {'error': f'Recording {orkuid} not found'}
                
                # Get related info
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM recording 
                    WHERE remoteparty = %s
                """, (recording['remoteparty'],))
                caller_history = cursor.fetchone()
                
                recording['caller_history_count'] = caller_history['count']
                return recording
        finally:
            conn.close()
    
    def get_agent_stats(self, agent_extension: str, days: int = 7) -> Dict:
        """Get statistics for a specific agent"""
        conn = pymysql.connect(**self.connection_params)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT 
                        COUNT(*) as total_calls,
                        AVG(duration) as avg_duration,
                        MAX(duration) as max_duration,
                        MIN(duration) as min_duration,
                        SUM(duration) as total_duration
                    FROM recording
                    WHERE localparty = %s
                    AND timestamp >= NOW() - INTERVAL %s DAY
                """
                cursor.execute(query, (agent_extension, days))
                return cursor.fetchone()
        finally:
            conn.close()
    
    def find_long_calls(self, min_minutes: int = 30) -> List[Dict]:
        """Find calls longer than specified minutes"""
        conn = pymysql.connect(**self.connection_params)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT orkuid, timestamp, duration, localparty, remoteparty,
                           ROUND(duration/60.0, 1) as duration_minutes
                    FROM recording
                    WHERE duration >= %s
                    ORDER BY duration DESC
                    LIMIT 50
                """
                cursor.execute(query, (min_minutes * 60,))
                return cursor.fetchall()
        finally:
            conn.close()

# Example usage - just run these in Windsurf!
if __name__ == "__main__":
    # Initialize connection (update with your DEV server details)
    oreka = OrekaQuery(host='your-dev-server')
    
    print("=== Recent Calls (Last 24 Hours) ===")
    recent = oreka.get_recent_calls(24)
    for call in recent[:5]:  # Show first 5
        print(f"{call['timestamp']} - {call['remoteparty']} -> {call['localparty']} ({call['duration']}s)")
    
    print(f"\nTotal recent calls: {len(recent)}")
    
    # Example: Find specific caller
    # calls = oreka.search_by_party("555-1234")
    
    # Example: Get agent stats
    # stats = oreka.get_agent_stats("8001", days=30)