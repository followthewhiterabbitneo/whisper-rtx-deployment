#!/usr/bin/env python3
"""
BROKER ACTIVITY TRACKER - Track all broker calls across loans
Click on any phone number to see their full activity
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import pymysql
import json
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Broker Activity Tracker")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Redirect to timeline with clickable phone numbers"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Broker Activity Tracker</title>
        <meta http-equiv="refresh" content="0; url=/loans">
    </head>
    <body>
        <p>Redirecting to loan tracker...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/loans", response_class=HTMLResponse)
async def loan_list():
    """List loans with broker tracking enabled"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as mention_count,
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        HAVING mention_count >= 10
        ORDER BY mention_count DESC, last_mention DESC
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    loan_cards = ""
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                days = (row['last_mention'] - row['first_mention']).days
                loan_cards += f'''
                <div class="loan-card" onclick="window.location.href='/loan/{loan}'">
                    <div class="loan-number">#{loan}</div>
                    <div class="stats">
                        <span>{row['mention_count']} calls over {days} days</span>
                    </div>
                </div>
                '''
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Broker Activity Tracker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
            }}
            .loan-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 30px;
            }}
            .loan-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: all 0.2s;
                text-align: center;
            }}
            .loan-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .loan-number {{
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
                margin-bottom: 10px;
            }}
            .stats {{
                color: #7f8c8d;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📞 Broker Activity Tracker</h1>
            <p style="text-align: center; color: #7f8c8d;">Click any loan to see timeline with clickable phone numbers</p>
            <div class="loan-grid">
                {loan_cards}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/loan/{loan_number}", response_class=HTMLResponse)
async def loan_timeline(loan_number: str):
    """Show loan timeline with clickable phone numbers"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get loan timeline
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.summary,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    
    if not calls:
        return HTMLResponse("<h1>No calls found</h1>")
    
    # Get loan date range
    first_date = calls[0]['timestamp']
    last_date = calls[-1]['timestamp']
    
    # Build timeline
    timeline_html = ""
    for idx, call in enumerate(calls, 1):
        timeline_html += f'''
        <div class="timeline-item">
            <div class="call-header">
                <span class="call-number">Call #{idx}</span>
                <span class="call-date">{call['timestamp'].strftime('%m/%d/%Y %I:%M %p')}</span>
                <span class="call-duration">{call['duration']}s</span>
            </div>
            <div class="call-parties">
                <span class="phone-number clickable" onclick="searchBroker('{call['localParty']}', '{loan_number}', '{first_date}', '{last_date}')">{call['localParty']}</span>
                <span class="arrow">→</span>
                <span class="phone-number clickable" onclick="searchBroker('{call['remoteParty']}', '{loan_number}', '{first_date}', '{last_date}')">{call['remoteParty']}</span>
            </div>
            <div class="call-details">
                User: {call['user_name']}
                {f'<br>Summary: {call["summary"][:100]}...' if call.get('summary') else ''}
            </div>
        </div>
        '''
    
    cursor.close()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan #{loan_number} - Broker Tracking</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }}
            .header {{
                background: white;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                margin: 0;
                color: #2c3e50;
            }}
            .info {{
                color: #7f8c8d;
                margin: 10px 0;
            }}
            .timeline {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            .timeline-item {{
                padding: 15px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .timeline-item:last-child {{
                border-bottom: none;
            }}
            .call-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 14px;
                color: #7f8c8d;
            }}
            .call-number {{
                font-weight: bold;
                color: #2c3e50;
            }}
            .call-parties {{
                font-size: 18px;
                margin: 10px 0;
            }}
            .phone-number {{
                font-family: monospace;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
            }}
            .phone-number.clickable {{
                background: #e3f2fd;
                color: #1976d2;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .phone-number.clickable:hover {{
                background: #1976d2;
                color: white;
                transform: scale(1.05);
            }}
            .arrow {{
                margin: 0 10px;
                color: #7f8c8d;
            }}
            .call-details {{
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 10px;
            }}
            .back {{
                color: #3498db;
                text-decoration: none;
            }}
            
            /* Modal for broker search results */
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }}
            .modal-content {{
                background-color: white;
                margin: 5% auto;
                padding: 20px;
                border-radius: 8px;
                width: 90%;
                max-width: 1000px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }}
            .close {{
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }}
            .close:hover {{
                color: black;
            }}
            .broker-timeline {{
                margin-top: 20px;
            }}
            .broker-call {{
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
            }}
            .broker-call.same-loan {{
                background: #d4edda;
                border: 1px solid #c3e6cb;
            }}
            .broker-call.different-loan {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
            }}
            .broker-call.no-loan {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
                font-size: 18px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <a href="/loans" class="back">← Back to Loans</a>
                <h1>Loan #{loan_number}</h1>
                <p class="info">📅 {first_date.strftime('%m/%d/%Y')} to {last_date.strftime('%m/%d/%Y')}</p>
                <p class="info">💡 Click any phone number to see all their activity during this loan's lifecycle</p>
            </div>
        </div>
        
        <div class="container">
            <div class="timeline">
                <h2>Timeline</h2>
                {timeline_html}
            </div>
        </div>
        
        <!-- Broker Activity Modal -->
        <div id="brokerModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <h2 id="brokerTitle">Broker Activity</h2>
                <div id="brokerContent">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        </div>
        
        <script>
            async function searchBroker(phoneNumber, currentLoan, firstDate, lastDate) {{
                // Show modal
                document.getElementById('brokerModal').style.display = 'block';
                document.getElementById('brokerTitle').textContent = 'Activity for ' + phoneNumber;
                document.getElementById('brokerContent').innerHTML = '<div class="loading">Searching all calls...</div>';
                
                // Fetch broker activity
                const response = await fetch('/broker-search', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        phone_number: phoneNumber,
                        current_loan: currentLoan,
                        first_date: firstDate,
                        last_date: lastDate
                    }})
                }});
                
                const data = await response.json();
                
                // Display results
                let html = `
                    <div class="broker-stats">
                        <p><strong>Total Calls:</strong> ${{data.total_calls}}</p>
                        <p><strong>Loan Numbers Discussed:</strong> ${{data.unique_loans.join(', ') || 'None'}}</p>
                        <p><strong>Period:</strong> ${{data.period}}</p>
                    </div>
                    <div class="broker-timeline">
                        <h3>Call History</h3>
                `;
                
                data.calls.forEach((call, idx) => {{
                    let callClass = 'no-loan';
                    let loanInfo = 'No loan mentioned';
                    
                    if (call.loans && call.loans.length > 0) {{
                        if (call.loans.includes(currentLoan)) {{
                            callClass = 'same-loan';
                            loanInfo = 'Loan #' + currentLoan;
                        }} else {{
                            callClass = 'different-loan';
                            loanInfo = 'Loan #' + call.loans.join(', #');
                        }}
                    }}
                    
                    html += `
                        <div class="broker-call ${{callClass}}">
                            <div style="display: flex; justify-content: space-between;">
                                <span><strong>#${{idx + 1}}</strong> ${{call.timestamp}}</span>
                                <span>${{call.duration}}s</span>
                            </div>
                            <div>${{call.localParty}} → ${{call.remoteParty}}</div>
                            <div style="margin-top: 5px; font-size: 14px;">
                                <strong>${{loanInfo}}</strong>
                                ${{call.summary ? '<br>' + call.summary.substring(0, 100) + '...' : ''}}
                            </div>
                        </div>
                    `;
                }});
                
                html += '</div>';
                document.getElementById('brokerContent').innerHTML = html;
            }}
            
            function closeModal() {{
                document.getElementById('brokerModal').style.display = 'none';
            }}
            
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('brokerModal');
                if (event.target == modal) {{
                    closeModal();
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.post("/broker-search")
async def broker_search(data: dict):
    """Search all activity for a phone number during loan lifecycle"""
    
    phone_number = data.get('phone_number')
    current_loan = data.get('current_loan')
    first_date = data.get('first_date')
    last_date = data.get('last_date')
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all calls for this phone number from first mention through entire index
    cursor.execute("""
        SELECT 
            t.orkUid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.loan_numbers,
            ct.summary,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE (t.localParty = %s OR t.remoteParty = %s)
        AND t.timestamp >= %s
        ORDER BY t.timestamp
    """, (phone_number, phone_number, first_date))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Process results
    unique_loans = set()
    processed_calls = []
    
    for call in calls:
        call_data = {
            'orkuid': call['orkUid'],
            'timestamp': call['timestamp'].strftime('%m/%d/%Y %I:%M %p'),
            'duration': call['duration'],
            'localParty': call['localParty'],
            'remoteParty': call['remoteParty'],
            'user': call['user_name'],
            'summary': call.get('summary'),
            'loans': []
        }
        
        if call.get('loan_numbers'):
            try:
                loans = json.loads(call['loan_numbers'])
                call_data['loans'] = loans
                unique_loans.update(loans)
            except:
                pass
        
        processed_calls.append(call_data)
    
    # Calculate period
    if calls:
        period = f"{calls[0]['timestamp'].strftime('%m/%d/%Y')} to {calls[-1]['timestamp'].strftime('%m/%d/%Y')}"
    else:
        period = "No calls found"
    
    return JSONResponse({
        'phone_number': phone_number,
        'total_calls': len(calls),
        'unique_loans': sorted(list(unique_loans)),
        'period': period,
        'calls': processed_calls
    })

if __name__ == "__main__":
    print("Starting Broker Activity Tracker...")
    print("Open: http://localhost:8003")
    print("\nClick any phone number to see their full activity!")
    uvicorn.run(app, host="0.0.0.0", port=8003)