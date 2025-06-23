#!/usr/bin/env python3
"""
Loan Timeline API - Aggregates all transcripts for a loan number
Creates a comprehensive timeline with AI-powered summary
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import pymysql
import json
from datetime import datetime, date
import re
from collections import defaultdict

app = FastAPI(title="Loan Timeline API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': 's40vpsoxweb002',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Pydantic models
class TimelineEvent(BaseModel):
    orkuid: str
    timestamp: datetime
    duration: int
    user_name: Optional[str]
    summary: str
    key_facts: Dict
    sentiment: Optional[str]
    loan_mentions: int
    
class LoanTimeline(BaseModel):
    loan_number: str
    total_calls: int
    total_duration_minutes: int
    first_contact: datetime
    last_contact: datetime
    primary_user: Optional[str]
    timeline_events: List[TimelineEvent]
    aggregated_summary: str
    key_milestones: List[Dict]
    sentiment_trend: Dict[str, int]

class LoanInsights(BaseModel):
    loan_number: str
    loan_status: str
    key_issues: List[str]
    action_items: List[str]
    risk_indicators: List[str]
    compliance_notes: List[str]

def get_db_connection():
    """Get database connection"""
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

@app.get("/timeline/{loan_number}", response_model=LoanTimeline)
async def get_loan_timeline(loan_number: str):
    """Get complete timeline for a loan number"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all calls for this loan
        cursor.execute("""
            SELECT 
                l.orkuid,
                l.call_timestamp as timestamp,
                l.duration,
                l.user_name,
                ct.summary,
                ct.key_facts,
                ct.sentiment,
                ct.loan_numbers,
                t.localParty,
                t.remoteParty
            FROM loan_number_index l
            JOIN call_transcripts_v2 ct ON l.orkuid = ct.orkuid
            JOIN orktape t ON l.orkuid = t.orkUid
            WHERE l.loan_number = %s
            ORDER BY l.call_timestamp ASC
        """, (loan_number,))
        
        calls = cursor.fetchall()
        
        if not calls:
            raise HTTPException(status_code=404, detail="No calls found for this loan number")
        
        # Process timeline events
        timeline_events = []
        sentiment_counts = defaultdict(int)
        all_summaries = []
        total_duration = 0
        
        for call in calls:
            # Parse JSON fields
            key_facts = json.loads(call['key_facts']) if call['key_facts'] else {}
            loan_numbers = json.loads(call['loan_numbers']) if call['loan_numbers'] else []
            
            # Count loan mentions
            loan_mentions = loan_numbers.count(loan_number) if loan_numbers else 0
            
            # Create timeline event
            event = TimelineEvent(
                orkuid=call['orkuid'],
                timestamp=call['timestamp'],
                duration=call['duration'],
                user_name=call['user_name'],
                summary=call['summary'] or "No summary available",
                key_facts=key_facts,
                sentiment=call['sentiment'],
                loan_mentions=loan_mentions
            )
            timeline_events.append(event)
            
            # Aggregate data
            if call['sentiment']:
                sentiment_counts[call['sentiment']] += 1
            all_summaries.append(call['summary'] or "")
            total_duration += call['duration']
        
        # Determine primary user (most frequent)
        user_counts = defaultdict(int)
        for call in calls:
            if call['user_name']:
                user_counts[call['user_name']] += 1
        primary_user = max(user_counts, key=user_counts.get) if user_counts else None
        
        # Generate aggregated summary
        aggregated_summary = generate_timeline_summary(
            loan_number, 
            timeline_events,
            all_summaries
        )
        
        # Extract key milestones
        key_milestones = extract_milestones(timeline_events, all_summaries)
        
        # Create timeline response
        timeline = LoanTimeline(
            loan_number=loan_number,
            total_calls=len(calls),
            total_duration_minutes=total_duration // 60,
            first_contact=calls[0]['timestamp'],
            last_contact=calls[-1]['timestamp'],
            primary_user=primary_user,
            timeline_events=timeline_events,
            aggregated_summary=aggregated_summary,
            key_milestones=key_milestones,
            sentiment_trend=dict(sentiment_counts)
        )
        
        cursor.close()
        conn.close()
        
        return timeline
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/{loan_number}", response_model=LoanInsights)
async def get_loan_insights(loan_number: str):
    """Get AI-powered insights for a loan"""
    try:
        # First get the timeline
        timeline = await get_loan_timeline(loan_number)
        
        # Analyze for insights
        insights = analyze_loan_timeline(timeline)
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_timeline_summary(loan_number: str, events: List[TimelineEvent], summaries: List[str]) -> str:
    """Generate an aggregated summary of the entire loan timeline"""
    
    # Combine all summaries
    combined_text = " ".join(summaries)
    
    # Extract key themes
    themes = extract_themes(combined_text)
    
    # Build timeline summary
    summary_parts = [
        f"Loan #{loan_number} Timeline Summary:",
        f"",
        f"This loan has been discussed in {len(events)} calls spanning from {events[0].timestamp.strftime('%B %d, %Y')} to {events[-1].timestamp.strftime('%B %d, %Y')}."
    ]
    
    # Add sentiment analysis
    sentiments = [e.sentiment for e in events if e.sentiment]
    if sentiments:
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        if positive > negative:
            summary_parts.append(f"Overall sentiment has been predominantly positive ({positive}/{len(sentiments)} calls).")
        elif negative > positive:
            summary_parts.append(f"There have been concerns raised in {negative} out of {len(sentiments)} calls.")
    
    # Add key themes
    if themes:
        summary_parts.append(f"\nKey topics discussed: {', '.join(themes[:5])}.")
    
    # Look for resolution patterns
    if "resolved" in combined_text.lower() or "approved" in combined_text.lower():
        summary_parts.append("\nPositive outcomes have been noted in recent communications.")
    
    return " ".join(summary_parts)

