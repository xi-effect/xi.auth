from typing import BinaryIO

from httpx import AsyncClient

from app.common.config import settings
from app.common.schemas.vacancy_form_sch import VacancyFormSchema


class PublicUsersBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=settings.bridge_base_url,
        )

    async def apply_for_vacancy(
        self, vacancy_form: VacancyFormSchema, resume: tuple[str, BinaryIO, str]
    ) -> None:
        response = await self.client.post(
            "/api/v2/vacancy-applications/",
            data=vacancy_form.model_dump(),
            files={"resume": resume},
        )
        response.raise_for_status()
