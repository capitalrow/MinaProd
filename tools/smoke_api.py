import os, json, time, sys
import requests

BASE = os.environ.get("MINA_BASE_URL", "http://localhost:5000")
S = requests.Session()

def j(method, path, json_body=None):
    url = BASE + path
    r = S.request(method, url, json=json_body, timeout=10)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok or data.get("ok") is False:
        raise SystemExit(f"{method} {path} failed {r.status_code} -> {data}")
    return data

def main():
    print(f"[smoke] base={BASE}")
    # Verify health
    for ep in ["/healthz", "/readyz"]:
        r = S.get(BASE+ep, timeout=5)
        print(ep, r.status_code, r.text[:60])
    # Create conversation
    r = j("POST", "/api/conversations", {"title":"Smoke Test Session"})
    cid = r["id"]
    print("[smoke] conversation id:", cid)
    # Add segments (interim then final)
    segs = [
        {"idx":0,"start_ms":0,"end_ms":2000,"text":"Hello this is an interim ", "is_final":False},
        {"idx":1,"start_ms":2000,"end_ms":5000,"text":"and this is a final.\n", "is_final":True}
    ]
    for s in segs:
        j("POST", f"/api/conversations/{cid}/segments", s)
    # Finalize
    j("POST", f"/api/conversations/{cid}/finalize", {})
    # Fetch back and verify ordering and content
    r = j("GET", f"/api/conversations/{cid}")
    body = "".join(x["text"] for x in r["segments"])
    assert "interim" in body and "final" in body, "Transcript text missing"
    idxs = [x["idx"] for x in r["segments"]]
    assert idxs == sorted(idxs), "Segment indices not ordered"
    print("[smoke] PASS: segments persisted and ordered. len(body)=", len(body))
if __name__ == "__main__":
    main()
