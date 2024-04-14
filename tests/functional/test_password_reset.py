import time
from datetime import datetime
from typing import Any

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.config import password_reset_cryptography, pochta_producer
from app.models.users_db import User
from tests.conftest import ActiveSession
from tests.mock_stack import MockStack
from tests.utils import assert_nodata_response, assert_response, get_db_user


@pytest.mark.anyio()
async def test_requesting_password_reset(
    mock_stack: MockStack,
    client: TestClient,
    active_session: ActiveSession,
    user: User,
) -> None:
    pochta_mock = mock_stack.enter_async_mock(pochta_producer, "send_message")

    assert_nodata_response(
        client.post("/api/password-reset/requests/", json={"email": user.email}),
        expected_code=202,
    )

    pochta_mock.assert_called_once()
    async with active_session():
        assert (await get_db_user(user)).reset_token is not None


@pytest.mark.anyio()
async def test_requesting_password_reset_user_not_found(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post("/api/password-reset/requests/", json={"email": faker.email()}),
        expected_code=404,
        expected_json={"detail": "User not found"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset(
    faker: Faker,
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    async with active_session():
        db_user = await get_db_user(user)
        reset_token: str = db_user.generated_reset_token
        previous_last_password_change: datetime = db_user.last_password_change
    new_password: str = faker.password()

    assert_nodata_response(
        client.post(
            "/api/password-reset/confirmations/",
            json={
                "token": password_reset_cryptography.encrypt(reset_token),
                "new_password": new_password,
            },
        ),
    )

    async with active_session():
        user_after_reset = await get_db_user(user)
        assert user_after_reset.is_password_valid(new_password)
        assert user_after_reset.last_password_change > previous_last_password_change
        assert user_after_reset.reset_token is None


@pytest.mark.anyio()
async def test_confirming_password_reset_invalid_token(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/password-reset/confirmations/",
            json={"token": faker.text(), "new_password": faker.password()},
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_expired_token(
    faker: Faker,
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    async with active_session():
        reset_token: str = (await get_db_user(user)).generated_reset_token
    expired_reset_token: bytes = password_reset_cryptography.encryptor.encrypt_at_time(
        msg=reset_token.encode("utf-8"),
        current_time=int(time.time()) - password_reset_cryptography.encryption_ttl - 1,
    )

    assert_response(
        client.post(
            "/api/password-reset/confirmations/",
            json={
                "token": expired_reset_token.decode("utf-8"),
                "new_password": faker.password(),
            },
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_no_started_reset(
    faker: Faker,
    client: TestClient,
) -> None:
    assert_response(
        client.post(
            "/api/password-reset/confirmations/",
            json={
                "token": password_reset_cryptography.encrypt(faker.text()),
                "new_password": faker.password(),
            },
        ),
        expected_code=401,
        expected_json={"detail": "Invalid token"},
    )


@pytest.mark.anyio()
async def test_confirming_password_reset_with_old_password(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
    user_data: dict[str, Any],
) -> None:
    async with active_session():
        db_user = await get_db_user(user)
        reset_token: str = db_user.generated_reset_token
        previous_last_password_change: datetime = db_user.last_password_change

    assert_nodata_response(
        client.post(
            "/api/password-reset/confirmations/",
            json={
                "token": password_reset_cryptography.encrypt(reset_token),
                "new_password": user_data["password"],
            },
        ),
    )

    async with active_session():
        assert (
            await get_db_user(user)
        ).last_password_change == previous_last_password_change
