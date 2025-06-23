#!/usr/bin/env python3
"""
SCREAM Pipeline with Hybrid Storage
Processes recordings: Transcribe -> Summarize -> Store (DB + Filesystem)
Runs on RTX 4090 with local models
"""

import os
import sys
import json
import time
import re
import pymysql
from datetime import datetime
from pathlib import Path
from faster_whisper import WhisperModel

print("=" * 80)
print("SCREAM HYBRID PIPELINE")
print("=" * 80)

# Configuration
DB_CONFIG = {
    'host': 's01vdsoxweb047',
    'port': 3306,
    'user': 'root',
    'password': 'admin',
    'database': 'oreka',
    'charset': 'utf8mb4'
}

# Paths
WHISPER_MODEL_PATH = "models/faster-whisper-large-v3-turbo-ct2"
GEMMA_MODEL_PATH = "models/gemma-3-12b-it-qat-q4_0/gemma-3-12b-it-qat-q4_0.gguf"
TRANSCRIPT_BASE_PATH = "C:/transcripts"  # Windows path on RTX

# Ensure transcript directory exists
os.makedirs(TRANSCRIPT_BASE_PATH, exist_ok=True)

class ScreamPipeline:
    def __init__(self):
        """Initialize models and database connection"""
        print("\n1. Initializing Pipeline...")
        
        # Load Whisper
        print("   Loading Whisper model...")
        self.whisper_model = WhisperModel(
            WHISPER_MODEL_PATH, 
            device="cuda", 
            compute_type="int8_float16"
        )
        print("   ✓ Whisper loaded")
        
        # Load Gemma (lazy load when needed)
        self.gemma_model = None
        
        # Database connection
        print("   Connecting to database...")
        self.db_conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.db_conn.cursor(pymysql.cursors.DictCursor)
        print("   ✓ Database connected")
        
    def load_gemma(self):
        """Load Gemma model for summaries (only when needed)"""
        if self.gemma_model is None:
            print("   Loading Gemma model for summaries...")
            from llama_cpp import Llama
            self.gemma_model = Llama(
                model_path=GEMMA_MODEL_PATH,
                n_gpu_layers=-1,  # Use all GPU layers
                n_ctx=8192,       # Context window
                n_batch=512,
                n_threads=8,
                verbose=False
            )
            print("   ✓ Gemma loaded")
        return self.gemma_model
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio file using Whisper"""
        print(f"\n2. Transcribing: {os.path.basename(audio_path)}")
        start_time = time.time()
        
        # Transcribe
        segments, info = self.whisper_model.transcribe(audio_path, beam_size=5)
        
        # Collect transcript
        transcript_lines = []
        for segment in segments:
            transcript_lines.append(segment.text.strip())
        
        full_transcript = "\n".join(transcript_lines)
        transcribe_time = (time.time() - start_time) * 1000  # milliseconds
        
        print(f"   ✓ Transcribed in {transcribe_time:.0f}ms")
        print(f"   Duration: {info.duration:.1f}s | Speed: {info.duration/(transcribe_time/1000):.1f}x")
        
        return full_transcript, transcribe_time, info
    
    def extract_loan_numbers(self, text):
        """Extract loan numbers from transcript"""
        loan_patterns = [
            r'loan\s*(?:number)?\s*[:\s]*(\d{8,12})',
            r'application\s*(?:number)?\s*[:\s]*(\d{8,12})',
            r'account\s*(?:number)?\s*[:\s]*(\d{8,12})',
            r'reference\s*(?:number)?\s*[:\s]*(\d{8,12})',
        ]
        
        loan_numbers = set()
        text_lower = text.lower()
        
        for pattern in loan_patterns:
            matches = re.findall(pattern, text_lower)
            loan_numbers.update(matches)
        
        return list(loan_numbers)
    
    def generate_summary(self, transcript):
        """Generate legal brief summary using Gemma"""
        print("\n3. Generating Legal Summary...")
        
        # Load Gemma if not already loaded
        llm = self.load_gemma()
        
        # Truncate transcript if too long
        max_context = 6000  # Leave room for prompt
        if len(transcript) > max_context:
            transcript = transcript[:max_context] + "..."
        
        prompt = f"""<start_of_turn>user
You are a legal assistant creating a brief summary of a mortgage call transcript.

Create a concise legal brief (3-5 sentences) that includes:
1. Caller identification and purpose
2. Key facts (loan numbers, amounts, dates)
3. Actions taken or agreed upon
4. Outcome and any follow-up required

Transcript:
{transcript}

