#!/usr/bin/env python3
"""
Local Gemma Runner for Windsurf
Runs completely offline on your work laptop
"""

import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LocalGemma:
    def __init__(self, model_path="models/gemma-2b"):
        """Initialize local Gemma model"""
        print(f"Loading Gemma from {model_path}...")
        
        # Check if CUDA is available (unlikely on work laptop)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)
        
    def analyze(self, text, instruction="Summarize the following text:"):
        """Run analysis on text"""
        prompt = f"{instruction}\n\n{text}\n\nResponse:"
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the response part
        response = response.split("Response:")[-1].strip()
        
        return response
    
    def analyze_call_transcript(self, transcript, analysis_type="summary"):
        """Specialized call analysis"""
        prompts = {
            'summary': "Summarize this customer service call in 2-3 sentences:",
            'sentiment': "Analyze the customer's emotional state in this call:",
            'issues': "List the main problems or complaints mentioned in this call:",
            'compliance': "Check if this call follows proper customer service protocols:",
            'action_items': "Extract any commitments or follow-up actions from this call:"
        }
        
        instruction = prompts.get(analysis_type, prompts['summary'])
        return self.analyze(transcript, instruction)

# Lightweight alternative using llama.cpp (runs better on CPU)
class LocalGemmaLlamaCpp:
    def __init__(self, model_path="models/gemma-2b-q4_k_m.gguf"):
        """Use llama.cpp for better CPU performance"""
        self.model_path = model_path
        
    def analyze(self, text, instruction="Summarize"):
        import subprocess
        
        prompt = f"{instruction}: {text}\n\nResponse:"
        
        # Run llama.cpp
        cmd = [
            "llama.cpp/main",  # or wherever llama.cpp is installed
            "-m", self.model_path,
            "-p", prompt,
            "-n", "256",
            "--temp", "0.7"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.split("Response:")[-1].strip()

# Integration with MCP server
class GemmaAnalyzer:
    def __init__(self, use_llama_cpp=True):
        if use_llama_cpp:
            self.model = LocalGemmaLlamaCpp()
        else:
            self.model = LocalGemma()
    
    def batch_analyze_calls(self, calls, analysis_type="summary"):
        """Analyze multiple calls"""
        results = []
        
        for call in calls:
            print(f"Analyzing call {call['orkuid']}...")
            
            analysis = self.model.analyze_call_transcript(
                call.get('transcript', ''),
                analysis_type
            )
            
            results.append({
                'orkuid': call['orkuid'],
                'timestamp': call.get('timestamp'),
                'parties': f"{call.get('remoteparty')} -> {call.get('localparty')}",
                'analysis': analysis,
                'analysis_type': analysis_type
            })
        
        return results
    
    def save_analysis_report(self, results, filename="call_analysis.json"):
        """Save analysis results"""
        output_path = os.path.join("reports", filename)
        os.makedirs("reports", exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'model': 'gemma-2b-local',
                'results': results
            }, f, indent=2)
        
        print(f"Analysis saved to: {output_path}")
        return output_path

if __name__ == "__main__":
    # Test the analyzer
    analyzer = GemmaAnalyzer(use_llama_cpp=True)
    
    # Example call transcript
    test_transcript = """
    Agent: Thank you for calling support, how can I help you today?
    Customer: I'm really frustrated. I've been trying to cancel my subscription for three days!
    Agent: I'm sorry to hear that. Let me help you with the cancellation right away.
    Customer: I've called twice before and nothing happened.
    Agent: I apologize for the inconvenience. I'm processing your cancellation now and you'll receive a confirmation email within the hour.
    """
    
    result = analyzer.model.analyze_call_transcript(test_transcript, "sentiment")
    print(f"Analysis: {result}")