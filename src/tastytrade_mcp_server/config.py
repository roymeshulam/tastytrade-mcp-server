from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SANDBOX_API_BASE_URL = "https://api.cert.tastytrade.com"
PRODUCTION_API_BASE_URL = "https://api.tastytrade.com"


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    api_base_url: str
    session_token: str | None = None
    refresh_token: str | None = None
    client_secret: str | None = None
    account_number: str | None = None
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        env_name = os.getenv("TASTYTRADE_ENV", "sandbox").strip().lower()
        default_base_url = (
            PRODUCTION_API_BASE_URL if env_name in {"prod", "production", "live"} else SANDBOX_API_BASE_URL
        )

        return cls(
            api_base_url=os.getenv("TASTYTRADE_API_BASE_URL", default_base_url).rstrip("/"),
            session_token=_empty_to_none(os.getenv("TASTYTRADE_SESSION_TOKEN")),
            refresh_token=_empty_to_none(os.getenv("REFRESH_TOKEN")),
            client_secret=_empty_to_none(os.getenv("CLIENT_SECRET")),
            account_number=_empty_to_none(os.getenv("ACCOUNT_NUMBER")),
            username=_empty_to_none(os.getenv("TASTYTRADE_USERNAME")),
            password=_empty_to_none(os.getenv("TASTYTRADE_PASSWORD")),
        )

    def validate_auth(self) -> None:
        if self.session_token:
            return
        if self.refresh_token and self.client_secret:
            return
        if self.username and self.password:
            return
        raise ValueError(
            "Set REFRESH_TOKEN and CLIENT_SECRET, TASTYTRADE_SESSION_TOKEN, "
            "or both TASTYTRADE_USERNAME and TASTYTRADE_PASSWORD."
        )

    def default_account_number(self) -> str:
        if not self.account_number:
            raise ValueError("Set ACCOUNT_NUMBER or pass account_number explicitly.")
        return self.account_number


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _load_dotenv() -> None:
    env_path = _find_dotenv()
    if env_path is None:
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = _parse_dotenv_value(value)


def _find_dotenv() -> Path | None:
    for directory in (Path.cwd(), *Path.cwd().parents):
        env_path = directory / ".env"
        if env_path.is_file():
            return env_path
    return None


def _parse_dotenv_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
