"""Lightweight type stubs for the minimal httpx shim used in tests."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping, Sequence

# These aliases mirror the names expected by Starlette's test client for type hints.
URLTypes = str
RequestContent = bytes | str | Iterable[bytes] | None
RequestFiles = MutableMapping[str, Any] | Sequence[tuple[str, Any]] | None
QueryParamTypes = Mapping[str, Any] | Sequence[tuple[str, Any]] | None
HeaderTypes = Mapping[str, str] | Sequence[tuple[str, str]] | None
CookieTypes = Mapping[str, str] | Sequence[tuple[str, str]] | None
TimeoutTypes = float | tuple[float, float, float, float] | None
AuthTypes = Any

__all__ = [
    "URLTypes",
    "RequestContent",
    "RequestFiles",
    "QueryParamTypes",
    "HeaderTypes",
    "CookieTypes",
    "TimeoutTypes",
    "AuthTypes",
]
