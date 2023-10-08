from httpx import Response
from pydantic_marshals.contains import TypeChecker, assert_contains


def assert_response(
    response: Response,
    *,
    expected_code: int = 200,
    expected_json: TypeChecker,
    expected_headers: dict[str, TypeChecker] | None = None,
) -> Response:
    assert_contains(
        {
            "status_code": response.status_code,
            "json_data": response.json(),
            "headers": response.headers,
        },
        {
            "status_code": expected_code,
            "json_data": expected_json,
            "headers": expected_headers or {},
        },
    )
    return response
