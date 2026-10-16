import httpx

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/auth/me"
HEALTH_URL = "/api/v1/health"
VALID_PASSWORD = "StrongPass123"


def _register_payload(email: str = "Doctor@Example.com") -> dict[str, str]:
    return {"email": email, "full_name": "Test Doctor", "password": VALID_PASSWORD}


async def _login(
    client: httpx.AsyncClient,
    email: str = "doctor@example.com",
    password: str = VALID_PASSWORD,
) -> httpx.Response:
    return await client.post(LOGIN_URL, json={"email": email, "password": password})


async def test_register_login_and_me_when_credentials_are_valid_returns_profile(
    client: httpx.AsyncClient,
) -> None:
    register_response = await client.post(REGISTER_URL, json=_register_payload())
    login_response = await _login(client)
    access_token = login_response.json()["access_token"]
    me_response = await client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})

    assert register_response.status_code == 201
    assert register_response.json()["email"] == "doctor@example.com"
    assert register_response.json()["role"] == "submitter"
    assert "hashed_password" not in register_response.json()
    assert login_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "doctor@example.com"


async def test_register_when_email_already_exists_returns_409(
    client: httpx.AsyncClient,
) -> None:
    await client.post(REGISTER_URL, json=_register_payload())

    response = await client.post(REGISTER_URL, json=_register_payload("doctor@example.com"))

    assert response.status_code == 409


async def test_register_when_password_is_weak_returns_422_without_echoing_it(
    client: httpx.AsyncClient,
) -> None:
    payload = _register_payload()
    payload["password"] = "weak1"

    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 422
    assert "weak1" not in response.text


async def test_login_when_credentials_are_invalid_returns_same_401_message(
    client: httpx.AsyncClient,
) -> None:
    await client.post(REGISTER_URL, json=_register_payload())

    wrong_password = await _login(client, password="WrongPass123")
    unknown_email = await _login(client, email="nobody@example.com")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["message"] == unknown_email.json()["message"]


async def test_me_when_no_token_is_sent_returns_401(client: httpx.AsyncClient) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401


async def test_refresh_when_refresh_token_is_valid_returns_new_tokens(
    client: httpx.AsyncClient,
) -> None:
    await client.post(REGISTER_URL, json=_register_payload())
    tokens = (await _login(client)).json()

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_refresh_when_access_token_is_used_returns_401(
    client: httpx.AsyncClient,
) -> None:
    await client.post(REGISTER_URL, json=_register_payload())
    tokens = (await _login(client)).json()

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401


async def test_responses_when_requested_include_security_headers(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(HEALTH_URL)

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "x-request-id" in response.headers
