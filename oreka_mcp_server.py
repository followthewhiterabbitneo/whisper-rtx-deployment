#!/usr/bin/env python3
"""
First Principles MCP Server for Oreka
Just ONE tool: get recent calls
"""

import json
import sys
from datetime import datetime, timedelta
import pymysql

class OrekaMCPServer:
    def __init__(self):
        # Your DB connection
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'admin',
            'database': 'oreka',
            'port': 3306
        }
    
    def handle_request(self, request):
        """Main request handler - reads JSON from stdin"""
        if request.get('method') == 'list_tools':
            # Tell Claude what tools we have
            return {
                'tools': [{
                    'name': 'get_recent_calls',
                    'description': 'Get recordings from the last N hours',
                    'parameters': {
                        'hours': {
                            'type': 'integer',
                            'description': 'Number of hours to look back',
                            'default': 24
                        }
                    }
                }]
            }
        
        elif request.get('method') == 'call_tool':
            tool_name = request.get('params', {}).get('name')
            args = request.get('params', {}).get('arguments', {})
            
            if tool_name == 'get_recent_calls':
                return self.get_recent_calls(args.get('hours', 24))
        
        return {'error': 'Unknown method'}
    
    def get_recent_calls(self, hours=24):
        """Actually query the database"""
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Simple query - just get recent recordings
            query = """
                SELECT orkuid, timestamp, duration, localparty, remoteparty
                FROM recording
                WHERE timestamp >= NOW() - INTERVAL %s HOUR
                ORDER BY timestamp DESC
                LIMIT 10
            """
            
            cursor.execute(query, (hours,))
            results = cursor.fetchall()
            
            # Format for Claude
            formatted = []
            for rec in results:
                formatted.append({
                    'id': rec['orkuid'],
                    'time': rec['timestamp'].isoformat() if rec['timestamp'] else None,
                    'duration': rec['duration'],
                    'from': rec['remoteparty'],
                    'to': rec['localparty']
                })
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'success',
                'count': len(formatted),
                'calls': formatted
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run(self):
        """Main loop - read JSON from stdin, write JSON to stdout"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = self.handle_request(request)
                
                # Write response
                sys.stdout.write(json.dumps(response) + '\n')
                sys.stdout.flush()
                
            except Exception as e:
                error_response = {'error': str(e)}
                sys.stdout.write(json.dumps(error_response) + '\n')
                sys.stdout.flush()

if __name__ == '__main__':
    server = OrekaMCPServer()
    server.run()