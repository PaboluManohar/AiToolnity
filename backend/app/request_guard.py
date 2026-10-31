import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque

from starlette.responses import JSONResponse


class RequestGuard:
    def __init__(
        self,
        app,
        *,
        allowed_origins: list[str],
        max_body_bytes: int = 512 * 1024,
    ):
        self.app = app
        self.allowed_origins = set(allowed_origins)
        self.max_body_bytes = max_body_bytes
        self._requests: dict[tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _limit(self, path: str, method: str) -> tuple[int, int] | None:
        if path == "/api/auth/google/start":
            return (10, 60)
        if path == "/api/auth/google/callback":
            return (20, 60)
        if path == "/api/settings/test" and method == "POST":
            return (3, 60)
        if path.startswith("/api/executions") and method == "POST":
            return (5, 60)
        if path.startswith("/api/settings") and method in {"POST", "PUT", "DELETE"}:
            return (10, 60)
        return None

    def _is_rate_limited(self, client: str, path: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        key = (client, path)
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= now - window:
                requests.popleft()
            if len(requests) >= limit:
                return True
            requests.append(now)
            if len(self._requests) > 10_000:
                cutoff = now - window
                self._requests = defaultdict(
                    deque,
                    {
                        item_key: events
                        for item_key, events in self._requests.items()
                        if events and events[-1] > cutoff
                    },
                )
        return False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.lower(): value for key, value in scope.get("headers", [])
        }
        origin = headers.get(b"origin")
        if origin is not None and origin.decode("latin-1") not in self.allowed_origins:
            response = JSONResponse(
                {"detail": "This request origin is not allowed."}, status_code=403
            )
            await response(scope, receive, send)
            return

        content_length = headers.get(b"content-length")
        if content_length:
            try:
                body_size = int(content_length)
            except ValueError:
                response = JSONResponse(
                    {"detail": "Invalid Content-Length header."}, status_code=400
                )
                await response(scope, receive, send)
                return
            if body_size < 0 or body_size > self.max_body_bytes:
                response = JSONResponse(
                    {"detail": "Request body exceeds the allowed size."},
                    status_code=413,
                )
                await response(scope, receive, send)
                return

        path = scope.get("path", "")
        method = scope.get("method", "GET")
        rate = self._limit(path, method)
        if rate:
            peer = scope.get("client")
            client = peer[0] if peer else "unknown"
            if self._is_rate_limited(client, path, *rate):
                response = JSONResponse(
                    {"detail": "Too many requests. Wait before trying again."},
                    status_code=429,
                    headers={"Retry-After": str(rate[1])},
                )
                await response(scope, receive, send)
                return

        messages = []
        total_size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                messages.append(message)
                continue
            total_size += len(message.get("body", b""))
            if total_size > self.max_body_bytes:
                response = JSONResponse(
                    {"detail": "Request body exceeds the allowed size."},
                    status_code=413,
                )
                await response(scope, receive, send)
                return
            messages.append(message)
            if not message.get("more_body", False):
                break

        message_index = 0

        async def replay_body():
            nonlocal message_index
            if message_index < len(messages):
                message = messages[message_index]
                message_index += 1
                return message
            return await receive()

        await self.app(scope, replay_body, send)
