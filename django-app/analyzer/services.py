import os
import json
import requests
import socket
from typing import Dict, Any

SYSTEM_PROMPT = """You are an expert contract lawyer and risk analyst.
Your job is to analyze contracts and identify risks for the party signing or receiving the contract.
Always respond with valid JSON only. No markdown, no explanation outside the JSON."""

ANALYSIS_PROMPT = """Analyze the following contract text and return a JSON object with this exact structure:

{
  "overall_risk_score": <number 1-100>,
  "overall_risk_level": "<Low|Medium|High|Critical>",
  "summary": "<2-3 sentence plain English summary of what this contract is about>",
  "party_info": {
    "document_type": "<type of contract>",
    "key_parties": "<parties involved if mentioned>"
  },
  "risks": [
    {
      "id": "<unique id like risk_1>",
      "title": "<short risk title>",
      "severity": "<Low|Medium|High|Critical>",
      "category": "<category like Liability|Payment|Termination|IP|Privacy|Non-compete|Indemnification|Other>",
      "clause": "<the exact problematic clause text, max 200 chars>",
      "explanation": "<plain English explanation of why this is risky>",
      "recommendation": "<what to do about it>"
    }
  ],
  "missing_protections": [
    {
      "title": "<missing clause name>",
      "importance": "<Low|Medium|High>",
      "explanation": "<why this clause should be present>"
    }
  ],
  "positive_clauses": [
    {
      "title": "<favorable clause>",
      "explanation": "<why this is good for you>"
    }
  ],
  "quick_stats": {
    "total_risks": <number>,
    "critical_risks": <number>,
    "high_risks": <number>,
    "medium_risks": <number>,
    "low_risks": <number>
  }
}

Contract text to analyze:
"""

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file"""
    import io
    import pdfplumber
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def analyze_contract(contract_text: str, model: str = None) -> Dict[str, Any]:
    """
    Send contract text to Ollama service and return structured analysis JSON.
    """
    trimmed_text = contract_text[:8000]  # Limit text length
    user_prompt = ANALYSIS_PROMPT + trimmed_text

    # Get configuration from environment
    ollama_url = os.getenv("OLLAMA_URL", "https://clauseguard-ai-2.onrender.com/api/chat")
    model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
    
    # For Render deployment, ensure URL uses internal service name
    if os.getenv("RENDER") and "ollama" not in ollama_url:
        # Auto-correct to use internal service name if on Render
        ollama_url = "https://clauseguard-ai-2.onrender.com/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.2},
    }

    try:
        # Add timeout and retry logic
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=2)
        session.mount('http://', adapter)
        
        response = session.post(
            ollama_url, 
            json=payload, 
            timeout=60,  # 60 second timeout
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        data = response.json()
        response_text = data.get("message", {}).get("content", "") or ""
        
        # Clean the response
        response_text = _strip_code_fences(response_text)
        
        # Parse JSON
        try:
            result = json.loads(response_text)
            # Add metadata
            result["_analyzed_by"] = "ollama"
            result["_model"] = model
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from text
            extracted = _extract_first_json_object(response_text)
            if extracted:
                extracted["_analyzed_by"] = "ollama"
                extracted["_model"] = model
                return extracted
            raise ValueError("Could not parse Ollama response as JSON")
            
    except requests.exceptions.ConnectionError:
        # Connection refused - Ollama not running
        raise requests.exceptions.RequestException(
            f"Cannot connect to Ollama at {ollama_url}. Is the service running?"
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException(
            "Ollama service timed out. The model might still be loading."
        )
    except Exception as e:
        # Re-raise with more context
        raise type(e)(f"Ollama analysis failed: {str(e)}")

def _strip_code_fences(s: str) -> str:
    """Remove markdown code fences from string"""
    import re
    s = re.sub(r"^```json\s*", "", s.strip(), flags=re.IGNORECASE)
    s = re.sub(r"^```\s*", "", s.strip())
    s = re.sub(r"\s*```$", "", s.strip())
    return s.strip()

def _extract_first_json_object(text: str):
    """Extract first JSON object from text"""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                chunk = text[start:i+1]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    return None
    return None

def get_fallback_analysis(contract_text: str) -> Dict[str, Any]:
    """Return a fallback analysis when Ollama is unavailable"""
    return {
        "overall_risk_score": 50,
        "overall_risk_level": "Medium",
        "summary": "This is a demo analysis. The AI service is currently starting up.",
        "_is_demo": True,
        "party_info": {
            "document_type": "Contract (Demo Mode)",
            "key_parties": "Demo Mode - No parties identified"
        },
        "risks": [
            {
                "id": "risk_demo_1",
                "title": "Demo Mode - AI Service Starting",
                "severity": "Medium",
                "category": "Other",
                "clause": contract_text[:150] + "...",
                "explanation": "The AI analysis service is currently initializing. This is a demo response.",
                "recommendation": "Please try again in 2-3 minutes once the service is fully started."
            }
        ],
        "missing_protections": [
            {
                "title": "Full AI Analysis",
                "importance": "High",
                "explanation": "The complete contract analysis will be available once the AI service is running."
            }
        ],
        "positive_clauses": [],
        "quick_stats": {
            "total_risks": 1,
            "critical_risks": 0,
            "high_risks": 0,
            "medium_risks": 1,
            "low_risks": 0
        }
    }