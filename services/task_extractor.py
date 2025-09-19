# services/task_extractor.py
import os, re, time, json
import httpx
from typing import List, Dict

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("MINA_TASK_MODEL", "gpt-4o-mini")

HEURISTICS = [
    r"^\s*(we|i|you|they|team)\s+(will|should|need to|must)\s+(.+)",
    r"^\s*let'?s\s+(.*)",
    r"^\s*please\s+(.*)",
    r"^\s*(action|todo|task)[:\-]\s+(.*)",
]

def heuristic_extract(text: str) -> List[Dict]:
    out = []
    for line in text.splitlines():
        s = line.strip()
        for pat in HEURISTICS:
            m = re.match(pat, s, flags=re.IGNORECASE)
            if m:
                title = " ".join(g for g in m.groups() if g).strip(": ").strip()
                if title:
                    out.append({"title": title[:500], "owner": None, "due_date": None})
                break
    return out

def refine_with_llm(transcript: str, candidates: List[Dict]) -> List[Dict]:
    if not OPENAI_API_KEY or not candidates:
        return candidates
    prompt = (
        "Refine these action items from the transcript with clear titles, explicit owners if mentioned, "
        "and any due dates. Return JSON array of {title, owner, due_date}."
    )
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role":"system","content":"You extract concrete, unambiguous tasks."},
            {"role":"user","content": f"{prompt}\n\nTranscript:\n{transcript}\n\nCandidates:\n{json.dumps(candidates, ensure_ascii=False)}"}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    for attempt in range(3):
        try:
            with httpx.Client(timeout=60) as c:
                r = c.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"]
                j = json.loads(content)
                arr = j if isinstance(j, list) else j.get("tasks", [])
                return [
                    {"title": (t.get("title") or "")[:500], "owner": t.get("owner"), "due_date": t.get("due_date")}
                    for t in arr if (t.get("title") or "").strip()
                ] or candidates
            if r.status_code in (429,500,502,503,504):
                time.sleep(0.8*(attempt+1)); continue
            return candidates
        except Exception:
            time.sleep(0.8*(attempt+1))
    return candidates