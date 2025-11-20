"""
@Maaitrayo Das, 19 Nov 2025
run: python -m pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_triage_basic_shape():
    payload = {
        "description": "Checkout keeps failing with error 500 on mobile when I try to pay."
    }
    resp = client.post("/triage", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Check required fields
    for field in ["summary", "category", "severity", "known_issue", "related_issues", "next_action"]:
        assert field in data

    assert isinstance(data["related_issues"], list)


def test_triage_empty_description():
    payload = {"description": ""}
    resp = client.post("/triage", json=payload)
    assert resp.status_code == 422
