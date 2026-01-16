from fastapi.testclient import TestClient

import Backend.api_server as api


client = TestClient(api.app)


def test_approval_endpoints_toggle_status():
    section_queue = [
        {"section_id": "s1", "section_type": "intro", "position_order": 1, "status": "pending"},
        {"section_id": "s2", "section_type": "methodology", "position_order": 2, "status": "locked"},
    ]

    # Approve first section, expect next unlocked (pending)
    resp = client.post("/docgen/sections/s1/approve", json={"section_queue": section_queue})
    assert resp.status_code == 200
    updated = {s["section_id"]: s["status"] for s in resp.json()["section_queue"]}
    assert updated["s1"] == "approved"
    assert updated["s2"] == "pending"

    # Reject second section, status should flip to rejected
    resp2 = client.post("/docgen/sections/s2/reject", json={"section_queue": resp.json()["section_queue"], "feedback": "needs fix"})
    assert resp2.status_code == 200
    updated2 = {s["section_id"]: s["status"] for s in resp2.json()["section_queue"]}
    assert updated2["s2"] == "rejected"
