import os, requests, time
BASE = os.environ.get("MINA_BASE_URL","http://localhost:5000")
S = requests.Session()
def post(p, j): return S.post(BASE+p, json=j, timeout=10, allow_redirects=False)
def get(p): return S.get(BASE+p, timeout=10, allow_redirects=False)

print("[smoke] base", BASE)
u = str(int(time.time()))+"@test.local"
r = post("/auth/register", {"email":u,"password":"Passw0rd!","name":"Test"})
assert r.ok and r.json().get("ok"), r.text
r = get("/auth/me"); assert r.ok and r.json().get("user"), r.text
r = post("/api/conversations", {"title":"Smoke"}); assert r.ok and r.json().get("ok"), r.text
cid = r.json()["id"]
r = post(f"/api/conversations/{cid}/segments", {"idx":0,"text":"hello ","is_final":False}); assert r.ok
r = post(f"/api/conversations/{cid}/segments", {"idx":1,"text":"world","is_final":True}); assert r.ok
r = get(f"/api/conversations/{cid}"); j=r.json(); assert "segments" in j and len(j["segments"])==2
print("[smoke] PASS")
