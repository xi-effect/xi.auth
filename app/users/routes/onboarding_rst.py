from typing import Literal

from pydantic import BaseModel
from starlette.status import HTTP_409_CONFLICT

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.models.users_db import OnboardingStage, User
from app.users.utils.authorization import AuthorizedUser

router = APIRouterExt(tags=["onboarding"])


class CommunityChoiceModel(BaseModel):
    display_name: User.DisplayNameRequiredType


class OnboardingResponses(Responses):
    INVALID_TRANSITION = (HTTP_409_CONFLICT, "Invalid transition")


ValidForwardStages = Literal[
    OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_CREATE,
    OnboardingStage.COMMUNITY_INVITE,
    OnboardingStage.COMPLETED,
]

ValidReturnStages = Literal[
    OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_CREATE,
    OnboardingStage.COMMUNITY_INVITE,
]

forward_valid_transitions: set[tuple[OnboardingStage, ValidForwardStages]] = {
    (OnboardingStage.CREATED, OnboardingStage.COMMUNITY_CHOICE),
    (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_CREATE),
    (OnboardingStage.COMMUNITY_CHOICE, OnboardingStage.COMMUNITY_INVITE),
    (OnboardingStage.COMMUNITY_CREATE, OnboardingStage.COMPLETED),
    (OnboardingStage.COMMUNITY_INVITE, OnboardingStage.COMPLETED),
}

return_transitions: dict[ValidReturnStages, OnboardingStage] = {
    OnboardingStage.COMMUNITY_CHOICE: OnboardingStage.CREATED,
    OnboardingStage.COMMUNITY_CREATE: OnboardingStage.COMMUNITY_CHOICE,
    OnboardingStage.COMMUNITY_INVITE: OnboardingStage.COMMUNITY_CHOICE,
}


async def make_onboarding_transition(
    user: AuthorizedUser,
    stage: OnboardingStage,
) -> None:
    if (user.onboarding_stage, stage) not in forward_valid_transitions:
        raise OnboardingResponses.INVALID_TRANSITION.value
    user.onboarding_stage = stage


@router.put(
    "/stages/community-choice/",
    status_code=204,
    responses=OnboardingResponses.responses(),
    summary="Proceed to the community choice onboarding stage",
)
async def proceed_to_community_choice(
    user: AuthorizedUser,
    stage_data: CommunityChoiceModel,
) -> None:
    await make_onboarding_transition(user, OnboardingStage.COMMUNITY_CHOICE)
    user.update(**stage_data.model_dump())


@router.put(
    "/stages/{stage}/",
    status_code=204,
    responses=OnboardingResponses.responses(),
    summary="Proceed to the specified onboarding stage",
)
async def proceed_to_specified_stage(
    user: AuthorizedUser,
    stage: ValidForwardStages,
) -> None:
    await make_onboarding_transition(user, stage)


@router.delete(
    "/stages/{stage}/",
    status_code=204,
    responses=OnboardingResponses.responses(),
    summary="Return to the previous onboarding stage",
)
async def return_to_previous_onboarding_stage(
    user: AuthorizedUser,
    stage: ValidReturnStages,
) -> None:
    if stage is not user.onboarding_stage:
        raise OnboardingResponses.INVALID_TRANSITION.value
    user.onboarding_stage = return_transitions[stage]
