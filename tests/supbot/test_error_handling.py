import logging

import pytest
from aiogram.types import ErrorEvent

from app.supbot.routers.error_handling_tgm import error_handler
from tests.common.mock_stack import MockStack
from tests.supbot.factories import UpdateFactory


# This is a unit test
@pytest.mark.anyio()
async def test_handling_errors(
    mock_stack: MockStack,
) -> None:
    exception = Exception("Test exception")

    logging_error_mock = mock_stack.enter_mock(logging, "error")

    assert (
        await error_handler(
            ErrorEvent(update=UpdateFactory.build(), exception=exception)
        )
        is True
    )

    logging_error_mock.assert_called_once_with(
        f"Error in supbot: {exception}", exc_info=exception
    )
