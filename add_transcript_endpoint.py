#!/usr/bin/env python3
"""
Add this endpoint to loan_search_api.py to serve transcript files
"""

print("""
Add this endpoint to loan_search_api.py:

@app.get("/transcript/{orkuid}")
def get_transcript(orkuid: str):
    \"\"\"Get the full transcript text for a recording\"\"\"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get transcript path
        cursor.execute(\"\"\"
            SELECT transcript_path
            FROM call_transcripts_v2
            WHERE orkuid = %s
        \"\"\", (orkuid,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result or not result['transcript_path']:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Read transcript file
        transcript_path = result['transcript_path']
        
        # Try Windows path if needed
        if not os.path.exists(transcript_path) and '/' in transcript_path:
            transcript_path = transcript_path.replace('/', '\\\\')
        
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "orkuid": orkuid,
                "content": content,
                "path": transcript_path
            }
        else:
            raise HTTPException(status_code=404, detail="Transcript file not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

""")