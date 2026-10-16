import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user_role import UserRole
from app.repositories.user_repository import UserRepository

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CLAIMS_URL = "/api/v1/claims"
PASSWORD = "StrongPass123"


def _claim_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "patient_name": "Ali Khan",
        "policy_number": "POL-12345",
        "hospital_name": "City Hospital",
        "diagnosis": "Acute appendicitis",
        "procedure": "Appendectomy",
        "amount_claimed": 150000,
    }
    payload.update(overrides)
    return payload


async def _auth_headers(client: httpx.AsyncClient, email: str) -> dict[str, str]:
    await client.post(
        REGISTER_URL, json={"email": email, "full_name": "Test User", "password": PASSWORD}
    )
    response = await client.post(LOGIN_URL, json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _set_role(
    session_factory: async_sessionmaker[AsyncSession], email: str, role: UserRole
) -> None:
    async with session_factory() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        user.role = role
        await session.commit()


async def test_create_claim_when_data_is_valid_returns_201_with_claim_number(
    client: httpx.AsyncClient,
) -> None:
    headers = await _auth_headers(client, "alice@example.com")

    response = await client.post(CLAIMS_URL, json=_claim_payload(), headers=headers)

    assert response.status_code == 201
    assert response.json()["claim_number"].startswith("CLM-")
    assert response.json()["status"] == "submitted"


async def test_create_claim_when_amount_is_not_positive_returns_422(
    client: httpx.AsyncClient,
) -> None:
    headers = await _auth_headers(client, "alice@example.com")

    response = await client.post(CLAIMS_URL, json=_claim_payload(amount_claimed=0), headers=headers)

    assert response.status_code == 422


async def test_create_claim_when_no_token_is_sent_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(CLAIMS_URL, json=_claim_payload())

    assert response.status_code == 401


async def test_list_claims_when_user_is_submitter_returns_only_own_claims(
    client: httpx.AsyncClient,
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    bob = await _auth_headers(client, "bob@example.com")
    await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)
    await client.post(CLAIMS_URL, json=_claim_payload(), headers=bob)

    response = await client.get(CLAIMS_URL, headers=alice)

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_get_claim_when_claim_belongs_to_another_user_returns_404(
    client: httpx.AsyncClient,
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    bob = await _auth_headers(client, "bob@example.com")
    created = await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)

    response = await client.get(f"{CLAIMS_URL}/{created.json()['id']}", headers=bob)

    assert response.status_code == 404


async def test_list_claims_when_user_is_reviewer_returns_all_claims(
    client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    bob = await _auth_headers(client, "bob@example.com")
    reviewer = await _auth_headers(client, "reviewer@example.com")
    await _set_role(session_factory, "reviewer@example.com", UserRole.REVIEWER)
    created = await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)
    await client.post(CLAIMS_URL, json=_claim_payload(), headers=bob)

    list_response = await client.get(CLAIMS_URL, headers=reviewer)
    get_response = await client.get(f"{CLAIMS_URL}/{created.json()['id']}", headers=reviewer)

    assert list_response.json()["total"] == 2
    assert get_response.status_code == 200


async def test_review_claim_when_user_is_submitter_returns_403(
    client: httpx.AsyncClient,
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    created = await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)

    response = await client.patch(
        f"{CLAIMS_URL}/{created.json()['id']}/status",
        json={"status": "approved"},
        headers=alice,
    )

    assert response.status_code == 403


async def test_review_claim_when_user_is_reviewer_updates_status(
    client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    reviewer = await _auth_headers(client, "reviewer@example.com")
    await _set_role(session_factory, "reviewer@example.com", UserRole.REVIEWER)
    created = await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)

    response = await client.patch(
        f"{CLAIMS_URL}/{created.json()['id']}/status",
        json={"status": "approved", "note": "Documents verified."},
        headers=reviewer,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_review_claim_when_status_is_not_a_decision_returns_422(
    client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    alice = await _auth_headers(client, "alice@example.com")
    reviewer = await _auth_headers(client, "reviewer@example.com")
    await _set_role(session_factory, "reviewer@example.com", UserRole.REVIEWER)
    created = await client.post(CLAIMS_URL, json=_claim_payload(), headers=alice)

    response = await client.patch(
        f"{CLAIMS_URL}/{created.json()['id']}/status",
        json={"status": "submitted"},
        headers=reviewer,
    )

    assert response.status_code == 422
