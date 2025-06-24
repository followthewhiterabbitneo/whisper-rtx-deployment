#!/usr/bin/env python3
"""
LOAN NETWORK VISUALIZATION - Real data science visualization
Loan ID in the center, expanding network outward
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymysql
import json
import uvicorn

app = FastAPI(title="Loan Network Visualization")

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
    """List loans to visualize"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT loan_numbers, COUNT(*) as count
        FROM call_transcripts_v2
        WHERE loan_numbers != '[]'
        GROUP BY loan_numbers
        ORDER BY count DESC
        LIMIT 30
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Extract loans
    loan_list = ""
    for row in rows:
        try:
            loans = json.loads(row['loan_numbers'])
            for loan in loans[:1]:  # First loan from each group
                loan_list += f'''
                <div class="loan-card" onclick="window.location.href='/network/{loan}'">
                    <h3>Loan #{loan}</h3>
                    <p>{row['count']} direct mentions</p>
                    <p>Click to view network →</p>
                </div>
                '''
        except:
            pass
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan Network Visualization</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
            }}
            h1 {{
                text-align: center;
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
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
                background: #2a2a2a;
                border: 1px solid #00ff00;
                padding: 20px;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .loan-card:hover {{
                transform: scale(1.05);
                box-shadow: 0 0 20px #00ff00;
                background: #3a3a3a;
            }}
            .loan-card h3 {{
                color: #00ff00;
                margin: 0 0 10px 0;
            }}
            .loan-card p {{
                margin: 5px 0;
                color: #ccc;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌐 LOAN NETWORK VISUALIZATION</h1>
            <p style="text-align: center; color: #ccc;">Select a loan to see its network</p>
            <div class="loan-grid">
                {loan_list}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/network/{loan_number}", response_class=HTMLResponse)
async def show_network(loan_number: str):
    """Show the network visualization for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all calls for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.transcript_path,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    direct_calls = cursor.fetchall()
    
    # Find loan officer (most common party)
    parties = {}
    for call in direct_calls:
        for party in [call['localParty'], call['remoteParty']]:
            parties[party] = parties.get(party, 0) + 1
    
    loan_officer = max(parties, key=parties.get) if parties else None
    
    # Get extended network if loan officer found
    network_calls = direct_calls
    if loan_officer:
        cursor.execute("""
            SELECT 
                t.orkUid,
                t.timestamp,
                t.duration,
                t.localParty,
                t.remoteParty,
                ct.transcript_path,
                ct.loan_numbers,
                COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
            FROM orktape t
            LEFT JOIN call_transcripts_v2 ct ON t.orkUid = ct.orkuid
            LEFT JOIN orksegment s ON t.id = s.tape_id
            LEFT JOIN orkuser u ON s.user_id = u.id
            WHERE (t.localParty = %s OR t.remoteParty = %s)
            AND t.timestamp >= DATE_SUB((SELECT MIN(timestamp) FROM orktape t2 
                                       JOIN call_transcripts_v2 ct2 ON t2.orkUid = ct2.orkuid
                                       WHERE ct2.loan_numbers LIKE %s), INTERVAL 30 DAY)
            AND t.timestamp <= DATE_ADD((SELECT MAX(timestamp) FROM orktape t2 
                                       JOIN call_transcripts_v2 ct2 ON t2.orkUid = ct2.orkuid
                                       WHERE ct2.loan_numbers LIKE %s), INTERVAL 30 DAY)
            ORDER BY t.timestamp
        """, (loan_officer, loan_officer, f'%{loan_number}%', f'%{loan_number}%'))
        
        network_calls = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Build nodes and links for visualization
    nodes = []
    links = []
    
    # Add loan as center node
    nodes.append({
        'id': f'loan_{loan_number}',
        'label': f'LOAN\\n{loan_number}',
        'x': 400,
        'y': 300,
        'type': 'loan',
        'fixed': True
    })
    
    # Track unique parties
    party_nodes = {}
    
    for idx, call in enumerate(network_calls):
        # Add party nodes if not exists
        for party in [call['localParty'], call['remoteParty']]:
            if party not in party_nodes:
                party_nodes[party] = {
                    'id': party,
                    'label': party,
                    'type': 'loan_officer' if party == loan_officer else 'party',
                    'calls': 0
                }
        
        # Update call counts
        party_nodes[call['localParty']]['calls'] += 1
        party_nodes[call['remoteParty']]['calls'] += 1
        
        # Check if this call mentions the loan
        has_loan = False
        if call.get('loan_numbers'):
            try:
                loans = json.loads(call['loan_numbers'])
                has_loan = loan_number in loans
            except:
                pass
        
        # Add link from loan to parties if mentions loan
        if has_loan:
            links.append({
                'source': f'loan_{loan_number}',
                'target': call['remoteParty'],
                'type': 'direct',
                'call_id': call['orkUid']
            })
    
    # Add party nodes
    nodes.extend(party_nodes.values())
    
    # Add inter-party links
    for call in network_calls:
        links.append({
            'source': call['localParty'],
            'target': call['remoteParty'],
            'type': 'call',
            'duration': call['duration']
        })
    
    # Build call details table
    call_rows = ""
    for call in network_calls:
        has_loan = "✓" if call.get('loan_numbers') and loan_number in json.loads(call.get('loan_numbers', '[]')) else ""
        call_rows += f"""
        <tr>
            <td>{call['orkUid']}</td>
            <td>{call['timestamp']}</td>
            <td>{call['duration']}s</td>
            <td>{call['localParty']}</td>
            <td>{call['remoteParty']}</td>
            <td>{has_loan}</td>
            <td>{call.get('transcript_path', '') or ''}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loan {loan_number} Network</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                background: #1a1a1a;
                color: #fff;
            }}
            .header {{
                background: #000;
                padding: 20px;
                text-align: center;
                border-bottom: 2px solid #00ff00;
            }}
            h1 {{
                color: #00ff00;
                margin: 0;
                text-shadow: 0 0 20px #00ff00;
            }}
            #network {{
                width: 100%;
                height: 600px;
                background: #0a0a0a;
                position: relative;
            }}
            .stats {{
                padding: 20px;
                background: #2a2a2a;
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
            }}
            .stat-box {{
                background: #1a1a1a;
                padding: 15px;
                border: 1px solid #00ff00;
                border-radius: 5px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 2em;
                color: #00ff00;
            }}
            .details {{
                padding: 20px;
                max-height: 400px;
                overflow-y: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #2a2a2a;
            }}
            th, td {{
                border: 1px solid #444;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background: #1a1a1a;
                color: #00ff00;
            }}
            tr:hover {{
                background: #3a3a3a;
            }}
            .back {{
                position: absolute;
                top: 20px;
                left: 20px;
                color: #00ff00;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <a href="/" class="back">← Back</a>
        
        <div class="header">
            <h1>LOAN #{loan_number} NETWORK</h1>
            <p>Network Visualization</p>
        </div>
        
        <div id="network"></div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(direct_calls)}</div>
                <div>Direct Mentions</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(network_calls)}</div>
                <div>Total Network Calls</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(party_nodes)}</div>
                <div>Unique Parties</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(c['duration'] for c in network_calls) / 60:.1f}m</div>
                <div>Total Duration</div>
            </div>
        </div>
        
        <div class="details">
            <h2 style="color: #00ff00;">Network Calls</h2>
            <table>
                <tr>
                    <th>Call ID</th>
                    <th>Timestamp</th>
                    <th>Duration</th>
                    <th>From</th>
                    <th>To</th>
                    <th>Has Loan</th>
                    <th>Transcript Path</th>
                </tr>
                {call_rows}
            </table>
        </div>
        
        <script>
            const width = window.innerWidth;
            const height = 600;
            
            const nodes = {json.dumps(nodes)};
            const links = {json.dumps(links)};
            
            const svg = d3.select("#network")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
            
            // Add zoom
            const g = svg.append("g");
            
            svg.call(d3.zoom()
                .scaleExtent([0.1, 10])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                }}));
            
            // Create force simulation
            const simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(150))
                .force("charge", d3.forceManyBody().strength(-500))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            // Add links
            const link = g.append("g")
                .selectAll("line")
                .data(links)
                .enter().append("line")
                .style("stroke", d => d.type === 'direct' ? "#00ff00" : "#444")
                .style("stroke-width", d => d.type === 'direct' ? 3 : 1)
                .style("stroke-dasharray", d => d.type === 'direct' ? "0" : "5,5");
            
            // Add nodes
            const node = g.append("g")
                .selectAll("g")
                .data(nodes)
                .enter().append("g")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Add circles
            node.append("circle")
                .attr("r", d => {{
                    if (d.type === 'loan') return 40;
                    if (d.type === 'loan_officer') return 20;
                    return 10 + Math.sqrt(d.calls || 1) * 2;
                }})
                .style("fill", d => {{
                    if (d.type === 'loan') return "#00ff00";
                    if (d.type === 'loan_officer') return "#ff6600";
                    return "#0099ff";
                }})
                .style("stroke", "#fff")
                .style("stroke-width", 2);
            
            // Add labels
            node.append("text")
                .text(d => d.label)
                .style("fill", "#fff")
                .style("font-size", d => d.type === 'loan' ? "16px" : "10px")
                .style("text-anchor", "middle")
                .style("dominant-baseline", "central");
            
            // Add glow effect to loan node
            node.filter(d => d.type === 'loan')
                .append("circle")
                .attr("r", 45)
                .style("fill", "none")
                .style("stroke", "#00ff00")
                .style("stroke-width", 2)
                .style("opacity", 0.5)
                .style("filter", "blur(10px)");
            
            // Update positions
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});
            
            // Drag functions
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                if (d.type !== 'loan') {{
                    d.fx = null;
                    d.fy = null;
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

if __name__ == "__main__":
    print("Starting Loan Network Visualization...")
    print("Open: http://localhost:8000")
    print("\nReal data science visualization!")
    uvicorn.run(app, host="0.0.0.0", port=8000)