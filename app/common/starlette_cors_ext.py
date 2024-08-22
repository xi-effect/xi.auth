from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Message, Send


class CorrectCORSMiddleware(CORSMiddleware):
    async def send(
        self, message: Message, send: Send, request_headers: Headers
    ) -> None:
        if message["type"] != "http.response.start":
            await send(message)
            return

        message.setdefault("headers", [])
        headers = MutableHeaders(scope=message)
        headers.update(self.simple_headers)
        origin = request_headers["Origin"]

        if self.is_allowed_origin(origin=origin):
            self.allow_explicit_origin(headers, origin)

        await send(message)
