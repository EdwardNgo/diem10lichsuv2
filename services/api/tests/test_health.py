from fastapi.testclient import TestClient

from diem10_api.main import app


def test_health_check_returns_ok() -> None:
    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
