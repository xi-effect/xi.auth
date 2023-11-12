from starlette.testclient import TestClient

from tests.utils import assert_nodata_response


def test_cors(client: TestClient) -> None:
    assert_nodata_response(
        client.options("/api/signup", headers={"Origin": "hello"}),
        expected_code=405,
        expected_headers={
            "allow": "POST",
            "access-control-allow-origin": "*",
            "access-control-allow-credentials": "true",
        },
    )
