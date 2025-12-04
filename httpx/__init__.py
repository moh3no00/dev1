"""A minimal httpx-compatible shim for offline test environments.

This module implements just enough of the httpx API for Starlette's TestClient
usage in the unit tests. It is not a full HTTP client and should not be used
for production network calls.
"""
from __future__ import annotations

import io
import json
import urllib.parse
from typing import Any, Iterable, Mapping, Sequence

from . import _types
from ._client import USE_CLIENT_DEFAULT

__all__ = [
    "BaseTransport",
    "ByteStream",
    "Request",
    "Response",
    "Client",
    "Headers",
    "URL",
    "USE_CLIENT_DEFAULT",
]


class Headers:
    def __init__(self, data: Mapping[str, str] | Iterable[tuple[str, str]] | None = None):
        self._items: list[tuple[str, str]] = []
        if data:
            if isinstance(data, Mapping):
                self._items.extend(list(data.items()))
            else:
                self._items.extend(list(data))

    def multi_items(self) -> list[tuple[str, str]]:
        return list(self._items)

    def get(self, key: str, default: str | None = None) -> str | None:
        key_lower = key.lower()
        for header, value in self._items:
            if header.lower() == key_lower:
                return value
        return default

    def setdefault(self, key: str, value: str) -> None:
        if self.get(key) is None:
            self._items.append((key, value))

    def __iter__(self):  # pragma: no cover - convenience helper
        return iter(self._items)


class URL:
    def __init__(self, url: str):
        parsed = urllib.parse.urlparse(url)
        self.scheme = parsed.scheme or "http"
        self.host = parsed.hostname or ""
        port = parsed.port
        if port is None:
            default_ports = {"http": 80, "https": 443, "ws": 80, "wss": 443}
            port = default_ports.get(self.scheme, None)
        self.port = port
        netloc = parsed.netloc or parsed.hostname or ""
        if parsed.port and parsed.hostname:
            netloc = f"{parsed.hostname}:{parsed.port}"
        self.netloc = netloc.encode("ascii")
        path = parsed.path or "/"
        self.path = path
        self.raw_path = path.encode("ascii")
        self.query = (parsed.query or "").encode("ascii")

    def __str__(self) -> str:  # pragma: no cover - debug helper
        netloc = self.netloc.decode("ascii") if isinstance(self.netloc, (bytes, bytearray)) else str(self.netloc)
        query = f"?{self.query.decode('ascii')}" if self.query else ""
        return f"{self.scheme}://{netloc}{self.path}{query}"


class Request:
    def __init__(self, method: str, url: str, headers: Headers | None = None, content: Any = None):
        self.method = method.upper()
        self.url = URL(url)
        self.headers = headers or Headers()
        self._body = content or b""

    def read(self) -> bytes:
        if isinstance(self._body, bytes):
            return self._body
        if isinstance(self._body, str):
            return self._body.encode("utf-8")
        if isinstance(self._body, Iterable):  # pragma: no cover - not used in tests
            return b"".join(self._body)
        return b""


class ByteStream:
    def __init__(self, data: bytes):
        self._buffer = io.BytesIO(data)

    def read(self) -> bytes:
        return self._buffer.read()

    def __iter__(self):  # pragma: no cover - compatibility helper
        yield from self._buffer.getvalue()


class Response:
    def __init__(
        self,
        status_code: int,
        headers: list[tuple[str, str]] | None = None,
        stream: ByteStream | None = None,
        request: Request | None = None,
    ):
        self.status_code = status_code
        self.headers = headers or []
        self.request = request
        self._stream = stream or ByteStream(b"")
        self._content = self._stream.read()

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def text(self) -> str:
        return self._content.decode("utf-8")

    def json(self) -> Any:
        return json.loads(self.text or "null")


class BaseTransport:
    def handle_request(self, request: Request) -> Response:  # pragma: no cover - abstract
        raise NotImplementedError

    def __enter__(self):  # pragma: no cover - compatibility
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - compatibility
        return False


class Client:
    def __init__(
        self,
        base_url: str | None = None,
        headers: Mapping[str, str] | None = None,
        transport: BaseTransport | None = None,
        follow_redirects: bool | None = None,
        cookies: Mapping[str, str] | None = None,
    ) -> None:
        self.base_url = base_url or ""
        self.headers = Headers(headers)
        self.transport = transport
        self.follow_redirects = follow_redirects
        self.cookies = cookies or {}

    def _merge_url(self, url: str) -> str:
        if urllib.parse.urlparse(url).netloc:
            return url
        return urllib.parse.urljoin(self.base_url or "", url)

    def request(
        self,
        method: str,
        url: _types.URLTypes,
        *,
        content: _types.RequestContent | None = None,
        data: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
        files: _types.RequestFiles | None = None,
        json: Any = None,
        params: _types.QueryParamTypes | None = None,
        headers: _types.HeaderTypes | None = None,
        cookies: _types.CookieTypes | None = None,
        auth: _types.AuthTypes | USE_CLIENT_DEFAULT = USE_CLIENT_DEFAULT,
        follow_redirects: bool | USE_CLIENT_DEFAULT = USE_CLIENT_DEFAULT,
        timeout: _types.TimeoutTypes | USE_CLIENT_DEFAULT = USE_CLIENT_DEFAULT,
        extensions: dict[str, Any] | None = None,
    ) -> Response:
        merged_url = self._merge_url(url)
        combined_headers = Headers(self.headers.multi_items())
        if headers:
            combined_headers = Headers(list(combined_headers.multi_items()) + list(headers.items()))
        body: Any = content
        if json is not None:
            body = jsonlib.dumps(json)
            combined_headers.setdefault("content-type", "application/json")
        request = Request(method, merged_url, headers=combined_headers, content=body)
        if self.transport is None:
            raise RuntimeError("No transport provided for httpx shim")
        response = self.transport.handle_request(request)
        return response

    def get(self, url: _types.URLTypes, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: _types.URLTypes, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def __enter__(self) -> "Client":  # pragma: no cover - compatibility
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - compatibility
        return False


# Simple JSON helper to avoid shadowing stdlib json
jsonlib = json
