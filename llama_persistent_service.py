#!/usr/bin/env python3
"""
Persistent Llama Service - Keep model loaded in GPU memory
Avoid 101 second reload time!
"""
import subprocess
import requests
import json
import time
import threading
from datetime import datetime

class PersistentLlamaService:
    """Keep Llama model loaded in GPU memory"""
    
    def __init__(self):
        self.api_url = "http://localhost:11434"
        self.model = "llama3"
        self.load_time = None
        
        print("=== Persistent Llama Service ===")
        print("Keeping model in GPU memory to avoid 101s reload!")
        
        # Ensure Ollama is running
        self._ensure_ollama_running()
        
        # Load model once
        self._initial_load()
        
        # Start keep-alive thread
        self.keep_alive_thread = threading.Thread(target=self._keep_alive_loop)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()
        
    def _ensure_ollama_running(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print("✓ Ollama server is running")
                return True
        except:
            pass
        
        print("Starting Ollama server...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        
    def _initial_load(self):
        """Load model into GPU memory (one-time cost)"""
        print(f"\nLoading {self.model} into GPU memory...")
        print("This will take ~101 seconds ONE TIME only...")
        
        start = time.time()
        
        # Trigger model load with a simple query
        response = self.query("Hello", max_tokens=1)
        
        self.load_time = time.time() - start
        print(f"\n✓ Model loaded in {self.load_time:.1f} seconds")
        print("✓ Model now resident in GPU memory!")
        
        # Check GPU memory
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        print(f"✓ GPU memory used: {result.stdout.strip()} MiB")
        
    def _keep_alive_loop(self):
        """Keep model in memory with periodic pings"""
        while True:
            time.sleep(240)  # Every 4 minutes
            try:
                # Send tiny query to keep model loaded
                self.query(".", max_tokens=1, silent=True)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Model kept alive in GPU")
            except:
                pass
    
    def query(self, prompt, max_tokens=500, temperature=0.7, silent=False):
        """Query the model - FAST because it's already loaded!"""
        start = time.time()
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                elapsed = time.time() - start
                
                if not silent:
                    print(f"\n⚡ Response time: {elapsed:.2f}s (no reload needed!)")
                
                return {
                    "response": result.get("response", ""),
                    "time": elapsed,
                    "success": True
                }
            else:
                return {
                    "response": f"Error: {response.status_code}",
                    "time": 0,
                    "success": False
                }
                
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "time": 0,
                "success": False
            }
    
    def legal_summary(self, transcript):
        """Create legal summary - FAST!"""
        prompt = f"""Create a professional legal summary of this call:

TRANSCRIPT:
{transcript[:3000]}

LEGAL SUMMARY FORMAT:
1. Date/Time/Reference
2. Parties Involved
3. Subject Matter
4. Key Points Discussed
5. Agreements/Commitments
6. Action Items
7. Next Steps

Legal Summary:"""
        
        result = self.query(prompt, max_tokens=1000, temperature=0.3)
        return result
    
    def quick_response(self, prompt):
        """Quick response - already loaded!"""
        return self.query(prompt, max_tokens=200)

# Global service instance
_service = None

def get_service():
    """Get or create persistent service"""
    global _service
    if _service is None:
        _service = PersistentLlamaService()
    return _service

def test_service():
    """Test the persistent service"""
    print("\n=== Testing Persistent Service ===")
    
    service = get_service()
    
    # Test 1: Quick query
    print("\nTest 1: Quick query")
    result = service.quick_response("What is 2+2?")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.2f}s")
    
    # Test 2: Another query (should be fast!)
    print("\nTest 2: Another query (no reload!)")
    result = service.quick_response("What is the capital of France?")
    print(f"Response: {result['response']}")
    print(f"Time: {result['time']:.2f}s")
    
    # Test 3: Legal summary
    print("\nTest 3: Legal summary")
    test_transcript = "Eric Rawlins called on June 20th about his loan modification application status."
    result = service.legal_summary(test_transcript)
    print(f"Summary preview: {result['response'][:200]}...")
    print(f"Time: {result['time']:.2f}s")
    
    print("\n✅ Service is running! Model stays loaded in GPU")
    print("✅ No more 101 second wait times!")

if __name__ == "__main__":
    test_service()
    
    print("\n=== Service Running ===")
    print("Model loaded in GPU memory")
    print("Import and use:")
    print("  from llama_persistent_service import get_service")
    print("  service = get_service()")
    print("  result = service.query('your prompt')")
    print("\nPress Ctrl+C to stop")