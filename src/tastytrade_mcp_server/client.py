from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

import httpx

from .config import Settings


class TastytradeError(RuntimeError):
    """Raised when tastytrade returns an unsuccessful response."""


MARKET_DATA_PRODUCT_TYPES = {
    "equity",
    "equity-option",
    "future",
    "future-option",
    "cryptocurrency",
    "index",
}


class TastytradeClient:
    """Small async client for read-only tastytrade account endpoints."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        settings.validate_auth()
        self._settings = settings
        self._owned_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=httpx.Timeout(30.0),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "tastytrade-mcp-server/0.1.0",
            },
        )
        self._session_token = settings.session_token
        self._access_token: str | None = None

    async def __aenter__(self) -> "TastytradeClient":
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owned_client:
            await self._client.aclose()

    async def customer_accounts(self) -> dict[str, Any]:
        return await self._request("GET", "/customers/me/accounts")

    async def account_balance(self, account_number: str) -> dict[str, Any]:
        return await self._request("GET", f"/accounts/{account_number}/balances")

    async def account_positions(
        self,
        account_number: str,
        *,
        include_closed: bool = False,
        symbol: str | None = None,
        underlying_symbol: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "include-closed-positions": include_closed,
                "symbol": symbol,
                "underlying-symbol": underlying_symbol,
            }
        )
        return await self._request("GET", f"/accounts/{account_number}/positions", params=params)

    async def live_orders(self, account_number: str) -> dict[str, Any]:
        return await self._request("GET", f"/accounts/{account_number}/orders/live")

    async def search_orders(
        self,
        account_number: str,
        *,
        status: str | None = None,
        from_entered_time: str | None = None,
        to_entered_time: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "status": status,
                "from-entered-time": from_entered_time,
                "to-entered-time": to_entered_time,
                "underlying-symbol": symbol,
            }
        )
        return await self._request("GET", f"/accounts/{account_number}/orders", params=params)

    async def account_transactions(
        self,
        account_number: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        transaction_type: str | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none(
            {
                "start-date": start_date,
                "end-date": end_date,
                "type": transaction_type,
                "symbol": symbol,
            }
        )
        return await self._request("GET", f"/accounts/{account_number}/transactions", params=params)

    async def market_data_by_type(self, product_type: str, symbol: str) -> dict[str, Any]:
        product_type = product_type.strip().lower()
        if product_type not in MARKET_DATA_PRODUCT_TYPES:
            supported = ", ".join(sorted(MARKET_DATA_PRODUCT_TYPES))
            raise ValueError(f"product_type must be one of: {supported}.")

        formatted_symbol = format_market_data_symbol(product_type, symbol)
        return await self._request("GET", "/market-data/by-type", params={product_type: formatted_symbol})

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = await self._auth_headers()
        response = await self._client.request(method, path, params=params, json=json, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _error_detail(exc.response)
            raise TastytradeError(f"tastytrade API error {exc.response.status_code}: {detail}") from exc

        payload = response.json()
        if isinstance(payload, dict):
            return payload
        raise TastytradeError("tastytrade API returned a non-object JSON payload.")

    async def _auth_headers(self) -> dict[str, str]:
        if self._settings.refresh_token and self._settings.client_secret:
            if not self._access_token:
                await self._refresh_access_token()
            return {"Authorization": f"Bearer {self._access_token}"}

        if not self._session_token:
            await self._create_session()
        return {"Authorization": self._session_token or ""}

    async def _refresh_access_token(self) -> None:
        response = await self._client.post(
            "/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._settings.refresh_token,
                "client_secret": self._settings.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _error_detail(exc.response)
            raise TastytradeError(f"Unable to refresh tastytrade OAuth token: {detail}") from exc

        payload = response.json()
        token = _find_token(payload, "access_token", "access-token")
        if not token:
            raise TastytradeError("OAuth response did not include access_token.")
        self._access_token = token

    async def _create_session(self) -> None:
        response = await self._client.post(
            "/sessions",
            json={
                "login": self._settings.username,
                "password": self._settings.password,
                "remember-me": True,
            },
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _error_detail(exc.response)
            raise TastytradeError(f"Unable to create tastytrade session: {detail}") from exc

        payload = response.json()
        token = payload.get("data", {}).get("session-token") if isinstance(payload, dict) else None
        if not token:
            raise TastytradeError("Session response did not include data.session-token.")
        self._session_token = token


def _drop_none(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def format_market_data_symbol(product_type: str, symbol: str) -> str:
    value = symbol.strip()
    if not value:
        raise ValueError("symbol is required.")

    if product_type in {"equity", "equity-option", "future", "future-option", "cryptocurrency", "index"}:
        return value.upper()
    return value


def format_equity_option_symbol(
    root_symbol: str,
    expiration_date: str,
    option_type: str,
    strike_price: str | float | int | Decimal,
) -> str:
    root = root_symbol.strip().upper()
    if not root:
        raise ValueError("root_symbol is required.")
    if len(root) > 6:
        raise ValueError("root_symbol must be 6 characters or fewer for equity option symbology.")

    expiration = _format_option_expiration(expiration_date)
    call_put = _format_option_type(option_type)
    strike = _format_option_strike(strike_price)
    return f"{root:<6}{expiration}{call_put}{strike}"


def _format_option_expiration(expiration_date: str) -> str:
    value = expiration_date.strip()
    if len(value) == 6 and value.isdigit():
        return value

    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("expiration_date must be in YYYY-MM-DD or YYMMDD format.") from exc
    return parsed.strftime("%y%m%d")


def _format_option_type(option_type: str) -> str:
    value = option_type.strip().upper()
    if value in {"C", "CALL"}:
        return "C"
    if value in {"P", "PUT"}:
        return "P"
    raise ValueError("option_type must be call, put, C, or P.")


def _format_option_strike(strike_price: str | float | int | Decimal) -> str:
    try:
        strike = Decimal(str(strike_price)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("strike_price must be a numeric value.") from exc

    scaled = int(strike * 1000)
    if scaled < 0 or scaled > 99_999_999:
        raise ValueError("strike_price must fit the 8-digit equity option strike field.")
    return f"{scaled:08d}"


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text
    return str(payload)


def _find_token(payload: Any, *keys: str) -> str | None:
    if not isinstance(payload, dict):
        return None

    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    data = payload.get("data")
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value:
                return value

    return None
