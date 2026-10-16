from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middlewares.security_headers_middleware import SecurityHeadersMiddleware


def _build_client(strict: bool) -> TestClient:
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware, strict=strict)

    @test_app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(test_app)


def test_dispatch_when_not_strict_adds_base_headers_only() -> None:
    response = _build_client(strict=False).get("/ping")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" not in response.headers


def test_dispatch_when_strict_adds_hsts_and_csp() -> None:
    response = _build_client(strict=True).get("/ping")

    assert "strict-transport-security" in response.headers
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
