from collections.abc import AsyncIterator

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.users.models.users_db import User
from tests.common.assert_contains_ext import assert_nodata_response, assert_response


@pytest.fixture()
async def image(faker: Faker) -> bytes:
    return faker.graphic_webp_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
async def _create_avatar(user: User, image: bytes) -> AsyncIterator[None]:
    with user.avatar_path.open("wb") as f:
        f.write(image)
    yield
    user.avatar_path.unlink(missing_ok=True)


@pytest.mark.anyio()
async def test_avatar_uploading(
    authorized_client: TestClient, user: User, image: bytes
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/users/current/avatar/",
            files={"avatar": ("avatar.webp", image, "image/webp")},
        )
    )

    assert user.avatar_path.is_file()
    with user.avatar_path.open("rb") as f:
        assert f.read() == image

    user.avatar_path.unlink()


@pytest.mark.anyio()
async def test_avatar_uploading_wrong_format(
    authorized_client: TestClient, faker: Faker
) -> None:
    assert_response(
        authorized_client.put(
            "/api/users/current/avatar/",
            files={"avatar": ("avatar", faker.random.randbytes(100), "image/webp")},
        ),
        expected_code=415,
        expected_json={"detail": "Invalid image format"},
    )


@pytest.mark.anyio()
@pytest.mark.usefixtures("_create_avatar")
async def test_avatar_replacing(
    authorized_client: TestClient, user: User, faker: Faker
) -> None:
    image_2 = faker.graphic_webp_file(raw=True)
    assert_nodata_response(
        authorized_client.put(
            "/api/users/current/avatar/",
            files={"avatar": ("avatar.webp", image_2, "image/webp")},
        )
    )

    assert user.avatar_path.is_file()
    with user.avatar_path.open("rb") as f:
        assert f.read() == image_2


@pytest.mark.anyio()
@pytest.mark.usefixtures("_create_avatar")
async def test_avatar_deletion(authorized_client: TestClient, user: User) -> None:
    assert_nodata_response(authorized_client.delete("/api/users/current/avatar/"))

    assert not user.avatar_path.is_file()


@pytest.mark.anyio()
@pytest.mark.usefixtures("_create_avatar")
async def test_mub_user_deletion_with_avatar(
    mub_client: TestClient, user: User
) -> None:
    assert_nodata_response(mub_client.delete(f"/mub/users/{user.id}/"))

    assert not user.avatar_path.is_file()
