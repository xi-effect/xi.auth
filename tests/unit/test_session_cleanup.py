from datetime import datetime
from typing import Any

import pytest

from app.models.sessions_db import Session
from app.models.users_db import User
from tests.conftest import ActiveSession, Factory
from tests.unit.conftest import MockStack


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "method",
    [
        pytest.param(Session.cleanup_by_user, id="complete"),
        pytest.param(Session.cleanup_concurrent_by_user, id="specific"),
    ],
)
async def test_concurrent_sessions_limit(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    user: User,
    mock_stack: MockStack,
    method: Any,
) -> None:
    max_concurrent = 2
    total_active = 5
    total_history = 5
    max_concurrent_sessions_mock = mock_stack.enter_mock(
        Session, "max_concurrent_sessions", property_value=max_concurrent
    )

    session_ids = [(await session_factory()).id for _ in range(total_active)][::-1]
    history_session_ids = [
        (await session_factory(disabled=True)).id for _ in range(total_history)
    ]

    async with active_session():
        await method(user_id=user.id)

    max_concurrent_sessions_mock.assert_called_once_with()

    async with active_session():
        for history_session_id in history_session_ids:
            session = await Session.find_first_by_id(history_session_id)
            assert session is not None
            assert session.invalid

        for i in range(max_concurrent):
            session = await Session.find_first_by_id(session_ids[i])
            assert session is not None
            assert not session.invalid

        for i in range(max_concurrent, total_active):
            session = await Session.find_first_by_id(session_ids[i])
            assert session is not None
            assert session.invalid


@pytest.mark.anyio()
@pytest.mark.parametrize(
    "method",
    [
        pytest.param(Session.cleanup_by_user, id="complete"),
        pytest.param(Session.cleanup_history_by_user, id="specific"),
    ],
)
async def test_session_history_limit(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    user: User,
    mock_stack: MockStack,
    method: Any,
) -> None:
    max_history = 4
    total_active = 2
    allowed_history = max_history - total_active
    total_history = 5
    max_history_sessions_mock = mock_stack.enter_mock(
        Session, "max_history_sessions", property_value=max_history
    )

    session_ids = [
        (await session_factory(disabled=True)).id for _ in range(total_history)
    ][::-1]
    active_session_ids = [(await session_factory()).id for _ in range(total_active)]

    async with active_session():
        await method(user_id=user.id)

    max_history_sessions_mock.assert_called_once_with()

    async with active_session():
        for active_session_id in active_session_ids:
            session = await Session.find_first_by_id(active_session_id)
            assert session is not None
            assert not session.invalid

        for i in range(allowed_history):
            session = await Session.find_first_by_id(session_ids[i])
            assert session is not None

        for i in range(allowed_history, total_history):
            session = await Session.find_first_by_id(session_ids[i])
            assert session is None


@pytest.mark.anyio()
async def test_session_expiry_time_limit(
    active_session: ActiveSession,
    session_factory: Factory[Session],
    user: User,
) -> None:
    expired_session_id = (await session_factory(expiry=datetime.fromtimestamp(0))).id

    async with active_session():
        await Session.cleanup_history_by_user(user_id=user.id)

    async with active_session():
        session = await Session.find_first_by_id(expired_session_id)
        assert session is None
