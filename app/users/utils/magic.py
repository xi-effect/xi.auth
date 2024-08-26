from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from aenum import extend_enum  # type: ignore[import-untyped]

from app.common.fastapi_ext import Responses

T = TypeVar("T", bound=Enum)


def include_responses(*included_enums: type[Responses]) -> Callable[[type[T]], type[T]]:
    def wrapper(new_enum: type[T]) -> type[T]:
        for included_enum in included_enums:
            for name, member in included_enum.__members__.items():
                extend_enum(
                    new_enum,
                    name,
                    member.status_code,
                    member.detail,
                    member.headers,
                )
        return new_enum

    return wrapper
