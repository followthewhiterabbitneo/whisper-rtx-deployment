#!/usr/bin/env python3
"""
MCP Server for Oreka - Remote/Dev Server Version
Can handle SSH tunnel or direct connection
"""

import json
import sys
import os
from datetime import datetime, timedelta
import pymysql

class OrekaMCPServer:
    def __init__(self):
        # Check environment for DB config
        self.db_config = {
            'host': os.getenv('OREKA_DB_HOST', 'localhost'),
            'user': os.getenv('OREKA_DB_USER', 'root'),
            'password': os.getenv('OREKA_DB_PASS', 'admin'),
            'database': os.getenv('OREKA_DB_NAME', 'oreka'),
            'port': int(os.getenv('OREKA_DB_PORT', '3306'))
        }
        
        # Log config (to stderr so it doesn't interfere with stdout)
        sys.stderr.write(f"MCP Server starting...\n")
        sys.stderr.write(f"DB Host: {self.db_config['host']}:{self.db_config['port']}\n")
        sys.stderr.write(f"DB Name: {self.db_config['database']}\n")
        sys.stderr.flush()
    
    def handle_request(self, request):
        """Main request handler"""
        method = request.get('method')
        
        if method == 'list_tools':
            return {
                'tools': [
                    {
                        'name': 'get_recent_calls',
                        'description': 'Get recordings from the last N hours',
                        'parameters': {
                            'hours': {
                                'type': 'integer',
                                'description': 'Number of hours to look back',
                                'default': 24
                            }
                        }
                    },
                    {
                        'name': 'search_calls',
                        'description': 'Search recordings by various criteria',
                        'parameters': {
                            'date_from': {
                                'type': 'string',
                                'description': 'Start date (YYYY-MM-DD)'
                            },
                            'date_to': {
                                'type': 'string',
                                'description': 'End date (YYYY-MM-DD)'
                            },
                            'party': {
                                'type': 'string',
                                'description': 'Phone number or extension'
                            },
                            'min_duration': {
                                'type': 'integer',
                                'description': 'Minimum duration in seconds'
                            }
                        }
                    },
                    {
                        'name': 'get_call_details',
                        'description': 'Get detailed info about a specific call',
                        'parameters': {
                            'orkuid': {
                                'type': 'string',
                                'description': 'The recording ID',
                                'required': True
                            }
                        }
                    }
                ]
            }
        
        elif method == 'call_tool':
            tool_name = request.get('params', {}).get('name')
            args = request.get('params', {}).get('arguments', {})
            
            if tool_name == 'get_recent_calls':
                return self.get_recent_calls(args.get('hours', 24))
            elif tool_name == 'search_calls':
                return self.search_calls(**args)
            elif tool_name == 'get_call_details':
                return self.get_call_details(args.get('orkuid'))
        
        return {'error': f'Unknown method: {method}'}
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return pymysql.connect(**self.db_config)
        except Exception as e:
            sys.stderr.write(f"DB Connection Error: {str(e)}\n")
            sys.stderr.flush()
            raise
    
    def get_recent_calls(self, hours=24):
        """Get recent recordings"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT orkuid, timestamp, duration, 
                       localparty, remoteparty, filename
                FROM recording
                WHERE timestamp >= NOW() - INTERVAL %s HOUR
                ORDER BY timestamp DESC
                LIMIT 20
            """
            
            cursor.execute(query, (hours,))
            results = cursor.fetchall()
            
            formatted = []
            for rec in results:
                formatted.append({
                    'id': rec['orkuid'],
                    'time': rec['timestamp'].isoformat() if rec['timestamp'] else None,
                    'duration_seconds': rec['duration'],
                    'duration_formatted': f"{rec['duration']//60}:{rec['duration']%60:02d}" if rec['duration'] else "0:00",
                    'from': rec['remoteparty'],
                    'to': rec['localparty'],
                    'filename': rec['filename']
                })
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'success',
                'count': len(formatted),
                'calls': formatted,
                'query_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def search_calls(self, date_from=None, date_to=None, party=None, min_duration=None):
        """Search with multiple criteria"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Build dynamic query
            query = "SELECT orkuid, timestamp, duration, localparty, remoteparty FROM recording WHERE 1=1"
            params = []
            
            if date_from:
                query += " AND timestamp >= %s"
                params.append(date_from)
            
            if date_to:
                query += " AND timestamp <= %s"
                params.append(date_to + " 23:59:59")
            
            if party:
                query += " AND (localparty LIKE %s OR remoteparty LIKE %s)"
                params.extend([f"%{party}%", f"%{party}%"])
            
            if min_duration:
                query += " AND duration >= %s"
                params.append(min_duration)
            
            query += " ORDER BY timestamp DESC LIMIT 50"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
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
                'calls': formatted,
                'search_criteria': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'party': party,
                    'min_duration': min_duration
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_call_details(self, orkuid):
        """Get detailed info about a specific call"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get recording details
            query = """
                SELECT r.*, 
                       (SELECT COUNT(*) FROM recording WHERE localparty = r.localparty) as agent_total_calls,
                       (SELECT COUNT(*) FROM recording WHERE remoteparty = r.remoteparty) as caller_history_count
                FROM recording r
                WHERE orkuid = %s
            """
            
            cursor.execute(query, (orkuid,))
            result = cursor.fetchone()
            
            if not result:
                return {
                    'status': 'error',
                    'error': f'Recording {orkuid} not found'
                }
            
            # Format the response
            details = {
                'id': result['orkuid'],
                'timestamp': result['timestamp'].isoformat() if result['timestamp'] else None,
                'duration': result['duration'],
                'local_party': result['localparty'],
                'remote_party': result['remoteparty'],
                'filename': result['filename'],
                'file_path': result['path'] if 'path' in result else None,
                'agent_stats': {
                    'total_calls': result['agent_total_calls']
                },
                'caller_stats': {
                    'previous_calls': result['caller_history_count'] - 1
                }
            }
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'success',
                'call': details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run(self):
        """Main loop - read JSON from stdin, write JSON to stdout"""
        sys.stderr.write("MCP Server ready. Waiting for requests...\n")
        sys.stderr.flush()
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Log request to stderr
                sys.stderr.write(f"Request: {line.strip()}\n")
                sys.stderr.flush()
                
                request = json.loads(line)
                response = self.handle_request(request)
                
                # Write response
                output = json.dumps(response) + '\n'
                sys.stdout.write(output)
                sys.stdout.flush()
                
                # Log response size to stderr
                sys.stderr.write(f"Response sent: {len(output)} bytes\n")
                sys.stderr.flush()
                
            except json.JSONDecodeError as e:
                error_response = {'error': f'Invalid JSON: {str(e)}'}
                sys.stdout.write(json.dumps(error_response) + '\n')
                sys.stdout.flush()
            except Exception as e:
                error_response = {'error': f'Server error: {str(e)}'}
                sys.stdout.write(json.dumps(error_response) + '\n')
                sys.stdout.flush()
                sys.stderr.write(f"Error: {str(e)}\n")
                sys.stderr.flush()

if __name__ == '__main__':
    server = OrekaMCPServer()
    server.run()