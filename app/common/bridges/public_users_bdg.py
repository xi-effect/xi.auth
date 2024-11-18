from httpx import AsyncClient

from app.common.config import BRIDGE_BASE_URL
from app.common.schemas.vacancy_form_sch import VacancyFormSchema


class PublicUsersBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=BRIDGE_BASE_URL,
        )

    async def apply_for_vacancy(self, vacancy_form: VacancyFormSchema) -> None:
        response = await self.client.post(
            "/api/vacancy-applications/", json=vacancy_form.model_dump()
        )
        response.raise_for_status()
