from __future__ import annotations

import os
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

from .client import TastytradeClient
from .config import Settings


McpTransport = Literal["stdio", "sse", "streamable-http"]
MarketDataProductType = Annotated[
    Literal["equity", "equity-option", "future", "future-option", "cryptocurrency", "index"],
    Field(
        description=(
            "tastytrade market data product type. This becomes the query key for "
            "/market-data/by-type, such as index=SPX or equity-option=<OCC symbol>."
        )
    ),
]
OptionalAccountNumber = Annotated[
    str | None,
    Field(description="Optional tastytrade account number. Uses DEFAULT_ACCOUNT_NUMBER when omitted."),
]
OptionalDate = Annotated[
    str | None,
    Field(description="Optional date filter in YYYY-MM-DD format."),
]
OptionalTransactionType = Annotated[
    str | None,
    Field(description="Optional tastytrade transaction type filter, such as Trade, Receive Deliver, Money Movement, or Fee."),
]
OptionalSymbol = Annotated[
    str | None,
    Field(description="Optional symbol filter, for example AAPL, SPY, or /ES."),
]
MarketDataSymbol = Annotated[
    str,
    Field(
        description=(
            "Market data symbol for the selected product type, for example SPX, AAPL, "
            "or SPXW  260727P07250000."
        )
    ),
]

Settings.from_env()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_list(name: str) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings | None:
    allowed_hosts = _env_list("MCP_ALLOWED_HOSTS")
    allowed_origins = _env_list("MCP_ALLOWED_ORIGINS")
    dns_protection = _env_bool("MCP_DNS_REBINDING_PROTECTION", True)

    if not allowed_hosts and not allowed_origins and dns_protection:
        return None

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=dns_protection,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def _mcp_transport() -> McpTransport:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        return "stdio"
    if transport == "sse":
        return "sse"
    if transport == "streamable-http":
        return "streamable-http"
    raise ValueError("MCP_TRANSPORT must be one of: stdio, sse, streamable-http.")


mcp = FastMCP(
    "tastytrade",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=_env_int("MCP_PORT", 8000),
    streamable_http_path=os.getenv("MCP_STREAMABLE_HTTP_PATH", "/mcp"),
    json_response=_env_bool("MCP_JSON_RESPONSE", False),
    stateless_http=_env_bool("MCP_STATELESS_HTTP", False),
    transport_security=_transport_security_settings(),
)


def _with_client() -> TastytradeClient:
    return TastytradeClient(Settings.from_env())


def _account_number(account_number: str | None) -> str:
    if account_number:
        return account_number
    return Settings.from_env().default_account_number()


@mcp.tool()
async def list_accounts() -> dict[str, Any]:
    """List tastytrade accounts visible to the authenticated customer."""
    async with _with_client() as client:
        return await client.customer_accounts()


@mcp.tool()
async def get_account_balance(account_number: str | None = None) -> dict[str, Any]:
    """Fetch current balance data for a tastytrade account."""
    async with _with_client() as client:
        return await client.account_balance(_account_number(account_number))


@mcp.tool()
async def get_account_positions(
    account_number: str | None = None,
    include_closed: bool = False,
    symbol: str | None = None,
    underlying_symbol: str | None = None,
) -> dict[str, Any]:
    """Fetch positions for a tastytrade account, optionally filtered by symbol."""
    async with _with_client() as client:
        return await client.account_positions(
            _account_number(account_number),
            include_closed=include_closed,
            symbol=symbol,
            underlying_symbol=underlying_symbol,
        )


@mcp.tool()
async def get_live_orders(account_number: str | None = None) -> dict[str, Any]:
    """Fetch currently live orders for a tastytrade account."""
    async with _with_client() as client:
        return await client.live_orders(_account_number(account_number))


@mcp.tool()
async def search_orders(
    account_number: str | None = None,
    status: str | None = None,
    from_entered_time: str | None = None,
    to_entered_time: str | None = None,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Search historical orders for a tastytrade account."""
    async with _with_client() as client:
        return await client.search_orders(
            _account_number(account_number),
            status=status,
            from_entered_time=from_entered_time,
            to_entered_time=to_entered_time,
            symbol=symbol,
        )


@mcp.tool()
async def get_account_transactions(
    account_number: OptionalAccountNumber = None,
    start_date: OptionalDate = None,
    end_date: OptionalDate = None,
    transaction_type: OptionalTransactionType = None,
    symbol: OptionalSymbol = None,
) -> dict[str, Any]:
    """Fetch tastytrade account transactions with optional account, date range, type, and symbol filters."""
    async with _with_client() as client:
        return await client.account_transactions(
            _account_number(account_number),
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            symbol=symbol,
        )


@mcp.tool()
async def get_market_data(
    product_type: MarketDataProductType,
    symbol: MarketDataSymbol,
) -> dict[str, Any]:
    """Fetch fresh tastytrade market data for one product using /market-data/by-type."""
    async with _with_client() as client:
        return await client.market_data_by_type(product_type, symbol)


def main() -> None:
    mcp.run(transport=_mcp_transport())


if __name__ == "__main__":
    main()
