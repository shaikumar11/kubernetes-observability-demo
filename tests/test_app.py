from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "alive"}


def test_ready_ok_and_not_ready(monkeypatch):
    assert client.get("/ready").status_code == 200
    monkeypatch.setenv("FORCE_NOT_READY", "true")
    assert client.get("/ready").status_code == 503


def test_work_success_and_failure():
    assert client.get("/work").status_code == 200
    assert client.get("/work?fail_rate=1").status_code == 500


def test_visits_in_memory_increments():
    first = client.get("/visits").json()["visits"]
    second = client.get("/visits").json()["visits"]
    assert second == first + 1


def test_metrics_expose_request_counter():
    client.get("/health")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds_bucket" in body
