# services/exporter.py
from datetime import datetime, timedelta
from typing import Dict
import uuid

def to_markdown(meeting: Dict, summary: Dict, tasks: list) -> str:
    md = []
    md.append(f"# {meeting.get('title','Meeting')}")
    md.append(f"_Date:_ {meeting.get('started_at','')}\n")
    md.append("## TL;DR\n" + (summary.get("tldr","") or "") + "\n")
    md.append("## Key Points")
    md += [f"- {b}" for b in (summary.get("bullets","") or "").splitlines() if b.strip()]
    md.append("\n## Decisions")
    md += [f"- {d}" for d in (summary.get("decisions","") or "").splitlines() if d.strip()]
    md.append("\n## Risks")
    md += [f"- {r}" for r in (summary.get("risks","") or "").splitlines() if r.strip()]
    md.append("\n## Open Questions")
    md += [f"- {q}" for q in (summary.get("questions","") or "").splitlines() if q.strip()]
    md.append("\n## Tasks")
    for t in tasks:
        md.append(f"- [ ] {t.title} {('— @'+t.owner) if t.owner else ''}")
    return "\n".join(md)

def to_ics_followup(title: str, start_dt: datetime, minutes: int = 15) -> str:
    end_dt = start_dt + timedelta(minutes=minutes)
    uid = str(uuid.uuid4())
    def fmt(dt): return dt.strftime("%Y%m%dT%H%M%SZ")
    return "\n".join([
        "BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Mina//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{fmt(datetime.utcnow())}",
        f"DTSTART:{fmt(start_dt)}",
        f"DTEND:{fmt(end_dt)}",
        f"SUMMARY:{title}",
        "END:VEVENT","END:VCALENDAR"
    ])