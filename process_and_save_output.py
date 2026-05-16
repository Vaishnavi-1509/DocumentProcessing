import requests
import json
from pathlib import Path

def process_claim(pdf_path, claim_id, output_file=None):
    """Process a PDF claim and optionally save to file"""
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        data = {'claim_id': claim_id}
        
        # Use your deployed Render API
        response = requests.post(
            'https://documentprocessing-y7m1.onrender.com/api/process',
            files=files,
            data=data
        )
    
    result = response.json()
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Results saved to {output_file}")
    
    return result

# Usage
if __name__ == "__main__":
    pdf_file = "final (1).pdf"
    output_file = "claim_results.json"
    
    result = process_claim(pdf_file, "CLM-001", output_file)
    print(json.dumps(result, indent=2))