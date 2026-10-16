from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middlewares.rate_limit_middleware import RateLimitMiddleware


def _build_client(general_limit: int, auth_limit: int) -> TestClient:
    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware, general_limit=general_limit, auth_limit=auth_limit)

    @test_app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.post("/auth/login")
    async def login() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(test_app)


def test_dispatch_when_limit_is_exceeded_returns_429() -> None:
    client = _build_client(general_limit=3, auth_limit=3)

    statuses = [client.get("/ping").status_code for _ in range(4)]

    assert statuses == [200, 200, 200, 429]


def test_dispatch_when_limit_is_exceeded_sets_retry_after_header() -> None:
    client = _build_client(general_limit=1, auth_limit=1)
    client.get("/ping")

    response = client.get("/ping")

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) >= 1
    assert response.json()["error"] == "rate_limited"


def test_dispatch_when_auth_path_is_used_applies_stricter_limit() -> None:
    client = _build_client(general_limit=100, auth_limit=2)

    login_statuses = [client.post("/auth/login").status_code for _ in range(3)]

    assert login_statuses == [200, 200, 429]
    assert client.get("/ping").status_code == 200
