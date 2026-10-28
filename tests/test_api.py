from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ROOT = Path(__file__).parents[1]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_and_compare_specs():
    old = (ROOT / "examples" / "orders-v1.json").read_bytes()
    new = (ROOT / "examples" / "orders-v2.json").read_bytes()
    old_response = client.post("/api/v1/specs?name=orders-v1", files={"file": ("v1.json", old, "application/json")})
    new_response = client.post("/api/v1/specs?name=orders-v2", files={"file": ("v2.json", new, "application/json")})
    assert old_response.status_code == 201
    assert new_response.status_code == 201
    result = client.post("/api/v1/comparisons", json={"old_spec_id": old_response.json()["id"], "new_spec_id": new_response.json()["id"]})
    assert result.status_code == 201
    assert result.json()["risk_score"] > 0
