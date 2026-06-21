from __future__ import annotations

import json
from pathlib import Path


_CONFIG_DIR = Path.home() / ".config" / "hearworm"
_CREDS_FILE = _CONFIG_DIR / "auth.json"


def login(country: str = "us") -> str:
    import audible

    auth = audible.Authenticator.from_login_external(locale=country)
    ab = auth.get_activation_bytes()

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _load()
    data["activation_bytes"] = ab
    data["country"] = country
    _CREDS_FILE.write_text(json.dumps(data, indent=2))

    return ab


def get_activation_bytes() -> str | None:
    data = _load()
    return data.get("activation_bytes")


def set_activation_bytes(ab: str) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _load()
    data["activation_bytes"] = ab
    _CREDS_FILE.write_text(json.dumps(data, indent=2))


def _load() -> dict:
    if _CREDS_FILE.exists():
        return json.loads(_CREDS_FILE.read_text())
    return {}
