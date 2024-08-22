from typing import Annotated

from discord_webhook import AsyncDiscordWebhook
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.common.config import DEMO_WEBHOOK_URL, VACANCY_WEBHOOK_URL
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["forms"])


async def execute_discord_webhook(url: str | None, content: str) -> None:
    if url is None:
        raise HTTPException(500, "Webhook url is not set")

    webhook = AsyncDiscordWebhook(  # type: ignore[no-untyped-call]
        url=url, content=content
    )
    (await webhook.execute()).raise_for_status()


class DemoFormSchema(BaseModel):
    name: str
    contacts: Annotated[list[str], Field(min_length=1)]


@router.post(
    "/demo-applications/", status_code=204, summary="Apply for a demonstration"
)
async def apply_for_demonstration(demo_form: DemoFormSchema) -> None:
    await execute_discord_webhook(
        url=DEMO_WEBHOOK_URL,
        content="\n- ".join(
            ["**Новая запись на демонстрацию:**", f"Имя: {demo_form.name}"]
            + demo_form.contacts
        ),
    )


class VacancyFormSchema(BaseModel):
    name: str
    telegram: str
    position: str
    link: str
    message: str | None = None


@router.post("/vacancy-applications/", status_code=204, summary="Apply for a vacancy")
async def apply_for_vacancy(vacancy_form: VacancyFormSchema) -> None:
    content = (
        f"**Новый отклик на вакансию {vacancy_form.position}**\n"
        + f"- Имя: {vacancy_form.name}\n"
        + f"- Телеграм: {vacancy_form.telegram}\n"
        + f"- [Резюме](<{vacancy_form.link}>)\n"
    )
    if vacancy_form.message is not None:
        content = f"{content}>>> {vacancy_form.message}"

    await execute_discord_webhook(url=VACANCY_WEBHOOK_URL, content=content)