Legal Brief Summary:<end_of_turn>
<start_of_turn>model"""
        
        # Generate summary
        start_time = time.time()
        response = llm(
            prompt,
            max_tokens=300,
            temperature=0.3,
            stop=["<end_of_turn>", "<start_of_turn>"]
        )
        
        summary = response['choices'][0]['text'].strip()
        summary_time = (time.time() - start_time) * 1000
        
        print(f"   ✓ Summary generated in {summary_time:.0f}ms")
        
        return summary, summary_time
    
    def analyze_sentiment(self, transcript, summary):
        """Simple sentiment analysis based on keywords"""
        positive_words = ['thank', 'appreciate', 'helpful', 'resolved', 'satisfied', 
                         'approved', 'great', 'excellent', 'happy']
        negative_words = ['complaint', 'angry', 'frustrated', 'disappointed', 
                         'denied', 'problem', 'issue', 'unhappy', 'escalate']
        
        text = (transcript + " " + summary).lower()
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count + 2:
            return 'positive'
        elif negative_count > positive_count + 2:
            return 'negative'
        else:
            return 'neutral'
    
    def save_transcript_file(self, orkuid, transcript):
        """Save full transcript to filesystem"""
        # Parse orkuid for directory structure
        # Format: YYYYMMDD_HHMMSS_XXXX
        year = orkuid[:4]
        month = orkuid[4:6]
        day = orkuid[6:8]
        hour = orkuid[9:11]
        
        # Create directory path
        dir_path = os.path.join(TRANSCRIPT_BASE_PATH, year, month, day, hour)
        os.makedirs(dir_path, exist_ok=True)
        
        # Save transcript
        file_path = os.path.join(dir_path, f"{orkuid}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # Return relative path for database
        relative_path = f"/{year}/{month}/{day}/{hour}/{orkuid}.txt"
        return relative_path
    
    def save_to_database(self, orkuid, summary, transcript_path, loan_numbers, 
                        key_facts, sentiment, processing_time):
        """Save summary and metadata to database"""
        print("\n4. Saving to Database...")
        
        sql = """
        INSERT INTO call_transcripts_v2 
        (orkuid, summary, transcript_path, loan_numbers, key_facts, 
         sentiment, processing_time_ms, whisper_model, summary_model)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            summary = VALUES(summary),
            transcript_path = VALUES(transcript_path),
            loan_numbers = VALUES(loan_numbers),
            key_facts = VALUES(key_facts),
            sentiment = VALUES(sentiment),
            processing_time_ms = VALUES(processing_time_ms),
            updated_at = CURRENT_TIMESTAMP
        """
        
        self.cursor.execute(sql, (
            orkuid,
            summary,
            transcript_path,
            json.dumps(loan_numbers),
            json.dumps(key_facts),
            sentiment,
            int(processing_time),
            'large-v3-turbo',
            'gemma-3-12b'
        ))
        
        self.db_conn.commit()
        print("   ✓ Saved to database")
    
    def process_recording(self, orkuid, audio_path):
        """Process a single recording through the pipeline"""
        print(f"\n{'='*60}")
        print(f"Processing: {orkuid}")
        print(f"{'='*60}")
        
        total_start = time.time()
        
        try:
            # Step 1: Transcribe
            transcript, transcribe_time, info = self.transcribe_audio(audio_path)
            
            # Step 2: Extract loan numbers
            loan_numbers = self.extract_loan_numbers(transcript)
            print(f"\n   Loan numbers found: {loan_numbers if loan_numbers else 'None'}")
            
            # Step 3: Generate summary
            summary, summary_time = self.generate_summary(transcript)
            
            # Step 4: Analyze sentiment
            sentiment = self.analyze_sentiment(transcript, summary)
            print(f"   Sentiment: {sentiment}")
            
            # Step 5: Save transcript to filesystem
            transcript_path = self.save_transcript_file(orkuid, transcript)
            print(f"\n   Transcript saved: {transcript_path}")
            
            # Step 6: Extract key facts
            # For now, basic extraction - can be enhanced
            key_facts = {
                "duration_seconds": int(info.duration),
                "language": info.language,
                "loan_numbers": loan_numbers,
                "sentiment": sentiment
            }
            
            # Step 7: Save to database
            total_time = (time.time() - total_start) * 1000
            self.save_to_database(
                orkuid, summary, transcript_path, loan_numbers, 
                key_facts, sentiment, total_time
            )
            
            print(f"\n✅ Processing complete in {total_time:.0f}ms")
            print(f"\nSummary:\n{summary}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error processing {orkuid}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Clean up resources"""
        if self.cursor:
            self.cursor.close()
        if self.db_conn:
            self.db_conn.close()
        print("\n✓ Pipeline closed")


# Main execution
if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 3:
        print("\nUsage: python scream_hybrid_pipeline.py <orkuid> <audio_path>")
        print("Example: python scream_hybrid_pipeline.py 20250620_145645_LOLW audio.wav")
        sys.exit(1)
    
    orkuid = sys.argv[1]
    audio_path = sys.argv[2]
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = ScreamPipeline()
    try:
        pipeline.process_recording(orkuid, audio_path)
    finally:
        pipeline.close()