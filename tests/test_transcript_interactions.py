import json

def test_highlight_toggle(client, auth, segment):
    auth.login()
    res = client.post(f"/api/segment/{segment.id}/highlight", json={"highlighted": True})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["highlighted"] is True

def test_add_comment(client, auth, segment):
    auth.login()
    res = client.post(f"/api/segment/{segment.id}/comment", json={"text": "Test comment"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "comment" in data