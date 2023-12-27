from datetime import timedelta
from typing import Final

import pytest
from fastapi import Response
from freezegun import freeze_time

from app.models.sessions_db import Session
from app.models.users_db import User
from app.utils.authorization import authorize_user
from tests.conftest import ActiveSession
from tests.functional.test_reglog import assert_session_cookie
from tests.mock_stack import MockStack

days_to_renew: Final[int] = (Session.expiry_timeout - Session.renew_period_length).days


@pytest.mark.parametrize(
    ("active_for", "expected"),
    [
        pytest.param(days, days > days_to_renew)
        for days in range(Session.expiry_timeout.days)
        if days != days_to_renew
    ],
)
def test_renewal_required_detection(
    session: Session,
    mock_stack: MockStack,
    active_for: int,
    expected: bool,
) -> None:
    with freeze_time(session.created + timedelta(days=active_for)):
        assert session.is_renewal_required() == expected


@pytest.mark.anyio()
async def test_renewal_method(
    mock_stack: MockStack,
    active_session: ActiveSession,
    session: Session,
    session_token: str,
) -> None:
    old_expiry = session.expiry
    async with active_session():
        session.renew()
    assert session.token != session_token
    assert session.expiry > old_expiry


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "cross_site",
    [
        pytest.param(False, id="same_origin"),
        pytest.param(True, id="cross_site"),
    ],
)
async def test_automatic_renewal(
    mock_stack: MockStack,
    active_session: ActiveSession,
    user: User,
    cross_site: bool,
) -> None:
    session_is_renewal_required = mock_stack.enter_mock(
        Session, "is_renewal_required", return_value=True
    )
    session_renew_mock = mock_stack.enter_mock(Session, "renew")
    response = Response()

    async with active_session():
        session = await Session.create(user_id=user.id, cross_site=cross_site)
        await authorize_user(session, response)

    async with active_session():
        await assert_session_cookie(response, cross_site=cross_site)

    session_is_renewal_required.assert_called_once_with()
    session_renew_mock.assert_called_once_with()
