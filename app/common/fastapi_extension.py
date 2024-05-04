from collections import defaultdict
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Any, ParamSpec, TypeVar

from fastapi import Depends, HTTPException
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, APIRouter

ResponsesSchema = dict[str | int, dict[str, Any]]


class Responses(HTTPException, Enum):
    value: HTTPException

    @classmethod
    def responses(cls, continue_from: ResponsesSchema | None = None) -> ResponsesSchema:
        code_counts: dict[int, int] = defaultdict(int)
        if continue_from is not None:
            for code in continue_from.keys():
                code_counts[int(code)] += 1

        result: ResponsesSchema = {}
        for response in cls.__members__.values():
            error = response.value
            code_counts[error.status_code] += 1

            status_code = str(error.status_code) + " " * code_counts[error.status_code]
            result[status_code] = {
                "description": error.detail,
                "content": {
                    "application/json": {
                        "schema": {"properties": {"detail": {"const": error.detail}}},
                        "example": {"detail": error.detail},
                    }
                },
            }
        return result


class APIRouteExt(APIRoute):
    def dependency_responses(
        self,
        dependant: Dependant,
        dependencies_visited: set[Any],
        responses_seen: set[type[Responses]],
    ) -> Iterable[type[Responses]]:
        responses = getattr(dependant.call, "__responses__", None)
        if (
            isinstance(responses, type)
            and issubclass(responses, Responses)
            and responses not in responses_seen
        ):
            responses_seen.add(responses)
            yield responses

        for sub_dependant in dependant.dependencies:
            if sub_dependant.cache_key in dependencies_visited:
                continue
            dependencies_visited.add(dependant.cache_key)
            yield from self.dependency_responses(
                sub_dependant,
                dependencies_visited=dependencies_visited,
                responses_seen=responses_seen,
            )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.dependant.call is None:
            return

        responses_seen: set[type[Responses]] = getattr(
            self.dependant.call, "__responses_seen__", set()
        )
        for responses in self.dependency_responses(
            self.dependant,
            dependencies_visited=set(),
            responses_seen=responses_seen,
        ):
            self.responses.update(responses.responses(continue_from=self.responses))
        setattr(self.dependant.call, "__responses_seen__", responses_seen)  # noqa: B010


class APIRouterExt(APIRouter):
    # linter's bug: method is not useless, since default is overridden
    def __init__(  # noqa: WPS612
        self, *, route_class: type[APIRoute] = APIRouteExt, **kwargs: Any
    ) -> None:
        super().__init__(route_class=route_class, **kwargs)


P = ParamSpec("P")
R = TypeVar("R")


def with_responses(
    responses: type[Responses],
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def with_responses_inner(function: Callable[P, R]) -> Callable[P, R]:
        setattr(function, "__responses__", responses)  # noqa: B010
        return function

    return with_responses_inner


def with_responses_marker(responses: type[Responses]) -> Any:
    def noop() -> None:
        pass

    return Depends(with_responses(responses)(noop))
