import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import replay_engine

client = TestClient(app)


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def request(self, method, url, headers, json):
        return FakeResponse(200 if url.endswith("/ok") else 500)


@pytest.mark.asyncio
async def test_replay_engine_records_status_results(monkeypatch):
    monkeypatch.setattr(replay_engine.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    traffic = replay_engine.parse_traffic(
        b'{"method":"GET","path":"/ok","expected_status":200}\n'
        b'{"method":"GET","path":"/broken","expected_status":200}\n'
    )
    results = await replay_engine.replay_traffic("http://candidate.test", traffic)
    assert results[0].passed is True
    assert results[1].passed is False
    assert results[1].actual_status == 500


def test_replay_rejects_invalid_traffic_extension():
    response = client.post(
        "/api/v1/replays",
        data={"candidate_url": "http://127.0.0.1:9000"},
        files={"file": ("traffic.txt", b"{}", "application/json")},
    )
    assert response.status_code == 400
    assert "JSON Lines" in response.json()["detail"]


def test_parse_traffic_rejects_invalid_path():
    with pytest.raises(replay_engine.ReplayInputError):
        replay_engine.parse_traffic(b'{"method":"GET","path":"//internal","expected_status":200}')
