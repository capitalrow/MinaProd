import os, sys, time, random, string, requests

BASE = os.environ.get("MINA_BASE_URL","http://localhost:5000")
USERS = int(os.environ.get("SOAK_USERS","1"))
SEGS  = int(os.environ.get("SOAK_SEGS","50"))

S = requests.Session()

def j(method, path, json_body=None):
    url = BASE + path
    r = S.request(method, url, json=json_body, timeout=15)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    if not r.ok or data.get("ok") is False:
        raise RuntimeError(f"{method} {path} failed {r.status_code} -> {data}")
    return data

def random_text(n=40):
    import random, string
    words = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel","india"]
    return " ".join(random.choice(words) for _ in range(n//5)) + " "

def run_user(user_i):
    title = f"Soak-{user_i}-{int(time.time())}"
    r = j("POST","/api/conversations", {"title":title})
    cid = r["id"]
    idx = 0
    for k in range(SEGS-1):
        txt = random_text(60)
        j("POST", f"/api/conversations/{cid}/segments",
          {"idx":idx,"start_ms":k*1000,"end_ms":(k+1)*1000,"text":txt,"is_final":False})
        idx += 1
        time.sleep(0.02)  # 20ms spacing to simulate streaming
    j("POST", f"/api/conversations/{cid}/segments",
      {"idx":idx,"start_ms":(SEGS-1)*1000,"end_ms":SEGS*1000,"text":"[FINAL]\n","is_final":True})
    j("POST", f"/api/conversations/{cid}/finalize", {})
    r = j("GET", f"/api/conversations/{cid}")
    segs = r["segments"]
    assert len(segs) == SEGS, f"expected {SEGS} segs, got {len(segs)}"
    assert [s["idx"] for s in segs] == list(range(SEGS)), "indices not monotonic"
    return cid

def main():
    print(f"[soak] base={BASE} users={USERS} segs={SEGS}")
    ids=[]
    for i in range(USERS):
      cid = run_user(i)
      ids.append(cid)
      print(f"[soak] user={i} conversation={cid}")
    print("[soak] PASS: created conversations:", ids)
if __name__=="__main__":
    main()
