import pytest
from pydantic_marshals.contains import TypeChecker
from starlette.testclient import TestClient

from app.models.sessions_db import Session
from tests.conftest import Factory
from tests.utils import assert_response


def session_checker(session: Session, invalid: bool = False) -> TypeChecker:
    return {
        "id": session.id,
        "created": session.created.isoformat().rstrip("0"),
        "expiry": session.expiry.isoformat().rstrip("0"),
        "disabled": invalid,
        "invalid": invalid,
        "token": None,
    }


def test_getting_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_response(
        authorized_client.get("/api/sessions/current"),
        expected_json=session_checker(session),
    )


def test_disable_current_session(
    authorized_client: TestClient,
    session: Session,
) -> None:
    assert_response(
        authorized_client.delete(f"/api/sessions/{session.id}"),
        expected_json={"a": True},
    )
    assert_response(
        authorized_client.get("/api/sessions/"),
        expected_code=401,
        expected_json={"detail": "Session is invalid"},
    )


@pytest.fixture()
async def sessions(session_factory: Factory[Session]) -> list[Session]:
    return [await session_factory() for _ in range(5)][::-1]


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
    assert_response(
        authorized_client.delete("/api/sessions/"),
        expected_json={"a": True},
    )
    assert_response(
        authorized_client.get("/api/sessions/"),
        expected_json=[session_checker(session, invalid=True) for session in sessions],
    )
