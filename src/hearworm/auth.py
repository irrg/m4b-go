from __future__ import annotations

from pathlib import Path


_CONFIG_DIR = Path.home() / ".config" / "hearworm"
_AUTH_FILE = _CONFIG_DIR / "auth.json"


def login(country: str = "us") -> str:
    import audible

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    auth = audible.Authenticator.from_login_external(locale=country)
    ab = auth.get_activation_bytes()
    auth.activation_bytes = ab
    auth.to_file(_AUTH_FILE, encryption=False)
    return ab


def load_auth() -> "audible.Authenticator":
    import audible

    if not _AUTH_FILE.exists():
        raise RuntimeError("Not logged in. Run 'hearworm auth login' first.")
    return audible.Authenticator.from_file(_AUTH_FILE, encryption=False)


def get_activation_bytes() -> str | None:
    if not _AUTH_FILE.exists():
        return None
    auth = load_auth()
    return auth.activation_bytes


def set_activation_bytes(ab: str) -> None:
    import audible

    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _AUTH_FILE.exists():
        auth = load_auth()
    else:
        raise RuntimeError("Not logged in. Run 'hearworm auth login' first.")
    auth.activation_bytes = ab
    auth.to_file(_AUTH_FILE, encryption=False)