def extract_milestones(events: List[TimelineEvent], summaries: List[str]) -> List[Dict]:
    """Extract key milestones from the timeline"""
    milestones = []
    
    # Keywords that indicate milestones
    milestone_keywords = {
        'approved': 'Approval',
        'denied': 'Denial',
        'submitted': 'Submission',
        'received': 'Receipt',
        'completed': 'Completion',
        'payment': 'Payment',
        'deferral': 'Deferral',
        'modification': 'Modification',
        'escalated': 'Escalation',
        'resolved': 'Resolution'
    }
    
    for i, (event, summary) in enumerate(zip(events, summaries)):
        summary_lower = summary.lower()
        
        for keyword, milestone_type in milestone_keywords.items():
            if keyword in summary_lower:
                # Extract context around keyword
                context = extract_context(summary, keyword, 50)
                
                milestones.append({
                    'date': event.timestamp.isoformat(),
                    'type': milestone_type,
                    'description': context,
                    'orkuid': event.orkuid,
                    'sentiment': event.sentiment
                })
                break
    
    return sorted(milestones, key=lambda x: x['date'])

def extract_themes(text: str) -> List[str]:
    """Extract key themes from combined text"""
    # Simple theme extraction - in production, use NLP
    themes = []
    
    theme_patterns = {
        'payment': r'\b(payment|pay|paid|paying|installment)\b',
        'deferral': r'\b(defer|deferral|postpone|delay)\b',
        'hardship': r'\b(hardship|difficult|struggle|unable)\b',
        'documentation': r'\b(document|paperwork|form|submit)\b',
        'approval': r'\b(approve|approved|approval|accept)\b',
        'modification': r'\b(modify|modification|change|adjust)\b',
        'employment': r'\b(job|employment|work|income)\b',
        'covid': r'\b(covid|pandemic|coronavirus)\b'
    }
    
    text_lower = text.lower()
    
    for theme, pattern in theme_patterns.items():
        if re.search(pattern, text_lower):
            themes.append(theme)
    
    return themes

