import os

os.environ.setdefault("CONTRACT_ACCOUNT", "contract.testnet")
os.environ.setdefault("AGENT_ACCOUNT", "agent.testnet")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/sealquery-backend-test.db")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("INDEXER_ON_STARTUP", "0")
os.environ.setdefault("SEALQUERY_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

from app import services  # noqa: E402
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


def test_async_query_rejects_unlisted_dataset() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/query",
            json={"dataset_id": "evil", "computation_id": "evil"},
        )
    assert response.status_code == 400


def test_dataset_state_normalizes_a_stale_budget(monkeypatch) -> None:
    today = int(__import__("time").time() // 86_400)

    def fake_view(_contract: str, method: str, _args: dict) -> dict:
        if method == "get_dataset":
            return {"budget_per_day": 20, "owner": "owner.testnet"}
        if method == "get_computation":
            return {"operation": "spend_growth"}
        if method == "quote":
            return {"price_yocto": "1"}
        return {"day": today - 1, "count": 20}

    monkeypatch.setattr(services.agent_client, "rpc_view", fake_view)
    result = services.dataset_state("retail_v1", "spend_growth_v1")
    assert result["budget"] == {"day": today, "count": 0}
    assert result["budget_exhausted"] is False


def test_machine_query_requires_key_and_is_idempotent() -> None:
    with TestClient(app) as client:
        unauthorized = client.post(
            "/api/v1/query",
            json={"dataset_id": "retail_v1", "computation_id": "spend_growth_v1"},
        )
        assert unauthorized.status_code == 401

        headers = {"X-API-Key": "test-key", "Idempotency-Key": "test-idem"}
        first = client.post(
            "/api/v1/query",
            headers=headers,
            json={"dataset_id": "retail_v1", "computation_id": "spend_growth_v1"},
        )
        second = client.post(
            "/api/v1/query",
            headers=headers,
            json={"dataset_id": "retail_v1", "computation_id": "spend_growth_v1"},
        )
    assert first.status_code == 202
    assert second.status_code == 200
    assert first.json()["job_id"] == second.json()["job_id"]
