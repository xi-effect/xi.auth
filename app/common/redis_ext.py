import asyncio
import logging
from collections.abc import Callable
from typing import Any, Final, Protocol, TypeVar, get_type_hints, ClassVar

from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from app.common.config import settings

BLOCK_TIME_MS: Final[int] = 2000

T = TypeVar("T", bound=BaseModel, contravariant=True)


class MessageHandlerProtocol(Protocol[T]):
    async def __call__(self, message: T) -> None:
        pass
        # TODO nq remove protocol


class ConsumerException(Exception):
    message: ClassVar[str]
    requeue: ClassVar[bool]

    def __init__(self, message_override: str | None = None) -> None:
        super().__init__(message_override or self.message)


class SMTPTimeoutException(ConsumerException):
    message = "SMTP sad(("
    requeue = True


class RedisStreamConsumer:
    def __init__(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        model: type[T],
        message_handler: MessageHandlerProtocol[T],
    ) -> None:
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.model = model
        self.message_handler = message_handler

        self.redis_client = Redis.from_url(
            url=settings.redis_dsn,
            decode_responses=True,
            retry=Retry(backoff=ExponentialBackoff(cap=10, base=1), retries=10),
            retry_on_error=[ConnectionError, TimeoutError],
        )

    async def create_group_if_not_exist(self) -> None:
        try:
            await self.redis_client.xgroup_create(
                name=self.stream_name,
                groupname=self.group_name,
                id="$",
                mkstream=True,
            )
        except ResponseError as response_exc:
            # Не поднимаем ошибку о том, что группа уже создана (`BUSYGROUP`)
            if "BUSYGROUP" not in str(response_exc):
                raise

    async def process_message(self, message_id: str, data: dict[str, str]) -> None:
        # TODO nq fixup error messages & expand extras
        try:
            validated_data = self.model.model_validate(data)
        except ValidationError as e:  # TODO nq mb move to handle_messages
            logging.error(
                "Invalid message payload",
                extra={"original_message": data},
                exc_info=e,
            )
            await self.redis_client.xack(  # type: ignore[no-untyped-call]
                self.stream_name,
                self.group_name,
                message_id,
            )
            return

        try:
            await self.message_handler(validated_data)
        # TODO nq ConsumerException?
        except Exception as e:  # noqa PIE786  # TODO nq mb move to handle_messages
            logging.error(
                f"Error in {self.consumer_name} while processing message {data}",
                exc_info=e,
            )

        await self.redis_client.xack(  # type: ignore[no-untyped-call]
            self.stream_name,
            self.group_name,
            message_id,
        )

    async def handle_messages(self) -> None:
        await self.create_group_if_not_exist()

        last_message_id: str = "0"

        while True:  # noqa WPS457 # required for continuous message handling
            messages = await self.redis_client.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_name: last_message_id},
                count=1,
                block=BLOCK_TIME_MS,
            )
            if len(messages) == 0:
                continue
            elif len(messages[0][1]) == 0:
                last_message_id = ">"
                continue

            message_id, data = messages[0][1][0]
            await self.process_message(message_id, data)
            if last_message_id != ">":
                last_message_id = message_id

    async def run(self) -> None:
        while True:  # noqa WPS457 # required for continuous running
            try:
                await self.handle_messages()
            except asyncio.CancelledError:
                await self.redis_client.close()  # TODO nq move to destruct?
                break
            except Exception as e:  # noqa PIE786
                logging.error(
                    f"An error occurred in worker {self.consumer_name}: {e}",
                    exc_info=e,
                )
                await asyncio.sleep(2)
                # TODO nq backoff & give up after 10 tries
                #   or remove `while True` completely
                continue


class RedisRouter:
    def __init__(self) -> None:
        self.consumers: list[RedisStreamConsumer] = []
        self.tasks: list[asyncio.Task[Any]] = []

    def add_consumer(
        self, stream_name: str, group_name: str, consumer_name: str
    ) -> Callable[[MessageHandlerProtocol[T]], None]:
        def redis_consumer_wrapper(func: MessageHandlerProtocol[T]) -> None:
            model = next(iter(get_type_hints(func).values()))  # TODO nq signature
            if not issubclass(model, BaseModel):
                raise TypeError(f"Expected a subclass of BaseModel, got {model}")
            worker_instance = RedisStreamConsumer(
                stream_name=stream_name,
                group_name=group_name,
                consumer_name=consumer_name,
                model=model,
                message_handler=func,
            )
            self.consumers.append(worker_instance)

        return redis_consumer_wrapper

    def include_router(self, router: "RedisRouter") -> None:
        self.consumers.extend(router.consumers)

    async def run_consumers(self) -> None:
        self.tasks.extend(
            [asyncio.create_task(consumer.run()) for consumer in self.consumers]
        )

    async def terminate_consumers(self) -> None:
        for task in self.tasks:
            task.cancel()
