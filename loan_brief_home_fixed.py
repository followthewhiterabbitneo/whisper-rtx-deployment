#!/usr/bin/env python3
"""
LOAN BRIEF HOME - Fixed for MariaDB 5.5 (no JSON functions)
Simple web interface with clickable links
"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pymysql
import json
import uvicorn

app = FastAPI(title="Loan Brief Home")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

@app.get("/", response_class=HTMLResponse)
def home():
    """Loan Brief Homepage with clickable links"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get recent loans - MariaDB 5.5 compatible
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as mentions,
            MAX(created_at) as last_seen
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY last_seen DESC
        LIMIT 30
    """)
    
    loan_groups = cursor.fetchall()
    
    # Parse loan numbers
    recent_loans = []
    for group in loan_groups:
        try:
            loans = json.loads(group['loan_numbers'])
            for loan in loans:
                recent_loans.append({
                    'loan_number': loan,
                    'mentions': group['mentions'],
                    'last_seen': group['last_seen']
                })
        except:
            pass
    
    # Get top brokers
    cursor.execute("""
        SELECT 
            t.remoteParty as broker,
            COUNT(DISTINCT ct.orkuid) as calls
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers != '[]'
        AND t.remoteParty NOT LIKE '+1555%'
        AND t.remoteParty NOT LIKE '%1947%'
        GROUP BY t.remoteParty
        ORDER BY calls DESC
        LIMIT 10
    """)
    
    top_brokers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Build HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Brief Home</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #1976d2;
                text-align: center;
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .loan-link {
                display: block;
                padding: 10px;
                margin: 5px 0;
                background: #e3f2fd;
                border-radius: 5px;
                text-decoration: none;
                color: #1976d2;
                transition: background 0.3s;
            }
            .loan-link:hover {
                background: #bbdefb;
            }
            .search-box {
                text-align: center;
                margin: 20px 0;
            }
            input[type="text"] {
                padding: 10px;
                width: 300px;
                border: 2px solid #1976d2;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                padding: 10px 20px;
                background: #1976d2;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-left: 10px;
            }
            button:hover {
                background: #1565c0;
            }
            .broker-link {
                display: inline-block;
                padding: 5px 10px;
                margin: 3px;
                background: #f5f5f5;
                border-radius: 3px;
                text-decoration: none;
                color: #333;
                font-size: 14px;
            }
            .broker-link:hover {
                background: #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 Loan Brief Home</h1>
            
            <div class="search-box">
                <input type="text" id="loanSearch" placeholder="Enter loan number..." />
                <button onclick="searchLoan()">Search</button>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h2>📋 Recent Loans</h2>
                    <p>Click any loan to view details:</p>
    """
    
    # Add recent loans (first 20)
    for loan in recent_loans[:20]:
        if loan['loan_number']:
            html += f"""
                    <a href="/loan/{loan['loan_number']}" class="loan-link">
                        <strong>Loan #{loan['loan_number']}</strong><br>
                        <small>{loan['mentions']} calls | Last: {loan['last_seen']}</small>
                    </a>
            """
    
    html += """
                </div>
                
                <div class="card">
                    <h2>📞 Top Brokers</h2>
                    <p>Most active brokers:</p>
    """
    
    # Add brokers
    for broker in top_brokers:
        html += f"""
                    <a href="/broker/{broker['broker']}" class="broker-link">
                        {broker['broker']} ({broker['calls']} calls)
                    </a>
        """
    
    html += """
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h2>🔗 Quick Links</h2>
                <a href="/simple" class="loan-link">📊 Simple Table View</a>
                <a href="/search" class="loan-link">🔍 Advanced Search</a>
            </div>
        </div>
        
        <script>
            function searchLoan() {
                const loanNumber = document.getElementById('loanSearch').value;
                if (loanNumber) {
                    window.location.href = '/loan/' + loanNumber;
                }
            }
            
            // Enter key to search
            document.getElementById('loanSearch').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchLoan();
                }
            });
        </script>
    </body>
    </html>
    """
    
    return html

@app.get("/loan/{loan_number}", response_class=HTMLResponse)
def loan_details(loan_number: str):
    """Show loan details page"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get loan calls
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp DESC
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan #{loan_number}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #1976d2; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #1976d2; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
            .back-link {{ display: inline-block; margin-bottom: 20px; color: #1976d2; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
            .stats {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            <h1>Loan #{loan_number}</h1>
            
            <div class="stats">
                <strong>Summary:</strong><br>
                Total Calls: {len(calls)}<br>
                Total Duration: {sum(c['duration'] for c in calls) / 60:.1f} minutes
            </div>
            
            <table>
                <tr>
                    <th>Date/Time</th>
                    <th>Duration</th>
                    <th>From → To</th>
                    <th>User</th>
                    <th>Call ID</th>
                </tr>
    """
    
    for call in calls:
        html += f"""
                <tr>
                    <td>{call['timestamp']}</td>
                    <td>{call['duration']}s</td>
                    <td>{call['localParty']} → {call['remoteParty']}</td>
                    <td>{call['user_name']}</td>
                    <td>{call['orkuid']}</td>
                </tr>
        """
    
    html += """
            </table>
            
            <div style="margin-top: 20px;">
                <a href="/" class="back-link">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    print("Starting Loan Brief Home...")
    print("Open: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)