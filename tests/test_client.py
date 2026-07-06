from __future__ import annotations

import httpx
import pytest

from tastytrade_mcp_server.client import TastytradeClient, format_equity_option_symbol
from tastytrade_mcp_server.config import Settings


@pytest.mark.asyncio
async def test_reuses_configured_session_token() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"items": []}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url="https://example.test")
    client = TastytradeClient(
        Settings(api_base_url="https://example.test", session_token="token-123"),
        http_client=http_client,
    )

    try:
        await client.customer_accounts()
    finally:
        await http_client.aclose()

    assert requests[0].headers["authorization"] == "token-123"
    assert requests[0].url.path == "/customers/me/accounts"


@pytest.mark.asyncio
async def test_creates_session_when_credentials_are_configured() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/sessions":
            return httpx.Response(201, json={"data": {"session-token": "new-token"}})
        return httpx.Response(200, json={"data": {"items": []}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url="https://example.test")
    client = TastytradeClient(
        Settings(
            api_base_url="https://example.test",
            username="some-user",
            password="some-password",
        ),
        http_client=http_client,
    )

    try:
        await client.account_balance("5WT00000")
    finally:
        await http_client.aclose()

    assert [request.url.path for request in requests] == ["/sessions", "/accounts/5WT00000/balances"]
    assert requests[1].headers["authorization"] == "new-token"


@pytest.mark.asyncio
async def test_refreshes_oauth_token_when_refresh_token_is_configured() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/oauth/token":
            return httpx.Response(200, json={"access_token": "access-token"})
        return httpx.Response(200, json={"data": {"account-number": "5WT00000"}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url="https://example.test")
    client = TastytradeClient(
        Settings(
            api_base_url="https://example.test",
            refresh_token="refresh-token",
            client_secret="client-secret",
        ),
        http_client=http_client,
    )

    try:
        await client.account_balance("5WT00000")
    finally:
        await http_client.aclose()

    assert [request.url.path for request in requests] == [
        "/oauth/token",
        "/accounts/5WT00000/balances",
    ]
    assert requests[0].content == (
        b"grant_type=refresh_token&refresh_token=refresh-token&client_secret=client-secret"
    )
    assert requests[1].headers["authorization"] == "Bearer access-token"


@pytest.mark.asyncio
async def test_fetches_market_data_by_type() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"items": [{"symbol": "SPX"}]}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url="https://example.test")
    client = TastytradeClient(
        Settings(api_base_url="https://example.test", session_token="token-123"),
        http_client=http_client,
    )

    try:
        await client.market_data_by_type("index", "spx")
    finally:
        await http_client.aclose()

    assert requests[0].url.path == "/market-data/by-type"
    assert requests[0].url.params["index"] == "SPX"


@pytest.mark.asyncio
async def test_fetches_market_data_for_equity_option_symbol() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"items": [{"symbol": "SPXW  260727P07250000"}]}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport, base_url="https://example.test")
    client = TastytradeClient(
        Settings(api_base_url="https://example.test", session_token="token-123"),
        http_client=http_client,
    )
    symbol = format_equity_option_symbol("SPXW", "2026-07-27", "put", "7250")

    try:
        await client.market_data_by_type("equity-option", symbol)
    finally:
        await http_client.aclose()

    assert symbol == "SPXW  260727P07250000"
    assert requests[0].url.path == "/market-data/by-type"
    assert requests[0].url.params["equity-option"] == "SPXW  260727P07250000"
