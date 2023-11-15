from faker import Faker
from starlette.testclient import TestClient

from tests.utils import assert_nodata_response


def test_tailing_stash(client: TestClient) -> None:
    assert_nodata_response(
        client.get("/api/signup", follow_redirects=False),
        expected_code=307,
    )


def test_cors(client: TestClient, faker: Faker) -> None:
    hostname: str = faker.hostname()
    assert_nodata_response(
        client.options(
            "/api/signup/",
            headers={"Origin": hostname, "Access-Control-Request-Method": "POST"},
        ),
        expected_code=200,
        expected_headers={
            "access-control-allow-origin": hostname,
            "access-control-allow-credentials": "true",
        },
    )
    assert_nodata_response(
        client.post(
            "/api/signup/",
            headers={"Origin": hostname},
        ),
        expected_code=422,
        expected_headers={
            "access-control-allow-origin": hostname,
            "access-control-allow-credentials": "true",
        },
    )
