from collections.abc import Iterator
from typing import Annotated, BinaryIO

from discord_webhook import AsyncDiscordWebhook
from fastapi import File, HTTPException, UploadFile
from filetype import filetype  # type: ignore[import-untyped]
from filetype.types.archive import Pdf  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from app.common.config import settings
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.vacancy_form_sch import VacancyFormSchema

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


class DemoFormSchema(BaseModel):
    name: str
    contacts: Annotated[list[str], Field(min_length=1)]


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


@router.post(
    "/vacancy-applications/",
    status_code=204,
    summary="Use POST /api/v2/vacancy-applications/ instead",
    deprecated=True,
)
async def apply_for_vacancy_old(vacancy_form: VacancyFormSchema) -> None:
    content = (
        f"**Новый отклик на вакансию {vacancy_form.position}**\n"
        + f"- Имя: {vacancy_form.name}\n"
        + f"- Телеграм: {vacancy_form.telegram}\n"
        + f"- [Резюме](<{vacancy_form.link}>)\n"
    )
    if vacancy_form.message is not None:
        content = f"{content}>>> {vacancy_form.message}"

    await execute_discord_webhook(url=settings.vacancy_webhook_url, content=content)


class FileFormatResponses(Responses):
    WRONG_FORMAT = 415, "Invalid file format"


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
    position: Annotated[str, File()],
    name: Annotated[str, File()],
    telegram: Annotated[str, File()],
    resume: UploadFile,
    message: Annotated[str | None, File()] = None,
) -> None:
    if not filetype.match(resume.file, [Pdf()]):
        raise FileFormatResponses.WRONG_FORMAT.value

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
