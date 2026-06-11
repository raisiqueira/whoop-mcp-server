from __future__ import annotations

from collections.abc import Iterable

from starlette.types import ASGIApp, Message, Receive, Scope, Send


def append_www_authenticate_scope(header_value: str, scopes: Iterable[str]) -> str:
    scope_value = " ".join(scope for scope in scopes if scope)
    if not scope_value or 'scope="' in header_value:
        return header_value
    if not header_value.lower().startswith("bearer"):
        return header_value
    return f'{header_value}, scope="{scope_value}"'


class WWWAuthenticateScopeMiddleware:
    def __init__(self, app: ASGIApp, scopes: Iterable[str]) -> None:
        self.app = app
        self.scopes = tuple(scopes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_scope(message: Message) -> None:
            if message["type"] == "http.response.start" and message.get("status") == 401:
                headers = list(message.get("headers", []))
                for index, (name, value) in enumerate(headers):
                    if name.lower() == b"www-authenticate":
                        updated = append_www_authenticate_scope(
                            value.decode("latin-1"), self.scopes
                        )
                        headers[index] = (name, updated.encode("latin-1"))
                        message["headers"] = headers
                        break
            await send(message)

        await self.app(scope, receive, send_with_scope)
