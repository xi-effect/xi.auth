from typing import Generic, TypeVar

from httpx import Response
from pydantic_marshals.contains import TypeChecker, assert_contains

from app.models.sessions_db import Session
from app.models.users_db import User


def assert_nodata_response(
    response: Response,
    *,
    expected_code: int = 204,
    expected_headers: dict[str, TypeChecker] | None = None,
) -> Response:
    assert_contains(
        {
            "status_code": response.status_code,
            "headers": response.headers,
        },
        {
            "status_code": expected_code,
            "headers": expected_headers or {},
        },
    )
    return response


def assert_response(
    response: Response,
    *,
    expected_code: int = 200,
    expected_json: TypeChecker,
    expected_headers: dict[str, TypeChecker] | None = None,
) -> Response:
    expected_headers = expected_headers or {}
    expected_headers["Content-Type"] = "application/json"
    assert_contains(
        {
            "status_code": response.status_code,
            "json_data": (
                response.json()
                if response.headers.get("Content-Type") == "application/json"
                else None
            ),
            "headers": response.headers,
        },
        {
            "status_code": expected_code,
            "json_data": expected_json,
            "headers": expected_headers or {},
        },
    )
    return response


T = TypeVar("T")


class PytestRequest(Generic[T]):
    @property
    def param(self) -> T:
        raise NotImplementedError


async def get_db_user(user: User) -> User:
    db_user = await User.find_first_by_id(user.id)
    assert db_user is not None
    return db_user


async def get_db_session(session: Session) -> Session:
    db_session = await Session.find_first_by_id(session.id)
    assert db_session is not None
    return db_session
