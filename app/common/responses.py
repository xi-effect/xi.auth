from enum import Enum
from typing import Any

from fastapi import HTTPException


class Responses(HTTPException, Enum):
    value: HTTPException

    @classmethod
    def responses(cls) -> dict[str | int, dict[str, Any]]:
        result: dict[str | int, dict[str, Any]] = {}
        code_counts: dict[int, int] = {}
        for response in cls.__members__.values():
            error = response.value
            code_counts[error.status_code] = code_counts.get(error.status_code, -1) + 1

            status_code = str(error.status_code) + " " * code_counts[error.status_code]
            result[status_code] = {
                "description": error.detail,
                "content": {
                    "application/json": {
                        "schema": {"properties": {"detail": {"const": error.detail}}},
                        "example": {"detail": error.detail},
                    }
                },
            }
        return result
