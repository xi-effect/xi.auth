from collections.abc import Iterator
from typing import Annotated, BinaryIO

from discord_webhook import AsyncDiscordWebhook
from fastapi import Form, HTTPException

from app.common.config import settings
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.demo_form_sch import DemoFormSchema
from app.users.dependencies.forms_dep import ResumeFile

router = APIRouterExt(tags=["forms"])


async def execute_discord_webhook(
    url: str | None,
    content: str,
    attachment: tuple[str | None, BinaryIO] | None = None,
) -> None:
    if url is None:
        raise HTTPException(500, "Webhook url is not set")

    webhook = AsyncDiscordWebhook(  # type: ignore[no-untyped-call]
        url=url, content=content
    )
    if attachment is not None:
        # async discord webhook is badly typed: it uses httpx, there these types are supported
        webhook.add_file(file=attachment[1], filename=attachment[0])  # type: ignore[arg-type]
    (await webhook.execute()).raise_for_status()


@router.post(
    "/demo-applications/", status_code=204, summary="Apply for a demonstration"
)
async def apply_for_demonstration(demo_form: DemoFormSchema) -> None:
    await execute_discord_webhook(
        url=settings.demo_webhook_url,
        content="\n- ".join(
            ["**Новая запись на демонстрацию:**", f"Имя: {demo_form.name}"]
            + demo_form.contacts
        ),
    )


def iter_vacancy_message_lines(
    position: str, name: str, telegram: str, message: str | None
) -> Iterator[str]:
    yield f"**Новый отклик на вакансию {position.lower()}**"
    yield f"- Имя: {name}"
    yield f"- Телеграм: {telegram}"
    if message is not None and message != "":
        yield f">>> {message}"


@router.post(
    "/v2/vacancy-applications/", status_code=204, summary="Apply for a vacancy"
)
async def apply_for_vacancy(
    position: Annotated[str, Form()],
    name: Annotated[str, Form()],
    telegram: Annotated[str, Form()],
    resume: ResumeFile,
    message: Annotated[str | None, Form()] = None,
) -> None:
    await execute_discord_webhook(
        url=settings.vacancy_webhook_url,
        content="\n".join(
            iter_vacancy_message_lines(
                position=position,
                name=name,
                telegram=telegram,
                message=message,
            )
        ),
        attachment=(resume.filename, resume.file),
    )
