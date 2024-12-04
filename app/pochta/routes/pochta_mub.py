from email.message import EmailMessage
from typing import Annotated

from fastapi import File, Form, HTTPException, UploadFile

from app.common.config import EMAIL_USERNAME, smtp_client
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["pochta mub"])


@router.post(
    "/emails-from-file/",
    status_code=204,
    summary="Send email from uploaded file",
)
async def send_email_from_file(
    receiver: Annotated[str, Form()],
    subject: Annotated[str, Form()],
    file: Annotated[UploadFile, File(description="text/html")],
) -> None:
    if smtp_client is None:
        raise HTTPException(500, "Email config is not set")

    message = EmailMessage()
    message["To"] = receiver
    message["Subject"] = subject
    message["From"] = EMAIL_USERNAME
    message.set_content((await file.read()).decode("utf-8"), subtype="html")

    async with smtp_client as smtp:
        await smtp.send_message(message)
