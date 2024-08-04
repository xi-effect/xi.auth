from typing import Generic, TypeVar

from aiogram.types import ChatMemberUpdated, Message, Update, User
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

T = TypeVar("T", bound="BaseModel")


class BaseModelFactory(ModelFactory[T], Generic[T]):
    __is_base_factory__ = True
    __use_defaults__ = True


class UpdateFactory(BaseModelFactory[Update]):
    __model__ = Update


class MessageFactory(BaseModelFactory[Message]):
    __model__ = Message


class UserFactory(ModelFactory[User]):
    __model__ = User


class ChatMemberUpdatedFactory(BaseModelFactory[ChatMemberUpdated]):
    __model__ = ChatMemberUpdated
