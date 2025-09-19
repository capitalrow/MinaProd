# services/summarizer.py
import os, time, json
import httpx
from typing import Dict

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("MINA_SUMMARY_MODEL", "gpt-4o-mini")

PROMPT = """You are Mina, a meeting assistant. Given the full transcript, produce:
1) TL;DR (1–2 sentences)
2) 5–10 bullet key points
3) Decisions (with owners/dates if explicit)
4) Risks (concise)
5) Open Questions

Return JSON with keys: tldr, bullets, decisions, risks, questions.
"""

def summarize_transcript(transcript: str) -> Dict[str, str]:
    if not transcript:
        return {"tldr":"","bullets":"","decisions":"","risks":"","questions":""}
    if not OPENAI_API_KEY:
        # graceful fallback
        first = "\n".join(transcript.splitlines()[:8])
        return {
            "tldr": (first or "")[:280],
            "bullets": "- (Add an OpenAI key to enable rich summaries.)",
            "decisions": "", "risks": "", "questions": ""
        }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role":"system","content":"Be concise and structured."},
            {"role":"user","content": f"{PROMPT}\n\nTranscript:\n{transcript}"}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    for attempt in range(3):
        try:
            with httpx.Client(timeout=60) as c:
                r = c.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            if r.status_code in (429,500,502,503,504):
                time.sleep(0.8*(attempt+1)); continue
            return {"tldr":"","bullets":"","decisions":"","risks":"","questions":""}
        except Exception:
            time.sleep(0.8*(attempt+1))
    return {"tldr":"","bullets":"","decisions":"","risks":"","questions":""}