def extract_context(text: str, keyword: str, context_length: int = 50) -> str:
    """Extract context around a keyword"""
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    pos = text_lower.find(keyword_lower)
    if pos == -1:
        return text[:100] + "..."
    
    start = max(0, pos - context_length)
    end = min(len(text), pos + len(keyword) + context_length)
    
    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
    
    return context.strip()

def analyze_loan_timeline(timeline: LoanTimeline) -> LoanInsights:
    """Analyze timeline to generate insights"""
    
    # Determine loan status based on timeline
    loan_status = "Active"
    if "resolved" in timeline.aggregated_summary.lower():
        loan_status = "Resolved"
    elif "denied" in timeline.aggregated_summary.lower():
        loan_status = "Denied"
    elif timeline.sentiment_trend.get('negative', 0) > timeline.sentiment_trend.get('positive', 0):
        loan_status = "At Risk"
    
    # Extract issues from negative sentiment calls
    key_issues = []
    action_items = []
    risk_indicators = []
    compliance_notes = []
    
    for event in timeline.timeline_events:
        if event.sentiment == 'negative':
            # This is simplified - in production, use NLP
            if 'payment' in event.summary.lower():
                key_issues.append("Payment difficulties")
            if 'employment' in event.summary.lower():
                key_issues.append("Employment changes")
        
        # Extract action items (simplified)
        if 'need' in event.summary.lower() or 'require' in event.summary.lower():
            action_items.append(f"Follow-up required from {event.timestamp.strftime('%m/%d')}")
    
    # Risk indicators
    if timeline.total_calls > 5:
        risk_indicators.append("High call volume indicates ongoing issues")
    if timeline.sentiment_trend.get('negative', 0) > 2:
        risk_indicators.append("Multiple negative interactions")
    
    # Compliance notes
    if timeline.total_duration_minutes > 300:
        compliance_notes.append("Extended communication history documented")
    
    return LoanInsights(
        loan_number=timeline.loan_number,
        loan_status=loan_status,
        key_issues=list(set(key_issues)),
        action_items=action_items[:5],  # Top 5
        risk_indicators=risk_indicators,
        compliance_notes=compliance_notes
    )

# Additional endpoints for the React dashboard

@app.get("/timeline/{loan_number}/export")
async def export_timeline(loan_number: str, format: str = "json"):
    """Export timeline in various formats"""
    timeline = await get_loan_timeline(loan_number)
    
    if format == "csv":
        # Convert to CSV format
        csv_data = "Date,Time,Duration,User,Summary,Sentiment\n"
        for event in timeline.timeline_events:
            csv_data += f"{event.timestamp.date()},{event.timestamp.time()},{event.duration},{event.user_name or 'Unknown'},{event.summary[:50]}...,{event.sentiment}\n"
        
        return {"content": csv_data, "filename": f"loan_{loan_number}_timeline.csv"}
    
    return timeline

@app.get("/search/timeline")
async def search_timelines(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_calls: int = 1,
    sentiment: Optional[str] = None
):
    """Search for loans matching criteria"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                loan_number,
                COUNT(DISTINCT orkuid) as call_count,
                MIN(call_timestamp) as first_call,
                MAX(call_timestamp) as last_call,
                SUM(duration) as total_duration
            FROM loan_number_index
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND call_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND call_date <= %s"
            params.append(end_date)
            
        query += " GROUP BY loan_number HAVING call_count >= %s"
        params.append(min_calls)
        
        query += " ORDER BY call_count DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Loan Timeline API...")
    print("Timeline endpoint: http://localhost:8001/timeline/{loan_number}")
    print("Insights endpoint: http://localhost:8001/insights/{loan_number}")
    uvicorn.run(app, host="0.0.0.0", port=8001)