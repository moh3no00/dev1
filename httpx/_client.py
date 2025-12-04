"""Client defaults for the minimal httpx shim."""
from __future__ import annotations

class _UseClientDefault:
    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return "USE_CLIENT_DEFAULT"

USE_CLIENT_DEFAULT = _UseClientDefault()
