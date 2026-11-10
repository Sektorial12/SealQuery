import os

os.environ.setdefault("CONTRACT_ACCOUNT", "contract.testnet")
os.environ.setdefault("AGENT_ACCOUNT", "agent.testnet")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/sealquery-backend-test.db")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("INDEXER_ON_STARTUP", "0")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["contract"] == "contract.testnet"


def test_async_query_enqueues_job() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={"dataset_id": "retail_v1", "computation_id": "spend_growth_v1"},
        )
        assert response.status_code == 202
        payload = response.json()
        assert payload["ok"] is True
        assert payload["status"] == "queued"
        job = client.get(f"/api/jobs/{payload['job_id']}")
        assert job.status_code == 200
        assert job.json()["status"] == "queued"


def test_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"
