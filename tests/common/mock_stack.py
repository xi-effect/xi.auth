from collections.abc import Iterator
from contextlib import ExitStack
from typing import Any, overload
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from pydantic_core import PydanticUndefined, PydanticUndefinedType


class MockStack(ExitStack):
    @overload
    def enter_mock(
        self,
        target: Any,
        attribute: str,
        /,
        *,
        mock: Mock | None = None,
        return_value: Any | None = None,
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
    ) -> Mock: ...

    @overload
    def enter_mock(
        self,
        target: str,
        /,
        *,
        mock: Mock | None = None,
        return_value: Any | None = None,
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
    ) -> Mock: ...

    def enter_mock(
        self,
        target: Any,
        attribute: str | None = None,
        mock: Mock | None = None,
        return_value: Any | None = None,
        property_value: Any | None | PydanticUndefinedType = PydanticUndefined,
    ) -> Mock:
        if mock is None:
            if property_value is PydanticUndefined:
                mock = Mock(return_value=return_value)
            else:
                mock = PropertyMock(return_value=property_value)
        if attribute is None:
            return self.enter_context(patch(target, mock))
        return self.enter_context(patch.object(target, attribute, mock))

    @overload
    def enter_async_mock(
        self,
        target: Any,
        attribute: str,
        /,
        *,
        return_value: Any | None = None,
    ) -> AsyncMock: ...

    @overload
    def enter_async_mock(
        self,
        target: str,
        /,
        *,
        return_value: Any | None = None,
    ) -> AsyncMock: ...

    def enter_async_mock(
        self,
        target: Any,
        attribute: str | None = None,
        *,
        return_value: Any | None = None,
    ) -> AsyncMock:
        mock = AsyncMock(return_value=return_value)
        if attribute is None:
            return self.enter_context(patch(target, mock))
        return self.enter_context(patch.object(target, attribute, mock))

    @overload
    def enter_patch(self, target: Any, attribute: str, /) -> Mock: ...

    @overload
    def enter_patch(self, target: str, /) -> Mock: ...

    def enter_patch(self, target: Any, attribute: str | None = None) -> Mock:
        if attribute is None:
            return self.enter_context(patch(target))
        return self.enter_context(patch.object(target, attribute))


@pytest.fixture()
def mock_stack() -> Iterator[MockStack]:
    with MockStack() as stack:
        yield stack
