# Python Template
## Basics
### Stack
- Python
- FastAPI
- SQLAlchemy 2.0
- RabbitMQ (soon)
- Poetry
- Linters (flake8, wemake-style-guide, mypy)
- Formatters (black, autoflake)
- Pre-commit
- Pytest

Версии можно найти в [pyproject.toml](./pyproject.toml)

### Install
```sh
pip install poetry==1.4.1
poetry install
pre-commit install
```

### Run
Запуск бекенда локально:
```sh
uvicorn app.main:app --reload
```

## Docker Compose
**Пока что не пригодится при локальной разработке, но может помочь в будущем**

### Контейнеры
- `db`: локальная база данных для тестов и проверок, сбрасывается при рестарте
- `api`: докеризированное приложение основного api сервиса, сделано для полных проверок и работает только с `--profile app`

### Команды
```sh
# запустить все вспомогательные сервисы для локальной разработки
docker-compose up -d
# выключить обратно
docker-compose down

# тоже самое, но вместе с докеризированным приложением
docker-compose --profile app up -d
docker-compose --profile app down

# смотреть логи в реальном времени
docker-compose logs --follow <сервис>
docker-compose logs --follow mongo  # пример

# проверить статусы сервисов
docker-compose ps -a

# зайти в какой-то контейнер
docker-compose exec <сервис> <shell-команда>
docker-compose exec mongo sh  # пример
```
