import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.models.users_db import OnboardingStage, User
from tests.conftest import ActiveSession
from tests.utils import assert_nodata_response, assert_response, get_db_user


@pytest.mark.parametrize("method", ["PUT", "DELETE"])
@pytest.mark.parametrize(
    "stage",
    [
        OnboardingStage.CREATED,
        OnboardingStage.COMMUNITY_CHOICE,
        OnboardingStage.COMMUNITY_CREATE,
        OnboardingStage.COMMUNITY_INVITE,
        OnboardingStage.COMPLETED,
    ],
)
@pytest.mark.anyio()
async def test_onboarding_unauthorized(
    client: TestClient,
    method: str,
    stage: OnboardingStage,
) -> None:
    assert_response(
        client.request(method, f"/api/onboarding/stages/{stage.value}/"),
        expected_json={"detail": "Authorization is missing"},
        expected_code=401,
    )


@pytest.mark.anyio()
async def test_proceeding_to_community_choice_in_onboarding(
    authorized_client: TestClient,
    active_session: ActiveSession,
    user: User,
    faker: Faker,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/onboarding/stages/community-choice/",
            json={"display_name": faker.name()},
        )
    )

    async with active_session():
        assert (
            await get_db_user(user)
        ).onboarding_stage is OnboardingStage.COMMUNITY_CHOICE


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMPLETED),
    ],
)
async def test_proceeding_in_onboarding(
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_nodata_response(
        authorized_client.put(f"/api/onboarding/stages/{target_stage.value}/")
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is target_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.CREATED, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMPLETED),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMPLETED),
    ],
)
async def test_proceeding_in_onboarding_invalid_transition(
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_response(
        authorized_client.put(
            f"/api/onboarding/stages/{target_stage.value}/",
        ),
        expected_json={"detail": "Invalid transition"},
        expected_code=409,
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is current_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.CREATED),
    ],
)
async def test_returning_in_onboarding(
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_nodata_response(
        authorized_client.delete(f"/api/onboarding/stages/{current_stage.value}/")
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is target_stage


@pytest.mark.anyio()
@pytest.mark.parametrize(
    ("current_stage", "target_stage"),
    [
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMMUNITY_INVITE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CHOICE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_CREATE),
        (OnboardingStage.COMPLETED, OnboardingStage.COMMUNITY_INVITE),
    ],
)
async def test_returning_in_onboarding_invalid_transition(
    authorized_client: TestClient,
    user: User,
    current_stage: OnboardingStage,
    target_stage: OnboardingStage,
    active_session: ActiveSession,
) -> None:
    async with active_session():
        (await get_db_user(user)).onboarding_stage = current_stage

    assert_response(
        authorized_client.delete(
            f"/api/onboarding/stages/{target_stage.value}/",
        ),
        expected_json={"detail": "Invalid transition"},
        expected_code=409,
    )

    async with active_session():
        assert (await get_db_user(user)).onboarding_stage is current_stage
