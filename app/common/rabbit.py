from __future__ import annotations

import json
import logging
from abc import ABC
from collections.abc import Sequence
from typing import Any

from aio_pika import Message
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractQueue,
    DeliveryMode,
    ExchangeType,
)


class AbstractRabbitProducer:  # pragma: no coverage
    async def connect(self, connection: AbstractConnection) -> None:
        raise NotImplementedError()

    def is_uninitialized(self) -> bool:
        raise NotImplementedError()

    async def send_message(self, message: Message, **kwargs: Any) -> None:
        raise NotImplementedError()

    async def send_event(self, data: Any, event_name: str | None = None) -> None:
        if self.is_uninitialized():
            raise RuntimeError("Client is not connected")
        message = Message(
            body=json.dumps(data).encode("utf-8"),
            headers={"event_name": event_name},
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await self.send_message(message)
        logging.info(
            f"Sending event '{event_name}'",
            extra={"outgoing_message": message},
        )


class RabbitExchangeProducer(AbstractRabbitProducer, ABC):  # pragma: no coverage
    def __init__(self) -> None:
        self.exchange: AbstractExchange | None = None

    def is_uninitialized(self) -> bool:
        return self.exchange is None

    async def send_message(
        self,
        message: Message,
        *,
        routing_key: str = "",
        **kwargs: Any,
    ) -> None:
        if self.exchange is None:
            raise RuntimeError("Exchange not initialized")
        await self.exchange.publish(message=message, routing_key=routing_key, **kwargs)


class RabbitDirectProducer(RabbitExchangeProducer):  # pragma: no coverage
    def __init__(self, queue_name: str) -> None:
        super().__init__()
        self.queue_name: str = queue_name

    async def connect(self, connection: AbstractConnection) -> None:
        channel: AbstractChannel = await connection.channel()
        self.exchange = channel.default_exchange
        await channel.declare_queue(self.queue_name)

    async def send_message(self, message: Message, **kwargs: Any) -> None:
        kwargs["routing_key"] = self.queue_name
        return await super().send_message(message, **kwargs)


class RabbitFanoutProducer(RabbitExchangeProducer):  # pragma: no coverage
    def __init__(self, exchange: str, *queues: str) -> None:
        super().__init__()
        self.exchange_name: str = exchange
        self.queues: Sequence[str] = queues

    async def connect(self, connection: AbstractConnection) -> None:
        channel: AbstractChannel = await connection.channel()
        self.exchange = await channel.declare_exchange(
            name=self.exchange_name,
            type=ExchangeType.FANOUT,
        )
        for queue_name in self.queues:
            queue: AbstractQueue = await channel.declare_queue(queue_name)
            await queue.bind(self.exchange)
