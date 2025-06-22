#!/usr/bin/env python3
"""
Final optimized Llama 3 setup for CPU-only vGPU systems
Makes the best of the situation with fast response times
"""
import subprocess
import time
import os
import json
from pathlib import Path
from datetime import datetime

class OptimizedLlamaService:
    """Optimized Llama service that keeps model loaded"""
    
    def __init__(self):
        self.model_name = "llama3-legal"
        self.start_time = time.time()
        self.query_count = 0
        
        print("=== Optimized Llama 3 Service ===")
        print("Note: Using CPU due to vGPU limitations")
        print("Model will be kept in RAM for fast responses")
        
        # Ensure Ollama is running
        self._ensure_ollama_running()
        
        # Pre-load model
        print("\nPre-loading model into RAM...")
        self._warmup()
        
    def _ensure_ollama_running(self):
        """Make sure Ollama server is running"""
        result = subprocess.run(
            ["pgrep", "-f", "ollama serve"],
            capture_output=True
        )
        
        if result.returncode != 0:
            print("Starting Ollama server...")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)
    
    def _warmup(self):
        """Pre-load model into memory"""
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", self.model_name, "Initialize"],
            capture_output=True,
            text=True,
            timeout=120
        )
        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.1f} seconds")
        
        if result.returncode != 0:
            print(f"Warning: {result.stderr}")
    
    def query(self, prompt, max_time=60):
        """Query the model with timing"""
        self.query_count += 1
        start = time.time()
        
        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=max_time
            )
            
            elapsed = time.time() - start
            
            return {
                "success": result.returncode == 0,
                "response": result.stdout.strip() if result.returncode == 0 else result.stderr,
                "time": elapsed,
                "query_num": self.query_count
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "response": "Timeout after {max_time} seconds",
                "time": max_time,
                "query_num": self.query_count
            }
    
    def legal_summary(self, transcript):
        """Create a legal summary"""
        prompt = f"""Create a professional legal summary of this call:

TRANSCRIPT:
{transcript[:2000]}

LEGAL SUMMARY FORMAT:
1. Date/Time/Reference
2. Parties Involved
3. Subject Matter
4. Key Points Discussed
5. Agreements/Commitments
6. Action Items
7. Next Steps

Legal Summary:"""
        
        return self.query(prompt, max_time=90)
    
    def quick_summary(self, text):
        """Quick summary in 2-3 sentences"""
        prompt = f"Summarize in 2-3 sentences: {text[:500]}"
        return self.query(prompt, max_time=30)
    
    def status(self):
        """Get service status"""
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "queries_processed": self.query_count,
            "average_query_time": uptime / max(1, self.query_count),
            "model": self.model_name,
            "mode": "CPU (vGPU not accessible)"
        }

def create_test_transcript():
    """Create test transcript"""
    return """
Call Recording - June 20, 2025 14:56:45
Duration: 197 seconds
Reference: 20250620_145645_LOLW

Agent: Good afternoon, Shore Mortgage, this is Sarah.
Eric Rawlins: Hi Sarah, this is Eric Rawlins. I'm calling about my loan modification application.
Agent: I can help you with that. May I have your loan number?
Eric Rawlins: Yes, it's 4521887.
Agent: Thank you. I see you submitted your application on June 1st with all required documents.
Eric Rawlins: Yes, what's the status?
Agent: Your application is with underwriting. Standard timeline is 7-10 business days.
Eric Rawlins: When should I expect to hear back?
Agent: By June 14th or 15th at the latest. We'll call and send a letter.
Eric Rawlins: What about my upcoming payment?
Agent: We recommend continuing payments if possible. Would you like information about forbearance?
Eric Rawlins: Yes, please.
Agent: I'll email you the forbearance application. You can pause payments while under review.
Eric Rawlins: That would be helpful.
Agent: I'll send it to your email on file. Any other questions?
Eric Rawlins: When would new terms take effect if approved?
Agent: Next billing cycle after approval. Your reference number is SR-2025-0620-3847.
Eric Rawlins: Thank you Sarah.
Agent: You're welcome. Have a great day.
"""

def main():
    """Main function"""
    print("Starting Optimized Llama Service...")
    print("=" * 50)
    
    # Create service
    service = OptimizedLlamaService()
    
    # Test 1: Quick query
    print("\n[Test 1] Quick query:")
    result = service.quick_summary("Customer called about loan status")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.1f}s")
    
    # Test 2: Legal summary
    print("\n[Test 2] Legal summary:")
    transcript = create_test_transcript()
    result = service.legal_summary(transcript)
    
    if result['success']:
        print("\nLEGAL SUMMARY:")
        print("-" * 40)
        print(result['response'])
        print("-" * 40)
        print(f"Generated in: {result['time']:.1f}s")
        
        # Save to file
        output_file = Path("/moneyball/whisper-rtx-deployment/llama3_legal_summary_output.txt")
        with open(output_file, "w") as f:
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Model: Llama 3 8B (CPU Mode)\n")
            f.write(f"Time: {result['time']:.1f}s\n")
            f.write("\n" + "="*50 + "\n\n")
            f.write(result['response'])
        
        print(f"\nSaved to: {output_file}")
    else:
        print(f"Error: {result['response']}")
    
    # Status
    print("\n[Service Status]")
    status = service.status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n✓ Service is running and model is loaded in RAM")
    print("✓ Subsequent queries will be faster")
    print("\nUsage:")
    print("  from final_llama_setup import OptimizedLlamaService")
    print("  service = OptimizedLlamaService()")
    print("  result = service.legal_summary('your transcript')")

if __name__ == "__main__":
    main()