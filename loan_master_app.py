#!/usr/bin/env python3
"""
LOAN MASTER APP - All features on one port with route points
No more multiple ports!
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pymysql
import json
from datetime import datetime, timedelta
import os
import uvicorn
import re
from collections import defaultdict

app = FastAPI(title="Loan Master App")

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Store feedback in memory
feedback_data = {}

def gmt_to_est(timestamp):
    """Convert GMT timestamp to EST (GMT-5)"""
    if timestamp:
        # Subtract 5 hours for EST (you might want to handle DST properly in production)
        return timestamp - timedelta(hours=5)
    return timestamp

@app.get("/", response_class=HTMLResponse)
async def home():
    """Main navigation page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Master - All Features</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f7fa;
            }
            .header {
                background: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
            }
            .nav {
                background: #34495e;
                padding: 0;
                display: flex;
                justify-content: center;
            }
            .nav a {
                color: white;
                padding: 15px 25px;
                text-decoration: none;
                transition: background 0.3s;
            }
            .nav a:hover {
                background: #2c3e50;
            }
            .container {
                max-width: 1200px;
                margin: 40px auto;
                padding: 0 20px;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature-card {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                transition: all 0.3s;
                cursor: pointer;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .feature-icon {
                font-size: 48px;
                margin-bottom: 15px;
            }
            .feature-title {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .feature-desc {
                color: #7f8c8d;
            }
            .quick-search {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .search-input {
                padding: 12px 20px;
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 5px;
                width: 300px;
                margin-right: 10px;
            }
            .search-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .search-btn:hover {
                background: #2980b9;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Loan Master</h1>
            <p>All loan management features in one place</p>
        </div>
        
        <div class="nav">
            <a href="/timeline">📊 Timeline</a>
            <a href="/broker-tracker">📞 Broker Tracker</a>
            <a href="/analytics">📈 Analytics</a>
            <a href="/untranscribed">🔍 Untranscribed</a>
            <a href="/brief-generator">📄 Brief Generator</a>
        </div>
        
        <div class="container">
            <div class="quick-search">
                <h2>Quick Loan Search</h2>
                <input type="text" id="loanNumber" class="search-input" placeholder="Enter loan number..." onkeypress="if(event.key==='Enter')quickSearch()">
                <button class="search-btn" onclick="quickSearch()">Search</button>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card" onclick="location.href='/timeline'">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Loan Timeline</div>
                    <div class="feature-desc">View timeline with feedback & thumbs down to correct loan numbers</div>
                </div>
                
                <div class="feature-card" onclick="location.href='/broker-tracker'">
                    <div class="feature-icon">📞</div>
                    <div class="feature-title">Broker Activity Tracker</div>
                    <div class="feature-desc">Click any phone number to see full broker activity</div>
                </div>
                
                <div class="feature-card" onclick="location.href='/brief-generator'">
                    <div class="feature-icon">📄</div>
                    <div class="feature-title">Generate Loan Brief</div>
                    <div class="feature-desc">Create comprehensive LOAN_BRIEF_[NUMBER].txt</div>
                </div>
                
                <div class="feature-card" onclick="location.href='/untranscribed'">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Find Untranscribed</div>
                    <div class="feature-desc">Identify calls needing transcription</div>
                </div>
                
                <div class="feature-card" onclick="location.href='/add-call'">
                    <div class="feature-icon">➕</div>
                    <div class="feature-title">Add Missing Call</div>
                    <div class="feature-desc">Insert broker transfers into timeline</div>
                </div>
                
                <div class="feature-card" onclick="location.href='/analytics'">
                    <div class="feature-icon">📈</div>
                    <div class="feature-title">Loan Analytics</div>
                    <div class="feature-desc">View loans with 10+ calls and patterns</div>
                </div>
            </div>
        </div>
        
        <script>
            function quickSearch() {
                const loanNumber = document.getElementById('loanNumber').value.trim();
                if (loanNumber) {
                    window.location.href = `/timeline/${loanNumber}`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/timeline", response_class=HTMLResponse)
@app.get("/timeline/{loan_number}", response_class=HTMLResponse)
async def timeline(loan_number: str = None):
    """Loan timeline with feedback"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    if not loan_number:
        # Show loan list
        cursor.execute("""
            SELECT 
                loan_numbers,
                COUNT(*) as mention_count,
                MIN(t.timestamp) as first_mention,
                MAX(t.timestamp) as last_mention,
                SUM(CASE WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' THEN 1 ELSE 0 END) as processor_calls
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
                    <div class="loan-card" onclick="window.location.href='/timeline/{loan}'">
                        <div class="loan-number">#{loan}</div>
                        <div class="stats">
                            <div class="stat">
                                <span class="value">{row['mention_count']}</span>
                                <span class="label">calls</span>
                            </div>
                            <div class="stat">
                                <span class="value">{row['processor_calls']}</span>
                                <span class="label">processor</span>
                            </div>
                            <div class="stat">
                                <span class="value">{days}</span>
                                <span class="label">days</span>
                            </div>
                        </div>
                        <div class="dates">{row['first_mention'].strftime('%m/%d')} → {row['last_mention'].strftime('%m/%d')}</div>
                    </div>
                    '''
            except:
                pass
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loan Timeline</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f7fa;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }}
                .back-btn {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }}
                .back-btn:hover {{
                    background: #2980b9;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: #2c3e50;
                    margin: 0;
                }}
                .subtitle {{
                    color: #7f8c8d;
                    margin-bottom: 30px;
                }}
                .loan-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 15px;
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
                    margin-bottom: 15px;
                }}
                .stats {{
                    display: flex;
                    justify-content: space-around;
                    margin: 15px 0;
                }}
                .stat {{
                    text-align: center;
                }}
                .stat .value {{
                    display: block;
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .stat .label {{
                    display: block;
                    font-size: 12px;
                    color: #95a5a6;
                    text-transform: uppercase;
                }}
                .dates {{
                    font-size: 14px;
                    color: #7f8c8d;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Loan Timeline</h1>
                    <a href="/" class="back-btn">← Back to Home</a>
                </div>
                <p class="subtitle">Showing loans with 10+ calls - Click for details</p>
                <div class="loan-grid">
                    {loan_cards}
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    else:
        # Show specific loan timeline with feedback
        cursor.execute("""
            SELECT 
                ct.orkuid,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty,
                ct.transcript_path,
                ct.summary,
                COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name,
                CASE 
                    WHEN t.localParty LIKE '19472421%%' OR t.remoteParty LIKE '19472421%%' 
                    THEN 'PROCESSOR'
                    ELSE 'STANDARD'
                END as call_type
            FROM call_transcripts_v2 ct
            JOIN orktape t ON ct.orkuid = t.orkUid
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            WHERE ct.loan_numbers LIKE %s
            ORDER BY t.timestamp
        """, (f'%{loan_number}%',))
        
        calls = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not calls:
            return HTMLResponse(f"<h1>No calls found for loan {loan_number}</h1><a href='/timeline'>Back</a>")
        
        # Build timeline
        timeline_html = ""
        for idx, call in enumerate(calls, 1):
            is_processor = call['call_type'] == 'PROCESSOR'
            call_id = call['orkuid']
            
            timeline_html += f'''
            <div class="timeline-item {'processor' if is_processor else ''}" id="call_{call_id}">
                <div class="timeline-marker">
                    <div class="marker-dot"></div>
                    <div class="marker-line"></div>
                </div>
                <div class="timeline-content">
                    <div class="call-header">
                        <span class="call-number">Call #{idx}</span>
                        <span class="call-date">{gmt_to_est(call['timestamp']).strftime('%m/%d/%Y %I:%M %p')} EST</span>
                        <span class="call-duration">{call['duration']}s</span>
                    </div>
                    <div class="call-parties">
                        <div class="party-wrapper">
                            <span class="party from clickable" onclick="searchBroker('{call['localParty']}')">{call['localParty']}</span>
                            <span class="user-name">{call['user_name']}</span>
                        </div>
                        <span class="arrow">→</span>
                        <div class="party-wrapper">
                            <span class="party to clickable" onclick="searchBroker('{call['remoteParty']}')">{call['remoteParty']}</span>
                        </div>
                    </div>
                    {'<div class="processor-tag">PROCESSOR ASSISTANT</div>' if is_processor else ''}
                    <div style="color: #95a5a6; font-size: 12px; font-family: monospace; margin: 5px 0;">orkuid: {call_id}</div>
                    
                    <div class="feedback-section">
                        <div class="feedback-controls">
                            <button class="thumbs-up" onclick="markGood('{call_id}')" title="Correct loan">
                                👍
                            </button>
                            <button class="thumbs-down" onclick="markBad('{call_id}')" title="Wrong loan">
                                👎
                            </button>
                            <div class="loan-correction" id="correction_{call_id}" style="display:none;">
                                <input type="text" placeholder="Correct loan #" id="correct_loan_{call_id}" class="correction-input">
                                <button onclick="submitCorrection('{call_id}')" class="btn-submit-small">✓</button>
                                <button onclick="cancelCorrection('{call_id}')" class="btn-cancel-small">✗</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="transcript-path">
                        <input type="text" value="{call.get('transcript_path', '') or ''}" readonly>
                        <button onclick="copyPath(this)">📋</button>
                    </div>
                </div>
            </div>
            '''
        
        # Calculate stats
        first_call = calls[0]
        last_call = calls[-1]
        journey_days = (last_call['timestamp'] - first_call['timestamp']).days
        total_duration = sum(c['duration'] for c in calls)
        processor_count = sum(1 for c in calls if c['call_type'] == 'PROCESSOR')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loan #{loan_number} Timeline</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: #f5f7fa;
                }}
                .header {{
                    background: white;
                    padding: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 20px;
                }}
                h1 {{
                    margin: 0;
                    color: #2c3e50;
                }}
                .nav-buttons {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                }}
                .nav-btn {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }}
                .nav-btn:hover {{
                    background: #2980b9;
                }}
                .nav-btn.secondary {{
                    background: #95a5a6;
                }}
                .nav-btn.secondary:hover {{
                    background: #7f8c8d;
                }}
                .nav-btn.success {{
                    background: #27ae60;
                }}
                .nav-btn.success:hover {{
                    background: #229954;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #3498db;
                }}
                .stat-label {{
                    color: #7f8c8d;
                    margin-top: 5px;
                }}
                .timeline {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }}
                .timeline-item {{
                    display: flex;
                    margin-bottom: 30px;
                    position: relative;
                }}
                .timeline-marker {{
                    width: 40px;
                    position: relative;
                    flex-shrink: 0;
                }}
                .marker-dot {{
                    width: 16px;
                    height: 16px;
                    background: #3498db;
                    border-radius: 50%;
                    position: absolute;
                    left: 12px;
                    top: 5px;
                    z-index: 2;
                }}
                .marker-line {{
                    width: 2px;
                    background: #e0e0e0;
                    position: absolute;
                    left: 19px;
                    top: 25px;
                    bottom: -30px;
                }}
                .timeline-item:last-child .marker-line {{
                    display: none;
                }}
                .timeline-content {{
                    flex: 1;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-left: 10px;
                }}
                .processor .timeline-content {{
                    background: #fff3cd;
                    border: 1px solid #ffeeba;
                }}
                .processor .marker-dot {{
                    background: #ff9900;
                }}
                .call-header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    font-size: 14px;
                }}
                .call-number {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .call-date {{
                    color: #7f8c8d;
                }}
                .call-duration {{
                    color: #3498db;
                }}
                .call-parties {{
                    font-size: 16px;
                    margin: 10px 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .party-wrapper {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }}
                .party {{
                    font-weight: 500;
                    padding: 4px 8px;
                    border-radius: 4px;
                }}
                .user-name {{
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-top: 2px;
                }}
                .party.clickable {{
                    background: #e3f2fd;
                    color: #1976d2;
                    cursor: pointer;
                    transition: all 0.2s;
                }}
                .party.clickable:hover {{
                    background: #1976d2;
                    color: white;
                }}
                .arrow {{
                    margin: 0 10px;
                    color: #7f8c8d;
                }}
                .call-user {{
                    color: #7f8c8d;
                    font-size: 14px;
                    margin: 5px 0;
                }}
                .processor-tag {{
                    display: inline-block;
                    background: #ff9900;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin: 5px 0;
                }}
                .feedback-section {{
                    margin: 15px 0;
                    padding: 10px 0;
                    border-top: 1px solid #e0e0e0;
                }}
                .feedback-controls {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .thumbs-up, .thumbs-down {{
                    background: #f0f0f0;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 18px;
                    width: 40px;
                    height: 40px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }}
                .thumbs-up:hover {{
                    background: #e0e0e0;
                    transform: scale(1.1);
                }}
                .thumbs-down:hover {{
                    background: #e0e0e0;
                    transform: scale(1.1);
                }}
                .thumbs-up.active {{
                    background: #d4edda;
                }}
                .thumbs-down.active {{
                    background: #f8d7da;
                }}
                .loan-correction {{
                    display: inline-flex;
                    gap: 5px;
                    align-items: center;
                    margin-left: 10px;
                }}
                .correction-input {{
                    padding: 5px 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    width: 120px;
                    font-size: 14px;
                }}
                .btn-submit-small, .btn-cancel-small {{
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .btn-cancel-small {{
                    background: #dc3545;
                }}
                .transcript-path {{
                    display: flex;
                    align-items: center;
                    margin-top: 10px;
                    gap: 5px;
                }}
                .transcript-path input {{
                    flex: 1;
                    padding: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 12px;
                    background: white;
                }}
                .transcript-path button {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                .toast {{
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 5px;
                    opacity: 0;
                    transition: opacity 0.3s;
                    pointer-events: none;
                }}
                .toast.show {{
                    opacity: 1;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>Loan #{loan_number} Timeline</h1>
                    <p style="color: #7f8c8d; margin: 5px 0;">Click phone numbers to see broker activity</p>
                </div>
            </div>
            
            <div class="container">
                <div class="nav-buttons">
                    <a href="/timeline" class="nav-btn">← Back to Loans</a>
                    <a href="/" class="nav-btn secondary">Home</a>
                    <button class="nav-btn success" onclick="window.location.href='/brief-generator?loan={loan_number}'">Generate Brief</button>
                    <button class="nav-btn secondary" onclick="window.location.href='/add-call?loan={loan_number}'">+ Add Call</button>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{len(calls)}</div>
                        <div class="stat-label">Total Mentions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{journey_days}</div>
                        <div class="stat-label">Journey Days</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{processor_count}</div>
                        <div class="stat-label">Processor Calls</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{int(total_duration/60)}</div>
                        <div class="stat-label">Total Minutes</div>
                    </div>
                </div>
                
                <div class="timeline">
                    <h2>Call Timeline</h2>
                    {timeline_html}
                </div>
            </div>
            
            <div id="toast" class="toast"></div>
            
            <script>
                function copyPath(button) {{
                    const input = button.previousElementSibling;
                    input.select();
                    document.execCommand('copy');
                    button.textContent = '✓';
                    setTimeout(() => button.textContent = '📋', 2000);
                }}
                
                async function markGood(callId) {{
                    const callDiv = document.getElementById('call_' + callId);
                    const thumbsUp = callDiv.querySelector('.thumbs-up');
                    const thumbsDown = callDiv.querySelector('.thumbs-down');
                    
                    thumbsUp.classList.toggle('active');
                    thumbsDown.classList.remove('active');
                    
                    await fetch('/api/feedback', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            call_id: callId,
                            type: 'correct'
                        }})
                    }});
                }}
                
                async function markBad(callId) {{
                    // Show correction input
                    const correctionDiv = document.getElementById('correction_' + callId);
                    correctionDiv.style.display = 'inline-flex';
                    document.getElementById('correct_loan_' + callId).focus();
                }}
                
                function cancelCorrection(callId) {{
                    document.getElementById('correction_' + callId).style.display = 'none';
                    document.getElementById('correct_loan_' + callId).value = '';
                }}
                
                async function submitCorrection(callId) {{
                    const correctLoan = document.getElementById('correct_loan_' + callId).value.trim();
                    
                    if (!correctLoan) {{
                        alert('Please enter the correct loan number');
                        return;
                    }}
                    
                    // Update UI
                    const callDiv = document.getElementById('call_' + callId);
                    const thumbsDown = callDiv.querySelector('.thumbs-down');
                    thumbsDown.classList.add('active');
                    
                    // Hide input
                    document.getElementById('correction_' + callId).style.display = 'none';
                    
                    // Send feedback
                    await fetch('/api/feedback', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            call_id: callId,
                            type: 'wrong',
                            correct_loan: correctLoan
                        }})
                    }});
                    
                    showToast(`Marked for loan #${{correctLoan}}`);
                }}
                
                function showToast(message) {{
                    const toast = document.getElementById('toast');
                    toast.textContent = message;
                    toast.classList.add('show');
                    setTimeout(() => {{
                        toast.classList.remove('show');
                    }}, 3000);
                }}
                
                function searchBroker(phoneNumber) {{
                    window.location.href = `/broker-tracker?phone=${{phoneNumber}}&loan={loan_number}`;
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)

@app.get("/broker-tracker", response_class=HTMLResponse)
async def broker_tracker(phone: str = None, loan: str = None):
    """Broker activity tracker"""
    
    if phone:
        # Show activity for specific phone number
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        # Get all calls for this phone number
        cursor.execute("""
            SELECT 
                t.orkUid,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty,
                ct.loan_numbers,
                ct.summary,
                ct.transcript_path,
                COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            WHERE (t.localParty = %s OR t.remoteParty = %s)
            ORDER BY t.timestamp DESC
            LIMIT 500
        """, (phone, phone))
        
        calls = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Build call history
        call_rows = ""
        unique_loans = set()
        
        for idx, call in enumerate(calls, 1):
            loans = []
            if call.get('loan_numbers'):
                try:
                    loans = json.loads(call['loan_numbers'])
                    unique_loans.update(loans)
                except:
                    pass
            
            loan_info = ', '.join(f'#{l}' for l in loans) if loans else 'No loan'
            row_class = ""
            if loans:
                if loan and loan in loans:
                    row_class = "same-loan"
                else:
                    row_class = "different-loan"
            
            # Get transcript info
            transcript_link = ""
            if call.get('transcript_path'):
                transcript_link = f'<a href="#" onclick="copyToClipboard(\'{call["transcript_path"]}\'); return false;" title="Click to copy path">📄</a>'
            
            call_rows += f'''
            <tr class="{row_class}">
                <td>{idx}</td>
                <td>{gmt_to_est(call['timestamp']).strftime('%m/%d/%Y %I:%M %p')}</td>
                <td>{call['duration']}s</td>
                <td>
                    <div class="phone-with-user">
                        <div>{call['localParty']}</div>
                        <div class="user-label">{call['user_name']}</div>
                    </div>
                </td>
                <td>
                    <div class="phone-with-user">
                        <div>{call['remoteParty']}</div>
                    </div>
                </td>
                <td>{loan_info}</td>
                <td style="color: #95a5a6; font-size: 12px; font-family: monospace;">{call['orkUid']}</td>
                <td>{transcript_link}</td>
            </tr>
            '''
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Broker Activity - {phone}</title>
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
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    margin: 0;
                    color: #2c3e50;
                }}
                .back-btn {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    text-decoration: none;
                    display: inline-block;
                    margin-bottom: 20px;
                }}
                .back-btn:hover {{
                    background: #2980b9;
                }}
                .stats {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }}
                table {{
                    width: 100%;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                th {{
                    background: #34495e;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #ecf0f1;
                }}
                tr:hover {{
                    background: #f8f9fa;
                }}
                .same-loan {{
                    background: #d4edda !important;
                }}
                .different-loan {{
                    background: #fff3cd !important;
                }}
                .legend {{
                    margin: 20px 0;
                    display: flex;
                    gap: 20px;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                .legend-box {{
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                }}
                .phone-with-user {{
                    display: inline-flex;
                    flex-direction: column;
                    align-items: center;
                }}
                .user-label {{
                    font-size: 11px;
                    color: #95a5a6;
                    margin-top: 2px;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📞 Broker Activity: {phone}</h1>
            </div>
            
            <div class="container">
                <a href="javascript:history.back()" class="back-btn">← Back</a>
                
                <div class="stats">
                    <h2>Summary</h2>
                    <p><strong>Total Calls:</strong> {len(calls)}</p>
                    <p><strong>Unique Loans:</strong> {', '.join(f'#{l}' for l in sorted(unique_loans)) if unique_loans else 'None'}</p>
                    <p><strong>Total Duration:</strong> {sum(c['duration'] for c in calls) / 60:.1f} minutes</p>
                </div>
                
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-box" style="background: #d4edda;"></div>
                        <span>Current loan</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-box" style="background: #fff3cd;"></div>
                        <span>Different loan</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-box" style="background: white;"></div>
                        <span>No loan</span>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Date/Time (EST)</th>
                            <th>Duration</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Loan</th>
                            <th>orkUid</th>
                            <th>Transcript</th>
                        </tr>
                    </thead>
                    <tbody>
                        {call_rows}
                    </tbody>
                </table>
            </div>
            
            <script>
                function copyToClipboard(text) {{
                    navigator.clipboard.writeText(text).then(function() {{
                        // Create a temporary toast notification
                        const toast = document.createElement('div');
                        toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; background: #28a745; color: white; padding: 10px 20px; border-radius: 5px; z-index: 1000;';
                        toast.textContent = 'Path copied to clipboard!';
                        document.body.appendChild(toast);
                        setTimeout(() => document.body.removeChild(toast), 2000);
                    }}, function(err) {{
                        alert('Failed to copy path');
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    else:
        # Show broker search page
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Broker Activity Tracker</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f7fa;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    text-align: center;
                }
                .search-box {
                    display: flex;
                    gap: 10px;
                    margin: 30px 0;
                }
                .search-input {
                    flex: 1;
                    padding: 12px;
                    font-size: 16px;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                }
                .search-btn {
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .search-btn:hover {
                    background: #2980b9;
                }
                .back-btn {
                    background: #95a5a6;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    text-decoration: none;
                    display: inline-block;
                }
                .back-btn:hover {
                    background: #7f8c8d;
                }
                .info {
                    color: #7f8c8d;
                    text-align: center;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Back to Home</a>
                <h1>📞 Broker Activity Tracker</h1>
                <p class="info">Enter a phone number to see all their call activity</p>
                
                <div class="search-box">
                    <input type="text" id="phoneNumber" class="search-input" placeholder="Enter phone number (e.g., 2485551234)" onkeypress="if(event.key==='Enter')searchBroker()">
                    <button class="search-btn" onclick="searchBroker()">Search</button>
                </div>
                
                <p class="info">This will show all calls made by or to this phone number, with loan associations highlighted.</p>
            </div>
            
            <script>
                function searchBroker() {
                    const phone = document.getElementById('phoneNumber').value.trim();
                    if (phone) {
                        window.location.href = `/broker-tracker?phone=${phone}`;
                    }
                }
            </script>
        </body>
        </html>
        """)

@app.get("/brief-generator", response_class=HTMLResponse)
async def brief_generator(loan: str = None):
    """Loan brief generator page"""
    
    if loan:
        # Generate brief for specific loan
        try:
            from generate_loan_brief import generate_loan_brief
            filename = generate_loan_brief(loan)
            
            # Read the generated file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Loan Brief - {loan}</title>
                <style>
                    body {{
                        font-family: 'Courier New', monospace;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1000px;
                        margin: 0 auto;
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                        padding-bottom: 20px;
                        border-bottom: 2px solid #e0e0e0;
                    }}
                    h1 {{
                        margin: 0;
                        color: #2c3e50;
                    }}
                    .buttons {{
                        display: flex;
                        gap: 10px;
                    }}
                    .btn {{
                        background: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                    }}
                    .btn:hover {{
                        background: #2980b9;
                    }}
                    .btn.success {{
                        background: #27ae60;
                    }}
                    .btn.success:hover {{
                        background: #229954;
                    }}
                    .content {{
                        white-space: pre-wrap;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .highlight {{
                        background: #fff3cd;
                        padding: 2px 4px;
                        border-radius: 3px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📄 Loan Brief - {loan}</h1>
                        <div class="buttons">
                            <a href="/timeline/{loan}" class="btn">View Timeline</a>
                            <a href="/download-brief/{loan}" class="btn success">Download File</a>
                            <button class="btn" onclick="window.print()">Print</button>
                        </div>
                    </div>
                    <div class="content">{content}</div>
                </div>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html)
            
        except Exception as e:
            return HTMLResponse(f"<h1>Error generating brief: {str(e)}</h1><a href='/brief-generator'>Back</a>")
    
    else:
        # Show brief generator form
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loan Brief Generator</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f7fa;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    text-align: center;
                }
                .form-group {
                    margin: 30px 0;
                }
                .label {
                    display: block;
                    margin-bottom: 10px;
                    color: #2c3e50;
                    font-weight: 500;
                }
                .input {
                    width: 100%;
                    padding: 12px;
                    font-size: 16px;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    box-sizing: border-box;
                }
                .btn {
                    background: #27ae60;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    width: 100%;
                }
                .btn:hover {
                    background: #229954;
                }
                .back-btn {
                    background: #95a5a6;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    text-decoration: none;
                    display: inline-block;
                }
                .back-btn:hover {
                    background: #7f8c8d;
                }
                .info {
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    color: #1976d2;
                }
                .features {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .features h3 {
                    margin-top: 0;
                    color: #2c3e50;
                }
                .features ul {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                .features li {
                    margin: 5px 0;
                    color: #555;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Back to Home</a>
                <h1>📄 Generate Loan Brief</h1>
                
                <div class="info">
                    This will create a comprehensive LOAN_BRIEF_[NUMBER].txt file with all call details, conditions, dates, and sentiment analysis.
                </div>
                
                <div class="form-group">
                    <label class="label" for="loanNumber">Loan Number</label>
                    <input type="text" id="loanNumber" class="input" placeholder="Enter loan number (e.g., 1225237672)" onkeypress="if(event.key==='Enter')generateBrief()">
                </div>
                
                <button class="btn" onclick="generateBrief()">Generate Brief</button>
                
                <div class="features">
                    <h3>What's included in the brief:</h3>
                    <ul>
                        <li>Complete call timeline organized by day</li>
                        <li>Combined conversations (calls with same timestamp)</li>
                        <li>Broker/LO names and contact information</li>
                        <li>All conditions and requirements to clear</li>
                        <li>Important dates (CTC, submission, closing)</li>
                        <li>Sentiment analysis (especially angry/frustrated calls)</li>
                        <li>Processor assistant involvement</li>
                        <li>Executive summary with key insights</li>
                        <li>Untranscribed call warnings</li>
                    </ul>
                </div>
            </div>
            
            <script>
                function generateBrief() {
                    const loanNumber = document.getElementById('loanNumber').value.trim();
                    if (loanNumber) {
                        window.location.href = `/brief-generator?loan=${loanNumber}`;
                    } else {
                        alert('Please enter a loan number');
                    }
                }
            </script>
        </body>
        </html>
        """)

@app.get("/download-brief/{loan_number}")
async def download_brief(loan_number: str):
    """Download generated brief file"""
    filename = f"LOAN_BRIEF_{loan_number}.txt"
    if os.path.exists(filename):
        return FileResponse(filename, filename=filename)
    else:
        return HTMLResponse("Brief not found", status_code=404)

@app.get("/untranscribed", response_class=HTMLResponse)
async def untranscribed():
    """Find untranscribed calls page"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get summary
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM call_transcripts_v2
        WHERE (transcript_path IS NULL OR transcript_path = '')
        AND (transcript_text IS NULL OR transcript_text = '')
    """)
    total_untranscribed = cursor.fetchone()['total']
    
    # Get top loans needing transcription
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as count,
            SUM(t.duration) as total_duration
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
        AND loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY count DESC
        LIMIT 20
    """)
    
    loan_rows = ""
    for row in cursor.fetchall():
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                duration_min = row['total_duration'] / 60 if row['total_duration'] else 0
                loan_rows += f'''
                <tr>
                    <td><a href="/untranscribed/{loan}">{loan}</a></td>
                    <td>{row['count']}</td>
                    <td>{duration_min:.1f}</td>
                    <td>
                        <a href="/timeline/{loan}" class="action-btn">View Timeline</a>
                        <a href="/untranscribed/{loan}" class="action-btn">Details</a>
                    </td>
                </tr>
                '''
        except:
            pass
    
    cursor.close()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Untranscribed Calls</title>
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
            .header {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            h1 {{
                margin: 0;
                color: #2c3e50;
            }}
            .summary {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .back-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }}
            .back-btn:hover {{
                background: #2980b9;
            }}
            table {{
                width: 100%;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .action-btn {{
                background: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                margin-right: 5px;
                font-size: 12px;
                display: inline-block;
            }}
            .action-btn:hover {{
                background: #2980b9;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Back to Home</a>
            
            <div class="header">
                <h1>🔍 Untranscribed Calls</h1>
            </div>
            
            <div class="summary">
                <h2>System Summary</h2>
                <p><strong>Total untranscribed calls:</strong> {total_untranscribed}</p>
                <p>The following loans have calls that need transcription:</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Loan Number</th>
                        <th>Untranscribed Calls</th>
                        <th>Total Duration (min)</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {loan_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/untranscribed/{loan_number}", response_class=HTMLResponse)
async def untranscribed_loan_details(loan_number: str):
    """Show untranscribed calls for specific loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            t.filename
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE ct.loan_numbers LIKE %s
        AND (ct.transcript_path IS NULL OR ct.transcript_path = '')
        AND (ct.transcript_text IS NULL OR ct.transcript_text = '')
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    cursor.close()
    conn.close()
    
    call_rows = ""
    queue_content = f"# Transcription Queue for Loan {loan_number}\n"
    queue_content += f"# Generated: {datetime.now()}\n\n"
    
    for idx, call in enumerate(calls, 1):
        # Build audio path
        ts = call['timestamp']
        audio_path = f"/var/log/orkaudio.prod.nfs/audio/{ts.strftime('%Y/%m/%d/%H')}/{call['filename'] or call['orkuid'] + '.wav'}"
        
        call_rows += f'''
        <tr>
            <td>{idx}</td>
            <td>{call['orkuid']}</td>
            <td>{call['timestamp'].strftime('%m/%d/%Y %I:%M %p')}</td>
            <td>{call['duration']}s</td>
            <td>{call['localParty']}</td>
            <td>{call['remoteParty']}</td>
            <td class="audio-path">{audio_path}</td>
        </tr>
        '''
        
        queue_content += f"{call['orkuid']}|{audio_path}\n"
    
    # Escape backticks for JavaScript
    queue_content_escaped = queue_content.replace("`", "\\`")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Untranscribed Calls - Loan {loan_number}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            h1 {{
                margin: 0;
                color: #2c3e50;
            }}
            .back-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
            }}
            .back-btn:hover {{
                background: #2980b9;
            }}
            .download-btn {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }}
            .download-btn:hover {{
                background: #229954;
            }}
            .summary {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            table {{
                width: 100%;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .audio-path {{
                font-family: monospace;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/untranscribed" class="back-btn">← Back</a>
            
            <div class="header">
                <h1>🔍 Untranscribed Calls - Loan #{loan_number}</h1>
                <button class="download-btn" onclick="downloadQueue()">Download Queue File</button>
            </div>
            
            <div class="summary">
                <p><strong>Total untranscribed:</strong> {len(calls)} calls</p>
                <p><strong>Total duration:</strong> {sum(c['duration'] for c in calls) / 60:.1f} minutes</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Call ID</th>
                        <th>Date/Time</th>
                        <th>Duration</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Audio File Path</th>
                    </tr>
                </thead>
                <tbody>
                    {call_rows}
                </tbody>
            </table>
        </div>
        
        <script>
            function downloadQueue() {{
                const content = `{queue_content_escaped}`;
                const blob = new Blob([content], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'transcribe_queue_loan_{loan_number}.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/add-call", response_class=HTMLResponse)
async def add_call_page(loan: str = None):
    """Add missing call page"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Missing Call</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
            }}
            .form-group {{
                margin: 20px 0;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
                color: #2c3e50;
                font-weight: 500;
            }}
            input {{
                width: 100%;
                padding: 10px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }}
            input:focus {{
                border-color: #3498db;
                outline: none;
            }}
            .btn {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                margin-top: 20px;
            }}
            .btn:hover {{
                background: #229954;
            }}
            .back-btn {{
                background: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
            }}
            .back-btn:hover {{
                background: #7f8c8d;
            }}
            .info {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                color: #1976d2;
            }}
            .result {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }}
            .result.success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .result.error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Back to Home</a>
            <h1>➕ Add Missing Call</h1>
            
            <div class="info">
                Add a call that should be part of a loan's timeline. This is useful for broker transfers that may not have been tagged with the loan number.
            </div>
            
            <div class="form-group">
                <label for="loanNumber">Loan Number</label>
                <input type="text" id="loanNumber" placeholder="e.g., 1225237672" value="{loan or ''}">
            </div>
            
            <div class="form-group">
                <label for="orkuid">Call ID (orkUid)</label>
                <input type="text" id="orkuid" placeholder="e.g., 20250612_125406_UVCT">
            </div>
            
            <button class="btn" onclick="addCall()">Add Call to Loan</button>
            
            <div id="result" class="result"></div>
        </div>
        
        <script>
            async function addCall() {{
                const loanNumber = document.getElementById('loanNumber').value.trim();
                const orkuid = document.getElementById('orkuid').value.trim();
                
                if (!loanNumber || !orkuid) {{
                    alert('Please fill in both fields');
                    return;
                }}
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'none';
                
                try {{
                    const response = await fetch('/api/add-call', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            loan_number: loanNumber,
                            orkuid: orkuid
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        resultDiv.className = 'result success';
                        resultDiv.innerHTML = `
                            <strong>✅ Success!</strong><br>
                            Call ${{orkuid}} has been added to loan ${{loanNumber}}.<br>
                            <a href="/timeline/${{loanNumber}}">View Updated Timeline</a>
                        `;
                    }} else {{
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = `<strong>❌ Error:</strong> ${{result.error}}`;
                    }}
                    
                    resultDiv.style.display = 'block';
                    
                }} catch (error) {{
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<strong>❌ Error:</strong> ${{error.message}}`;
                    resultDiv.style.display = 'block';
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.post("/api/feedback")
async def save_feedback(data: dict):
    """Save feedback about a call"""
    call_id = data.get('call_id')
    feedback_type = data.get('type')
    correct_loan = data.get('correct_loan')
    
    feedback_data[call_id] = {
        'type': feedback_type,
        'correct_loan': correct_loan,
        'timestamp': datetime.now().isoformat()
    }
    
    return JSONResponse({"status": "success"})

@app.post("/api/add-call")
async def api_add_call(data: dict):
    """Add missing call to loan"""
    loan_number = data.get('loan_number')
    orkuid = data.get('orkuid')
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    try:
        # Check if call exists
        cursor.execute("SELECT * FROM orktape WHERE orkUid = %s", (orkuid,))
        if not cursor.fetchone():
            return JSONResponse({"success": False, "error": "Call not found in database"})
        
        # Check existing assignments
        cursor.execute("SELECT loan_numbers FROM call_transcripts_v2 WHERE orkuid = %s", (orkuid,))
        existing = cursor.fetchone()
        
        current_loans = []
        if existing and existing.get('loan_numbers'):
            current_loans = json.loads(existing['loan_numbers'])
        
        if loan_number not in current_loans:
            current_loans.append(loan_number)
            new_json = json.dumps(current_loans)
            
            if existing:
                cursor.execute("""
                    UPDATE call_transcripts_v2 
                    SET loan_numbers = %s, updated_at = NOW()
                    WHERE orkuid = %s
                """, (new_json, orkuid))
            else:
                cursor.execute("""
                    INSERT INTO call_transcripts_v2 (orkuid, loan_numbers, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (orkuid, new_json))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        cursor.close()
        conn.close()
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics():
    """Loan analytics page"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get loan activity stats
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT loan_numbers) as total_loans,
            COUNT(*) as total_calls,
            AVG(call_count) as avg_calls_per_loan,
            MAX(call_count) as max_calls
        FROM (
            SELECT loan_numbers, COUNT(*) as call_count
            FROM call_transcripts_v2
            WHERE loan_numbers != '[]'
            GROUP BY loan_numbers
        ) as loan_stats
    """)
    
    stats = cursor.fetchone()
    
    # Get most active loans
    cursor.execute("""
        SELECT 
            loan_numbers,
            COUNT(*) as call_count,
            MIN(t.timestamp) as first_call,
            MAX(t.timestamp) as last_call,
            SUM(t.duration) as total_duration
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY call_count DESC
        LIMIT 20
    """)
    
    active_loans = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Build loan rows
    loan_rows = ""
    for row in active_loans:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:
                days = (row['last_call'] - row['first_call']).days
                loan_rows += f'''
                <tr>
                    <td><a href="/timeline/{loan}">{loan}</a></td>
                    <td>{row['call_count']}</td>
                    <td>{days}</td>
                    <td>{row['total_duration'] / 60:.1f}</td>
                    <td>{row['first_call'].strftime('%m/%d/%Y')}</td>
                    <td>{row['last_call'].strftime('%m/%d/%Y')}</td>
                </tr>
                '''
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Analytics</title>
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
            .header {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            h1 {{
                margin: 0;
                color: #2c3e50;
            }}
            .back-btn {{
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 20px;
            }}
            .back-btn:hover {{
                background: #2980b9;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat-value {{
                font-size: 36px;
                font-weight: bold;
                color: #3498db;
            }}
            .stat-label {{
                color: #7f8c8d;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Back to Home</a>
            
            <div class="header">
                <h1>📈 Loan Analytics</h1>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{stats['total_loans'] or 0}</div>
                    <div class="stat-label">Total Loans</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['total_calls'] or 0}</div>
                    <div class="stat-label">Total Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['avg_calls_per_loan'] or 0:.1f}</div>
                    <div class="stat-label">Avg Calls/Loan</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['max_calls'] or 0}</div>
                    <div class="stat-label">Max Calls</div>
                </div>
            </div>
            
            <h2>Most Active Loans</h2>
            <table>
                <thead>
                    <tr>
                        <th>Loan Number</th>
                        <th>Total Calls</th>
                        <th>Journey Days</th>
                        <th>Total Minutes</th>
                        <th>First Call</th>
                        <th>Last Call</th>
                    </tr>
                </thead>
                <tbody>
                    {loan_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting Loan Master App...")
    print("Open: http://localhost:8006")
    print("\nAll features available on one port!")
    print("\nAvailable routes:")
    print("  /                    - Home with all features")
    print("  /timeline            - Loan timeline with feedback")
    print("  /timeline/<loan>     - Specific loan timeline")
    print("  /broker-tracker      - Track broker activity")
    print("  /brief-generator     - Generate loan briefs")
    print("  /untranscribed       - Find untranscribed calls")
    print("  /add-call            - Add missing calls")
    print("  /analytics           - Loan analytics")
    
    uvicorn.run(app, host="0.0.0.0", port=8006)