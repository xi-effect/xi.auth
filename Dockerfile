FROM python:3.11-alpine

WORKDIR /backend
RUN pip install --upgrade pip

RUN pip install poetry==1.5.1
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main

COPY ./app /backend/app

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
