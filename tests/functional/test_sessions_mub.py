from datetime import datetime

import pytest
from pydantic import constr
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import AUTH_COOKIE_NAME
from tests.conftest import ActiveSession, Factory
from tests.functional.test_reglog import COOKIE_REGEX
from tests.functional.test_sessions import session_checker
from tests.utils import assert_nodata_response, assert_response, get_db_session


@pytest.fixture()
async def mub_session(session_factory: Factory[Session]) -> Session:
    return await session_factory(mub=True)


@pytest.mark.anyio()
async def test_making_mub_session(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    response = assert_nodata_response(
        client.post(f"/mub/users/{user.id}/sessions/"),
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        session = await Session.find_first_by_kwargs(
            token=response.cookies[AUTH_COOKIE_NAME]
        )
        assert session is not None
        assert_contains(
            {
                "mub": session.mub,
                "user_id": session.user_id,
                "invalid": session.invalid,
            },
            {"mub": True, "user_id": user.id, "invalid": False},
        )


@pytest.mark.anyio()
async def test_upserting_mub_session(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
) -> None:
    response = assert_nodata_response(
        client.put(f"/mub/users/{user.id}/sessions/"),
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        session = await Session.find_first_by_kwargs(
            token=response.cookies[AUTH_COOKIE_NAME]
        )
        assert session is not None
        assert_contains(
            {
                "mub": session.mub,
                "user_id": session.user_id,
                "invalid": session.invalid,
            },
            {"mub": True, "user_id": user.id, "invalid": False},
        )


@pytest.mark.anyio()
async def test_upserting_existing_mub_session(
    active_session: ActiveSession,
    client: TestClient,
    user: User,
    mub_session: Session,
) -> None:
    response = assert_nodata_response(
        client.put(f"/mub/users/{user.id}/sessions/"),
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        assert response.cookies[AUTH_COOKIE_NAME] == mub_session.token


@pytest.mark.anyio()
async def test_upserting_expired_mub_session(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    client: TestClient,
    user: User,
) -> None:
    await session_factory(mub=True, expiry=datetime.fromtimestamp(0))
    response = assert_nodata_response(
        client.put(f"/mub/users/{user.id}/sessions/"),
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        session = await Session.find_first_by_kwargs(
            token=response.cookies[AUTH_COOKIE_NAME]
        )
        assert session is not None
        assert_contains(
            {
                "mub": session.mub,
                "user_id": session.user_id,
                "invalid": session.invalid,
            },
            {"mub": True, "user_id": user.id, "invalid": False},
        )


@pytest.mark.anyio()
async def test_upserting_disabled_mub_session(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    client: TestClient,
    user: User,
) -> None:
    await session_factory(mub=True, disabled=True)
    response = assert_nodata_response(
        client.put(f"/mub/users/{user.id}/sessions/"),
        expected_headers={"Set-Cookie": constr(pattern=COOKIE_REGEX)},
    )

    async with active_session():
        session = await Session.find_first_by_kwargs(
            token=response.cookies[AUTH_COOKIE_NAME]
        )
        assert session is not None
        assert_contains(
            {
                "mub": session.mub,
                "user_id": session.user_id,
                "invalid": session.invalid,
            },
            {"mub": True, "user_id": user.id, "invalid": False},
        )


@pytest.mark.anyio()
async def test_mub_disabling_session(
    active_session: ActiveSession,
    client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        client.delete(f"/mub/users/{user.id}/sessions/{session.id}/"),
    )

    async with active_session():
        assert (await get_db_session(session)).invalid


@pytest.mark.anyio()
async def test_mub_deleting_session(
    active_session: ActiveSession,
    client: TestClient,
    session: Session,
    user: User,
) -> None:
    assert_nodata_response(
        client.delete(
            f"/mub/users/{user.id}/sessions/{session.id}/",
            params={"delete_session": "true"},
        ),
    )

    async with active_session():
        assert (await Session.find_first_by_id(session.id)) is None


@pytest.mark.anyio()
async def test_authorized_method_with_mub_session(
    client: TestClient,
    user: User,
    mub_session: Session,
) -> None:
    assert_response(
        client.get(
            "/api/users/current/home/", cookies={AUTH_COOKIE_NAME: mub_session.token}
        ),
        expected_json={
            "email": user.email,
            "username": user.username,
        },
    )


@pytest.mark.parametrize("method", ["POST", "PUT", "GET"])
@pytest.mark.anyio()
async def test_retriving_mub_session_user_not_found(
    client: TestClient,
    deleted_user: User,
    method: str,
) -> None:
    assert_response(
        client.request(method, f"/mub/users/{deleted_user.id}/sessions/"),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.parametrize("delete_session", [True, False])
@pytest.mark.anyio()
async def test_mub_disabling_session_user_not_found(
    client: TestClient,
    session: Session,
    deleted_user: User,
    delete_session: bool,
) -> None:
    assert_response(
        client.delete(
            f"/mub/users/{deleted_user.id}/sessions/{session.id}/",
            params={"delete_session": delete_session},
        ),
        expected_json={"detail": "User not found"},
        expected_code=404,
    )


@pytest.mark.parametrize("delete_session", [True, False])
@pytest.mark.anyio()
async def test_disabled_session_not_found(
    active_session: ActiveSession,
    client: TestClient,
    session: Session,
    user: User,
    delete_session: bool,
) -> None:
    async with active_session():
        await session.delete()

    assert_response(
        client.delete(
            f"/mub/users/{user.id}/sessions/{session.id}/",
            params={"delete_session": delete_session},
        ),
        expected_json={"detail": "Session not found"},
        expected_code=404,
    )


@pytest.mark.anyio()
async def test_listing_sessions_but_mub(
    authorized_client: TestClient,
    mub_session: Session,
) -> None:
    assert_response(authorized_client.get("/api/sessions/"), expected_json=[])


@pytest.mark.anyio()
async def test_disabling_session_mub_not_found(
    authorized_client: TestClient,
    mub_session: Session,
) -> None:
    assert_response(
        authorized_client.delete(f"/api/sessions/{mub_session.id}"),
        expected_json={"detail": "Session not found"},
        expected_code=404,
    )


@pytest.fixture()
async def mub_sessions(session_factory: Factory[Session]) -> list[Session]:
    return (
        [(await session_factory(mub=True)) for _ in range(3)]
        + [(await session_factory()) for _ in range(3)]
    )[::-1]


@pytest.mark.anyio()
async def test_disabling_all_other_sessions_but_mub(
    authorized_client: TestClient,
    active_session: ActiveSession,
    mub_sessions: list[Session],
) -> None:
    assert_nodata_response(authorized_client.delete("/api/sessions/"))

    async with active_session():
        for session in mub_sessions:
            session = await get_db_session(session)
            assert session.invalid != session.mub


@pytest.mark.anyio()
async def test_mub_getting_all_sessions(
    client: TestClient,
    user: User,
    mub_sessions: list[Session],
) -> None:
    assert_response(
        client.get(f"/mub/users/{user.id}/sessions/"),
        expected_json=[
            session_checker(session, check_mub=True) for session in mub_sessions
        ],
    )
