import pytest
from pydantic_marshals.contains import TypeChecker
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from app.utils.authorization import AUTH_COOKIE_NAME
from tests.conftest import ActiveSession, Factory
from tests.utils import assert_nodata_response, assert_response


def session_checker(session: Session, invalid: bool = False) -> TypeChecker:
    return {
        "id": session.id,
        "created": session.created,
        "expiry": session.expiry,
        "disabled": invalid,
        "invalid": invalid,
        "token": None,
    }


def test_getting_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_response(
        authorized_client.get("/api/sessions/current/"),
        expected_json=session_checker(session),
    )


def test_disable_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_nodata_response(authorized_client.delete(f"/api/sessions/{session.id}/"))
    assert_response(
        authorized_client.get("/api/sessions/"),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )


@pytest.fixture()
async def sessions(session_factory: Factory[Session]) -> list[Session]:
    return [await session_factory() for _ in range(2)][::-1]


@pytest.mark.anyio()
async def test_list_sessions(
    authorized_client: TestClient,
    sessions: list[Session],
) -> None:
    assert_response(
        authorized_client.get("/api/sessions/"),
        expected_json=[session_checker(session) for session in sessions],
    )


@pytest.mark.anyio()
async def test_disable_other_sessions(
    authorized_client: TestClient,
    sessions: list[Session],
) -> None:
    assert_nodata_response(authorized_client.delete("/api/sessions/"))
    assert_response(
        authorized_client.get("/api/sessions/"),
        expected_json=[session_checker(session, invalid=True) for session in sessions],
    )


@pytest.fixture()
async def deleted_session_id(
    session_factory: Factory[Session], active_session: ActiveSession
) -> int:
    session = await session_factory()
    async with active_session():
        await session.delete()
    return session.id


def test_non_existent_session_fails(
    authorized_client: TestClient, deleted_session_id: int
) -> None:
    assert_response(
        authorized_client.delete(f"/api/sessions/{deleted_session_id}/"),
        expected_code=404,
        expected_json={"detail": "Session not found"},
    )


@pytest.mark.parametrize(
    ("use_headers", "error"),
    [
        pytest.param(False, "Authorization is missing", id="missing_header"),
        pytest.param(True, "Session is invalid", id="invalid_session"),
    ],
)
@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("GET", "/api/sessions/", id="list_sessions"),
        pytest.param("DELETE", "/api/sessions/", id="delete_other_sessions"),
        pytest.param("GET", "/api/sessions/current/", id="get_current_session"),
        pytest.param("DELETE", "/api/sessions/{session_id}/", id="disable_session"),
    ],
)
def test_authorization_fails(
    client: TestClient,
    session: Session,
    invalid_token: str,
    use_headers: bool,
    error: str,
    method: str,
    path: str,
) -> None:
    cookies = {AUTH_COOKIE_NAME: invalid_token} if use_headers else {}
    assert_response(
        client.request(method, path.format(session_id=session.id), cookies=cookies),
        expected_code=401,
        expected_json={"detail": error},
    )


def test_foreign_user_fails(other_client: TestClient, session: Session) -> None:
    assert_response(
        other_client.delete(f"/api/sessions/{session.id}/"),
        expected_code=404,
        expected_json={"detail": "Session not found"},
    )
