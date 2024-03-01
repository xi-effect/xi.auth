from typing import Annotated

from discord_webhook import AsyncDiscordWebhook
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.config import DEMO_WEBHOOK_URL


class DemoFormSchema(BaseModel):
    name: str
    contacts: Annotated[list[str], Field(min_length=1)]


router = APIRouter(tags=["forms"])


@router.post(
    "/demo-applications/", status_code=204, summary="Apply for a demonstration"
)
async def apply_for_demonstration(demo_form: DemoFormSchema) -> None:
    if DEMO_WEBHOOK_URL is None:
        raise HTTPException(500, "Webhook url is not set")

    webhook = AsyncDiscordWebhook(  # type: ignore[no-untyped-call]
        url=DEMO_WEBHOOK_URL,
        content="\n- ".join(
            ["**Новая запись на демонстрацию:**", f"Имя: {demo_form.name}"]
            + demo_form.contacts
        ),
    )
    (await webhook.execute()).raise_for_status()
