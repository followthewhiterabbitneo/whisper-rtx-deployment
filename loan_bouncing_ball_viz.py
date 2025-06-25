#!/usr/bin/env python3
"""
LOAN BOUNCING BALL VISUALIZATION
Interactive timeline showing the loan journey from submission to CTC
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Loan Bouncing Ball")

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
    """List loans to track"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get loans with their journey info
    cursor.execute("""
        SELECT 
            loan_numbers,
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention,
            COUNT(DISTINCT ct.orkuid) as mention_count
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        HAVING mention_count >= 3
        ORDER BY last_mention DESC
        LIMIT 30
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    loan_cards = ""
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                journey_days = (row['last_mention'] - row['first_mention']).days
                loan_cards += f'''
                <div class="loan-card" onclick="window.location.href='/journey/{loan}'">
                    <h3>Loan #{loan}</h3>
                    <p>📅 {journey_days} day journey</p>
                    <p>📞 {row['mention_count']} calls</p>
                    <p>{row['first_mention'].strftime('%m/%d')} → {row['last_mention'].strftime('%m/%d')}</p>
                </div>
                '''
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Journey Tracker</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .loan-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}
            .loan-card {{
                background: white;
                border: 2px solid #ddd;
                padding: 20px;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .loan-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                border-color: #0066cc;
            }}
            .loan-card h3 {{
                color: #0066cc;
                margin: 0 0 10px 0;
            }}
            .loan-card p {{
                margin: 5px 0;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Loan Journey Tracker</h1>
            <p style="text-align: center;">Follow the bouncing ball from submission to Clear to Close</p>
            <div class="loan-grid">
                {loan_cards}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/journey/{loan_number}", response_class=HTMLResponse)
async def show_journey(loan_number: str):
    """Show the bouncing ball journey for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get first and last mentions
    cursor.execute("""
        SELECT 
            MIN(t.timestamp) as first_mention,
            MAX(t.timestamp) as last_mention
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
    """, (f'%{loan_number}%',))
    
    date_range = cursor.fetchone()
    if not date_range:
        return HTMLResponse("<h1>No journey found for this loan</h1>")
    
    # Expand window by 2 days each side
    start_date = date_range['first_mention'] - timedelta(days=2)
    end_date = date_range['last_mention'] + timedelta(days=2)
    
    # Get all relevant calls
    cursor.execute("""
        SELECT 
            t.orkUid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            ct.loan_numbers,
            CASE 
                WHEN ct.loan_numbers LIKE %s THEN 'DIRECT'
                WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 'PROCESSOR'
                ELSE 'NETWORK'
            END as call_type,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM orktape t
        LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE t.timestamp BETWEEN %s AND %s
        AND (
            ct.loan_numbers LIKE %s
            OR t.localParty IN (
                SELECT DISTINCT localParty FROM orktape t2 
                JOIN call_transcripts_v2 ct2 ON t2.orkUid = ct2.orkuid 
                WHERE ct2.loan_numbers LIKE %s
            )
            OR t.remoteParty IN (
                SELECT DISTINCT remoteParty FROM orktape t2 
                JOIN call_transcripts_v2 ct2 ON t2.orkUid = ct2.orkuid 
                WHERE ct2.loan_numbers LIKE %s
            )
            OR t.localParty LIKE '19472421%%' 
            OR t.remoteParty LIKE '19472421%%'
        )
        ORDER BY t.timestamp
    """, (f'%{loan_number}%', start_date, end_date, 
          f'%{loan_number}%', f'%{loan_number}%', f'%{loan_number}%'))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Build timeline data
    timeline_data = []
    for idx, call in enumerate(calls):
        # Check if this call mentions the loan
        has_loan = False
        if call.get('loan_numbers'):
            try:
                loans = json.loads(call['loan_numbers'])
                has_loan = loan_number in loans
            except:
                pass
        
        # Determine call importance
        if has_loan:
            importance = "high"
            color = "#00aa00"
        elif call['call_type'] == 'PROCESSOR':
            importance = "medium"
            color = "#ff9900"
        else:
            importance = "low"
            color = "#666666"
        
        timeline_data.append({
            'id': idx,
            'timestamp': call['timestamp'].isoformat(),
            'date': call['timestamp'].strftime('%m/%d'),
            'time': call['timestamp'].strftime('%I:%M %p'),
            'duration': call['duration'],
            'from': call['localParty'],
            'to': call['remoteParty'],
            'user': call['user_name'],
            'type': call['call_type'],
            'has_loan': has_loan,
            'importance': importance,
            'color': color,
            'path': call.get('transcript_path', '') or ''
        })
    
    # Calculate stats
    journey_days = (date_range['last_mention'] - date_range['first_mention']).days
    direct_calls = sum(1 for c in calls if c['call_type'] == 'DIRECT')
    processor_calls = sum(1 for c in calls if c['call_type'] == 'PROCESSOR')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan_number} Journey</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }}
            .header {{
                background: white;
                padding: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                margin: 0;
                color: #333;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #0066cc;
            }}
            .timeline-container {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin: 20px 0;
                overflow-x: auto;
            }}
            .timeline {{
                position: relative;
                min-height: 400px;
                padding: 40px 0;
            }}
            .timeline-line {{
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 4px;
                background: #ddd;
            }}
            .call-point {{
                position: absolute;
                transform: translateX(-50%);
                cursor: pointer;
                transition: all 0.3s;
            }}
            .call-point:hover {{
                transform: translateX(-50%) scale(1.2);
            }}
            .call-dot {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }}
            .call-label {{
                position: absolute;
                top: -30px;
                left: 50%;
                transform: translateX(-50%);
                background: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                white-space: nowrap;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .call-details {{
                display: none;
                position: absolute;
                top: 40px;
                left: 50%;
                transform: translateX(-50%);
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                z-index: 100;
                min-width: 300px;
            }}
            .call-point:hover .call-details {{
                display: block;
            }}
            .legend {{
                margin: 20px 0;
                display: flex;
                gap: 20px;
                justify-content: center;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            .legend-dot {{
                width: 15px;
                height: 15px;
                border-radius: 50%;
            }}
            .back {{
                color: #0066cc;
                text-decoration: none;
                margin-bottom: 20px;
                display: inline-block;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background: #f5f5f5;
            }}
            .direct-call {{
                background: #e8f8e8;
                font-weight: bold;
            }}
            .processor-call {{
                background: #fff8e8;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <a href="/" class="back">← Back to Loans</a>
                <h1>🎯 Loan #{loan_number} Journey</h1>
                <p>Following the bouncing ball from submission to Clear to Close</p>
            </div>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{journey_days}</div>
                    <div>Journey Days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(calls)}</div>
                    <div>Total Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{direct_calls}</div>
                    <div>Direct Mentions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{processor_calls}</div>
                    <div>Processor Calls</div>
                </div>
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-dot" style="background: #00aa00;"></div>
                    <span>Direct Loan Mention</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #ff9900;"></div>
                    <span>Processor Assistant</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #666666;"></div>
                    <span>Network Call</span>
                </div>
            </div>
            
            <div class="timeline-container">
                <h2>Interactive Timeline (Hover for details)</h2>
                <div class="timeline" id="timeline">
                    <div class="timeline-line"></div>
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2>Call Details</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Date/Time</th>
                            <th>Type</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Duration</th>
                            <th>User</th>
                            <th>Loan?</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add table rows
    for call in calls:
        has_loan = False
        if call.get('loan_numbers'):
            try:
                loans = json.loads(call['loan_numbers'])
                has_loan = loan_number in loans
            except:
                pass
        
        row_class = ""
        if has_loan:
            row_class = "direct-call"
        elif call['call_type'] == 'PROCESSOR':
            row_class = "processor-call"
        
        html += f"""
                        <tr class="{row_class}">
                            <td>{call['timestamp'].strftime('%m/%d/%Y %I:%M %p')}</td>
                            <td>{call['call_type']}</td>
                            <td>{call['localParty']}</td>
                            <td>{call['remoteParty']}</td>
                            <td>{call['duration']}s</td>
                            <td>{call['user_name']}</td>
                            <td>{'✓' if has_loan else ''}</td>
                        </tr>
        """
    
    html += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            const timelineData = {json.dumps(timeline_data)};
            const timeline = document.getElementById('timeline');
            
            // Calculate positions
            const startTime = new Date(timelineData[0].timestamp).getTime();
            const endTime = new Date(timelineData[timelineData.length - 1].timestamp).getTime();
            const timeRange = endTime - startTime;
            const timelineWidth = timeline.offsetWidth - 100; // Leave margins
            
            // Create call points
            timelineData.forEach((call, idx) => {{
                const callTime = new Date(call.timestamp).getTime();
                const position = ((callTime - startTime) / timeRange) * timelineWidth + 50;
                
                const callPoint = document.createElement('div');
                callPoint.className = 'call-point';
                callPoint.style.left = position + 'px';
                callPoint.style.top = '50%';
                
                // Create dot
                const dot = document.createElement('div');
                dot.className = 'call-dot';
                dot.style.background = call.color;
                
                // Create label
                const label = document.createElement('div');
                label.className = 'call-label';
                label.innerHTML = call.date + '<br>' + call.time;
                
                // Create details popup
                const details = document.createElement('div');
                details.className = 'call-details';
                details.innerHTML = `
                    <strong>${{call.type}} Call</strong><br>
                    <strong>Date:</strong> ${{call.date}} ${{call.time}}<br>
                    <strong>From:</strong> ${{call.from}}<br>
                    <strong>To:</strong> ${{call.to}}<br>
                    <strong>Duration:</strong> ${{call.duration}}s<br>
                    <strong>User:</strong> ${{call.user}}<br>
                    <strong>Has Loan:</strong> ${{call.has_loan ? 'Yes ✓' : 'No'}}<br>
                    <strong>Path:</strong> <small>${{call.path}}</small>
                `;
                
                // Alternate label positions to avoid overlap
                if (idx % 2 === 0) {{
                    label.style.top = '-30px';
                    details.style.top = '40px';
                }} else {{
                    label.style.top = 'auto';
                    label.style.bottom = '-30px';
                    details.style.top = '-200px';
                }}
                
                callPoint.appendChild(dot);
                callPoint.appendChild(label);
                callPoint.appendChild(details);
                timeline.appendChild(callPoint);
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting Loan Bouncing Ball Visualization...")
    print("Open: http://localhost:8005")
    print("\nFollow the loan journey from submission to Clear to Close!")
    uvicorn.run(app, host="0.0.0.0", port=8005)