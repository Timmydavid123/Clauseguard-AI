import pdfplumber
import json
import re
import io
import requests

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
    """Extract text content from a PDF file."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _strip_code_fences(s: str) -> str:
    s = re.sub(r"^```json\s*", "", s.strip(), flags=re.IGNORECASE)
    s = re.sub(r"^```\s*", "", s.strip())
    s = re.sub(r"\s*```$", "", s.strip())
    return s.strip()


def _extract_first_json_object(text: str):
    """
    If the model returns extra text, try to extract the first valid {...} JSON object.
    """
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
                chunk = text[start : i + 1]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    return None
    return None


def analyze_contract(contract_text: str, model: str = "qwen2.5:7b-instruct") -> dict:
    """
    Send contract text to Ollama and return structured analysis JSON.
    Requires Ollama running locally: http://127.0.0.1:11434
    """
    trimmed_text = contract_text[:8000]
    user_prompt = ANALYSIS_PROMPT + trimmed_text

    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.2},
    }

    r = requests.post(url, json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()

    response_text = data.get("message", {}).get("content", "") or ""
    response_text = _strip_code_fences(response_text)

    # First attempt: parse as pure JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: extract first JSON object from mixed output
        extracted = _extract_first_json_object(response_text)
        if extracted is None:
            raise ValueError("Ollama response was not valid JSON. Try a different model.")
        return extracted