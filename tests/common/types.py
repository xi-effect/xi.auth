from typing import Any, Generic, Protocol, TypeVar

Product = TypeVar("Product", covariant=True)


class Factory(Protocol[Product]):
    async def __call__(self, **kwargs: Any) -> Product:  # noqa: U100  # bug
        pass


ParamType = TypeVar("ParamType")


class PytestRequest(Generic[ParamType]):
    @property
    def param(self) -> ParamType:
        raise NotImplementedError


AnyJSON = dict[str, Any]
