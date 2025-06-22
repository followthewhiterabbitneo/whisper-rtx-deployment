#!/usr/bin/env python3
"""
SCREAM Loan Search - Find all calls for a specific loan number
First principles: Extract loan numbers FAST, then aggregate summaries
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import pymysql
from typing import List, Dict

class LoanNumberExtractor:
    """Fast loan number extraction without AI"""
    
    # Common loan number patterns in mortgage industry
    PATTERNS = [
        # Standard 10-12 digit loan numbers
        r'\b\d{10}\b',
        r'\b\d{11}\b', 
        r'\b\d{12}\b',
        
        # With common prefixes
        r'loan\s*(?:number|#|num)?\s*[:\-]?\s*(\d{8,12})',
        r'application\s*(?:number|#|num)?\s*[:\-]?\s*(\d{8,12})',
        r'file\s*(?:number|#|num)?\s*[:\-]?\s*(\d{8,12})',
        r'reference\s*(?:number|#|num)?\s*[:\-]?\s*(\d{8,12})',
        
        # FHA/VA/USDA formats
        r'\b\d{3}-\d{7}\b',  # FHA case number
        r'\b\d{2}-\d{2}-\d{6}\b',  # VA loan number
        
        # Alphanumeric patterns
        r'\b[A-Z]{2,4}\d{6,10}\b',  # Like FEN123456
        r'\b\d{6,10}[A-Z]{2,4}\b',  # Like 123456FEN
    ]
    
    @classmethod
    def extract(cls, text: str) -> List[str]:
        """Extract all potential loan numbers from text"""
        found = set()
        
        for pattern in cls.PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                if isinstance(match, tuple):
                    match = match[0]
                clean = match.strip().upper()
                
                # Filter out obvious non-loan numbers
                if clean and not cls._is_false_positive(clean):
                    found.add(clean)
        
        return sorted(list(found))
    
    @staticmethod
    def _is_false_positive(number: str) -> bool:
        """Filter out common false positives"""
        # Phone numbers (10 digits starting with area codes)
        if re.match(r'^[2-9]\d{9}$', number):
            return True
        
        # Dates in numeric format
        if re.match(r'^(19|20)\d{6}$', number):
            return True
            
        # Too short or too long
        if len(number) < 6 or len(number) > 15:
            return True
            
        return False


class LoanCallAggregator:
    """Aggregate all calls for a specific loan number"""
    
    def __init__(self, transcription_dir: str = "transcriptions", 
                 summary_dir: str = "summaries"):
        self.transcription_dir = Path(transcription_dir)
        self.summary_dir = Path(summary_dir)
        self.summary_dir.mkdir(exist_ok=True)
        
        # Create index file
        self.index_file = self.summary_dir / "loan_index.json"
        self.loan_index = self._load_index()
        
    def _load_index(self) -> Dict:
        """Load or create loan index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_index(self):
        """Save loan index"""
        with open(self.index_file, 'w') as f:
            json.dump(self.loan_index, f, indent=2)
    
    def scan_all_transcripts(self):
        """Scan all transcripts and build loan number index"""
        print("Scanning all transcripts for loan numbers...")
        
        for transcript_file in self.transcription_dir.glob("*.txt"):
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract loan numbers
                loan_numbers = LoanNumberExtractor.extract(content)
                
                # Update index
                for loan_num in loan_numbers:
                    if loan_num not in self.loan_index:
                        self.loan_index[loan_num] = []
                    
                    file_info = {
                        'file': str(transcript_file.name),
                        'path': str(transcript_file),
                        'timestamp': transcript_file.stat().st_mtime,
                        'date': datetime.fromtimestamp(
                            transcript_file.stat().st_mtime
                        ).strftime('%Y-%m-%d %H:%M')
                    }
                    
                    # Avoid duplicates
                    if not any(f['file'] == file_info['file'] 
                              for f in self.loan_index[loan_num]):
                        self.loan_index[loan_num].append(file_info)
                        print(f"  Found loan {loan_num} in {transcript_file.name}")
                        
            except Exception as e:
                print(f"Error processing {transcript_file}: {e}")
        
        # Save index
        self._save_index()
        print(f"\nIndexed {len(self.loan_index)} unique loan numbers")
        
    def get_calls_for_loan(self, loan_number: str) -> List[Dict]:
        """Get all calls related to a loan number"""
        loan_number = loan_number.upper().strip()
        
        if loan_number in self.loan_index:
            # Sort by timestamp
            calls = sorted(self.loan_index[loan_number], 
                          key=lambda x: x['timestamp'])
            return calls
        return []
    
    def create_loan_report(self, loan_number: str) -> str:
        """Create a report of all calls for a loan"""
        calls = self.get_calls_for_loan(loan_number)
        
        if not calls:
            return f"No calls found for loan number: {loan_number}"
        
        report = f"LOAN ACTIVITY REPORT\n"
        report += f"Loan Number: {loan_number}\n"
        report += f"Total Calls: {len(calls)}\n"
        report += f"Date Range: {calls[0]['date']} to {calls[-1]['date']}\n"
        report += "="*60 + "\n\n"
        
        for i, call in enumerate(calls, 1):
            report += f"Call #{i}: {call['date']}\n"
            report += f"File: {call['file']}\n"
            
            # Read first few lines of transcript
            try:
                with open(call['path'], 'r', encoding='utf-8') as f:
                    preview = f.read(500).replace('\n', ' ')
                    if len(preview) == 500:
                        preview += "..."
                report += f"Preview: {preview}\n"
            except:
                report += "Preview: [Unable to read file]\n"
                
            report += "-"*60 + "\n\n"
            
        return report
    
    def generate_consolidated_summary(self, loan_number: str, model=None):
        """Generate a consolidated summary of all calls for a loan"""
        calls = self.get_calls_for_loan(loan_number)
        
        if not calls:
            return None
            
        # Collect all transcripts
        all_content = []
        for call in calls:
            try:
                with open(call['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                all_content.append(f"=== Call on {call['date']} ===\n{content}\n")
            except:
                continue
                
        if not all_content:
            return None
            
        # If model provided, generate AI summary
        if model:
            combined = "\n\n".join(all_content)
            prompt = f"""Create a consolidated summary of all calls regarding loan {loan_number}.
            
Focus on:
1. Overall loan progression
2. Key issues or concerns raised
3. Commitments made across all calls
4. Final status/resolution

{combined[:30000]}"""  # Limit context
            
            # Model would generate summary here
            return "AI summary would go here"
        else:
            # Return basic report
            return self.create_loan_report(loan_number)


# Database integration for production
class LoanSearchDB:
    """Database-backed loan search for production"""
    
    def __init__(self, db_config: dict):
        self.db_config = db_config
        
    def search_by_loan(self, loan_number: str) -> List[Dict]:
        """Search database for all calls with loan number"""
        
        # This would search transcription results table
        query = """
        SELECT 
            s.orkuid,
            s.timestamp,
            s.localparty,
            s.remoteparty,
            t.filename,
            tr.transcript_text,
            tr.loan_numbers,
            tr.summary
        FROM scream_transcripts tr
        JOIN orksegment s ON tr.orkuid = s.orkuid
        JOIN orktape t ON s.orkuid = t.orkuid
        WHERE tr.loan_numbers LIKE %s
        ORDER BY s.timestamp DESC
        """
        
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, (f'%{loan_number}%',))
                results = cursor.fetchall()
            connection.close()
            return results
        except Exception as e:
            print(f"Database error: {e}")
            return []


def main():
    """Example usage"""
    import sys
    
    # Create aggregator
    aggregator = LoanCallAggregator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "scan":
            # Scan all transcripts
            aggregator.scan_all_transcripts()
            
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            # Search for specific loan
            loan_num = sys.argv[2]
            print(f"\nSearching for loan: {loan_num}")
            
            report = aggregator.create_loan_report(loan_num)
            print(report)
            
            # Save report
            report_file = aggregator.summary_dir / f"loan_{loan_num}_report.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {report_file}")
            
        elif sys.argv[1] == "extract" and len(sys.argv) > 2:
            # Extract loan numbers from specific file
            with open(sys.argv[2], 'r') as f:
                text = f.read()
            numbers = LoanNumberExtractor.extract(text)
            print(f"Found loan numbers: {numbers}")
            
    else:
        print("Usage:")
        print("  python scream_loan_search.py scan              # Build loan index")
        print("  python scream_loan_search.py search <loan#>    # Search for loan")
        print("  python scream_loan_search.py extract <file>    # Extract loan numbers")


if __name__ == "__main__":
    main()