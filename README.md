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
docker compose down
```

### Links
После запуска приложения становятся доступны следующие порты и ссылки:
- `5432`: порт для подключения к базе данных PostgreSQL
- `5672`: порт для подключения к брокеру сообщений RabbitMQ
- [`http://localhost:15672`](http://localhost:15672): management-консоль для RabbitMQ (логин и пароль: guest)
- [`http://localhost:5100`](http://localhost:5100/docs): автоматическая OpenAPI-документация основного приложения

### Run Supbot
Этот раздел для тех, кто хочет запустить supbot-а локально. В целом можно использовать стейджинг для тестирования бота, но тогда тестирование станет последним этапом, после миграций и тестов. API можно запускать и без бота, тесты (в том числе тесты бота) будут работать локально даже без настроек ниже

Итак, настроить себе тестовое окружение локально не слишком сложно:
1. Создать себе бота для локального тестирования через [@BotFather](https://t.me/BotFather)
2. Создать приватный канал в телеграмме также для тестирования, добавить туда своего бота администратором
3. В настройках каналов найти "Добавить Обсуждение" / "Add Discussion" и создать там новую приватную группу
4. Разрешить добавлять бота в группы, если не разрешено (BotFather > /mybots > BOT > Bot Settings > Allow Groups? > Turn on)
5. Выключить у бота "Group Privacy", если включена (BotFather > /mybots > BOT > Bot Settings > Group Privacy > Turn off)
6. Добавить бота в группу (важно сделать это именно после шагов 4-5, иначе нужно выгнать бота и добавить заново)
7. Если хочется, можно теперь запретить добавлять бота в группы, т.е. отменить шаг 4 (шаг 5 отменять нельзя)
8. Дальше настраиваем переменные окружения в файле `.env` (не заливать в git!):
   - `SUPBOT_POLLING` включить polling (поставить значение `"1"`), чтобы не тыкаться с webhook-ом
   - `SUPBOT_TOKEN` это токен бота, созданного на первом этапе
   - `SUPBOT_GROUP_ID` это id группы, в которую добавлен бот (id можно получить переслав сообщение из группы [боту](https://t.me/get_id_channel_bot) (начинается с -100))
   - `SUPBOT_CHANNEL_ID` это id канала, в который добавлен бот (id можно получить переслав сообщение из канала [боту](https://t.me/get_id_channel_bot) (начинается с -100))

Пример `.env`-файла:
```txt
SUPBOT_POLLING=1
SUPBOT_TOKEN=0000000000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
SUPBOT_GROUP_ID=-100123456
SUPBOT_CHANNEL_ID=-100123456
```

После всех настроек можно запускать приложение, как сказано в [инструкции выше](#run). Важно использовать `--port 5100`, а если хочется использовать иной порт, то его нужно указать в переменной `SUPBOT_WEBHOOK_URL` в `.env`, например, так:
```txt
SUPBOT_WEBHOOK_URL=http://localhost:8000
```

### Pochta
Для локального запуска сервиса можно использовать Gmail:
1. Заходим в управление аккаунтом Google
2. Включаем двухэтапную аутентификацию в разделе безопасность (если еще не включена)
3. Находим в строке поиска "пароли приложений" или "app pass"
4. Называем как угодно и копируем полученный пароль
5. Добавляем в .env файл следующего формата:

```txt
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=asdf lkjh zxcv qere
EMAIL_HOSTNAME=smtp.gmail.com
```

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
docker compose up -d
# выключить обратно
docker compose down

# тоже самое, но вместе с докеризированным приложением
docker compose --profile app up -d
docker compose --profile app down

# смотреть логи в реальном времени
docker compose logs --follow <сервис>
docker compose logs --follow mq  # пример

# проверить статусы сервисов
docker compose ps -a

# зайти в какой-то контейнер
docker compose exec -ti <сервис> <shell-команда>
docker compose exec -ti db psql -U test -d test  # пример
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
