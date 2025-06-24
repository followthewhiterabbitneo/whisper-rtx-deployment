#!/usr/bin/env python3
"""
Create visual network graphs and timelines for loan relationships
Generates HTML files with interactive visualizations
FIXED for Windows encoding issues
"""

import pymysql
import json
from datetime import datetime
import os

DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

def generate_network_visualization(loan_number):
    """Generate interactive network graph for a loan"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get all calls for this loan
    cursor.execute("""
        SELECT 
            ct.orkuid,
            ct.loan_numbers,
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
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    
    # Build network data
    nodes = {}
    edges = []
    
    for call in calls:
        # Add nodes
        if call['localParty'] not in nodes:
            nodes[call['localParty']] = {
                'id': call['localParty'],
                'label': call['localParty'],
                'type': 'phone',
                'calls': 0
            }
        if call['remoteParty'] not in nodes:
            nodes[call['remoteParty']] = {
                'id': call['remoteParty'],
                'label': call['remoteParty'],
                'type': 'phone',
                'calls': 0
            }
        
        # Update call counts
        nodes[call['localParty']]['calls'] += 1
        nodes[call['remoteParty']]['calls'] += 1
        
        # Add edge
        edges.append({
            'source': call['localParty'],
            'target': call['remoteParty'],
            'timestamp': call['timestamp'].strftime('%Y-%m-%d %H:%M'),
            'duration': call['duration'],
            'orkuid': call['orkuid']
        })
    
    # Generate HTML with D3.js visualization
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Loan #{loan_number} Network Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        #network {{
            width: 100%;
            height: 600px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .node {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        .node-label {{
            font-size: 12px;
            pointer-events: none;
        }}
        #timeline {{
            width: 100%;
            height: 200px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .timeline-item {{
            display: inline-block;
            margin: 10px;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>Loan #{loan_number} Network Visualization</h1>
    
    <div class="stats">
        <h3>Network Statistics</h3>
        <p>Total Calls: {len(calls)}</p>
        <p>Unique Phone Numbers: {len(nodes)}</p>
        <p>Date Range: {calls[0]['timestamp'].strftime('%Y-%m-%d')} to {calls[-1]['timestamp'].strftime('%Y-%m-%d') if len(calls) > 1 else calls[0]['timestamp'].strftime('%Y-%m-%d')}</p>
        <p>Total Duration: {sum(c['duration'] for c in calls) / 60:.1f} minutes</p>
    </div>
    
    <h2>Network Graph</h2>
    <div id="network"></div>
    
    <h2>Timeline</h2>
    <div id="timeline">
        {"".join(f'''
        <div class="timeline-item">
            <strong>{call['timestamp'].strftime('%Y-%m-%d %H:%M')}</strong><br>
            {call['localParty']} &lt;-&gt; {call['remoteParty']}<br>
            Duration: {call['duration']}s<br>
            <small>{call['orkuid']}</small>
        </div>
        ''' for call in calls)}
    </div>
    
    <script>
        // Network data
        const nodes = {json.dumps(list(nodes.values()))};
        const links = {json.dumps(edges)};
        
        // Set up SVG
        const width = document.getElementById('network').offsetWidth;
        const height = 600;
        
        const svg = d3.select("#network")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        // Add links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.sqrt(d.duration / 60));
        
        // Add nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => 10 + Math.sqrt(d.calls) * 3)
            .attr("fill", d => d.calls > 5 ? "#f44336" : "#2196F3")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add labels
        const label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .attr("class", "node-label")
            .text(d => d.label)
            .attr("text-anchor", "middle")
            .attr("dy", -15);
        
        // Add titles
        node.append("title")
            .text(d => d.label + " (" + d.calls + " calls)");
        
        link.append("title")
            .text(d => d.source.id + " <-> " + d.target.id + " (" + d.duration + "s)");
        
        // Update positions
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
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
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
"""
    
    # Save HTML file with UTF-8 encoding
    filename = f"loan_network_{loan_number}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    cursor.close()
    conn.close()
    
    return filename

def generate_timeline_chart(loan_number):
    """Generate a visual timeline chart"""
    
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    # Get timeline data
    cursor.execute("""
        SELECT 
            t.timestamp,
            t.duration,
            t.localParty,
            t.remoteParty,
            ct.loan_numbers,
            COALESCE(CONCAT(u.firstname, ' ', u.lastname), 'Unknown') as user_name
        FROM call_transcripts_v2 ct
        JOIN orktape t ON ct.orkuid = t.orkUid
        LEFT JOIN orksegment s ON t.id = s.tape_id
        LEFT JOIN orkuser u ON s.user_id = u.id
        WHERE ct.loan_numbers LIKE %s
        ORDER BY t.timestamp
    """, (f'%{loan_number}%',))
    
    calls = cursor.fetchall()
    
    # Generate timeline HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Loan #{loan_number} Timeline</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        #timeline {{
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Loan #{loan_number} Call Timeline</h1>
        <canvas id="timeline" width="400" height="200"></canvas>
    </div>
    
    <script>
        const ctx = document.getElementById('timeline').getContext('2d');
        
        const data = {{
            labels: {json.dumps([c['timestamp'].strftime('%Y-%m-%d %H:%M') for c in calls])},
            datasets: [{{
                label: 'Call Duration (seconds)',
                data: {json.dumps([c['duration'] for c in calls])},
                backgroundColor: 'rgba(33, 150, 243, 0.5)',
                borderColor: 'rgba(33, 150, 243, 1)',
                borderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }}]
        }};
        
        const config = {{
            type: 'line',
            data: data,
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Call Duration Over Time'
                    }},
                    tooltip: {{
                        callbacks: {{
                            afterLabel: function(context) {{
                                const calls = {json.dumps([{{
                                    'parties': f"{c['localParty']} <-> {c['remoteParty']}",
                                    'user': c['user_name']
                                }} for c in calls])};
                                return [
                                    'Parties: ' + calls[context.dataIndex].parties,
                                    'User: ' + calls[context.dataIndex].user
                                ];
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Duration (seconds)'
                        }}
                    }}
                }}
            }}
        }};
        
        new Chart(ctx, config);
    </script>
</body>
</html>
"""
    
    filename = f"loan_timeline_{loan_number}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    cursor.close()
    conn.close()
    
    return filename

def main():
    print("LOAN VISUALIZATION GENERATOR")
    print("="*50)
    
    loan_number = input("Enter loan number to visualize: ")
    
    print(f"\nGenerating visualizations for loan {loan_number}...")
    
    # Generate network graph
    network_file = generate_network_visualization(loan_number)
    print(f"✅ Network graph saved to: {network_file}")
    
    # Generate timeline chart
    timeline_file = generate_timeline_chart(loan_number)
    print(f"✅ Timeline chart saved to: {timeline_file}")
    
    print(f"\nOpen these files in your browser to view:")
    print(f"  - {network_file}")
    print(f"  - {timeline_file}")

if __name__ == "__main__":
    main()