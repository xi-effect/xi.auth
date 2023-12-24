# xi.auth
## How To
### Install
Эта установка нужна для запуска бэкенда локально и запуска форматеров, линтеров и тайп чекеров перед каждым коммитом. Для корректной работы требуется Python 3.11

```sh
pip install poetry==1.4.1
poetry install
pre-commit install
```

### Run
Сначала нужно запустить зависимости (нужен настроенный docker):
```sh
docker compose up -d
```

Запуск бэкенда локально:
```sh
uvicorn app.main:app --port 5100 --reload
```

Остановить зависимости:
```sh
docker-compose down
```

### Links
После запуска приложения становятся доступны следующие порты и ссылки:
- `5432`: порт для подключения к базе данных PostgreSQL
- `5672`: порт для подключения к брокеру сообщений RabbitMQ
- [`http://localhost:15672`](http://localhost:15672): management-консоль для RabbitMQ (логин и пароль: guest)
- [`http://localhost:5100`](http://localhost:5100/docs): автоматическая OpenAPI-документация основного приложения

## Info
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

### Контейнеры
- `mq`: локальный брокер RabbitMQ, сбрасывается при рестарте
- `db`: локальная база данных PostgreSQL для тестов и проверок, сбрасывается при рестарте
- `alembic`: специальный контейнер для работы с миграциями, работает только с `--profile migration`
- `app`: докеризированное приложение основного API сервиса, сделано для полных проверок и работает только с `--profile app`

### Commands
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
docker-compose logs --follow mq  # пример

# проверить статусы сервисов
docker-compose ps -a

# зайти в какой-то контейнер
docker-compose exec -ti <сервис> <shell-команда>
docker-compose exec -ti db psql -U test -d test  # пример
```

### Alembic
Используется для автосоздания миграций БД. Запуск вспомогательного контейнера для миграций:
```sh
docker compose run --build --rm -ti alembic
```
Команды для самих миграций:
```sh
alembic upgrade head
alembic revision --autogenerate -m "<message>" --rev-id "<issue>"
```
Сбросить базу или просто завершить работу с миграциями:
```sh
docker compose --profile migration down
```
