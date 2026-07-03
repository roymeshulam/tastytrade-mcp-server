from __future__ import annotations

from pathlib import Path

import pytest

from tastytrade_mcp_server.config import PRODUCTION_API_BASE_URL, SANDBOX_API_BASE_URL, Settings


def test_settings_default_to_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TASTYTRADE_ENV", raising=False)
    monkeypatch.delenv("TASTYTRADE_API_BASE_URL", raising=False)
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.delenv("DEFAULT_ACCOUNT_NUMBER", raising=False)

    settings = Settings.from_env()

    assert settings.api_base_url == SANDBOX_API_BASE_URL


def test_settings_support_production_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TASTYTRADE_ENV", "prod")
    monkeypatch.delenv("TASTYTRADE_API_BASE_URL", raising=False)

    settings = Settings.from_env()

    assert settings.api_base_url == PRODUCTION_API_BASE_URL


def test_settings_require_auth_material() -> None:
    settings = Settings(api_base_url="https://example.test")

    with pytest.raises(ValueError):
        settings.validate_auth()


def test_settings_accept_refresh_token_and_client_secret() -> None:
    settings = Settings(
        api_base_url="https://example.test",
        refresh_token="refresh-token",
        client_secret="client-secret",
    )

    settings.validate_auth()


def test_default_account_number_requires_configuration() -> None:
    settings = Settings(api_base_url="https://example.test", session_token="session-token")

    with pytest.raises(ValueError):
        settings.default_account_number()


def test_default_account_number_uses_configured_account() -> None:
    settings = Settings(
        api_base_url="https://example.test",
        session_token="session-token",
        account_number="5WT00000",
    )

    assert settings.default_account_number() == "5WT00000"


def test_settings_load_dotenv_from_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TASTYTRADE_ENV", raising=False)
    monkeypatch.delenv("TASTYTRADE_API_BASE_URL", raising=False)
    monkeypatch.delenv("TASTYTRADE_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.delenv("DEFAULT_ACCOUNT_NUMBER", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "TASTYTRADE_ENV=production",
                'REFRESH_TOKEN="refresh-token-from-dotenv"',
                'CLIENT_SECRET="client-secret-from-dotenv"',
                "DEFAULT_ACCOUNT_NUMBER=5WT00000",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings.from_env()

    assert settings.api_base_url == PRODUCTION_API_BASE_URL
    assert settings.refresh_token == "refresh-token-from-dotenv"
    assert settings.client_secret == "client-secret-from-dotenv"
    assert settings.account_number == "5WT00000"


def test_environment_overrides_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REFRESH_TOKEN", "token-from-env")
    (tmp_path / ".env").write_text("REFRESH_TOKEN=token-from-dotenv", encoding="utf-8")

    settings = Settings.from_env()

    assert settings.refresh_token == "token-from-env"
