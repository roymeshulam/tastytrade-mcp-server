# tastytrade-mcp-server

A lightweight, read-only Model Context Protocol (MCP) server for tastytrade
brokerage account data.

The first version exposes account discovery, balances, positions, live orders,
order search, and transactions. It intentionally does not submit, replace, or
cancel orders.

## Requirements

- Python 3.10+
- `uv` or another Python package manager
- tastytrade sandbox or production API credentials

## Setup

```powershell
uv venv
uv pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set your `.env` values:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
ACCOUNT_NUMBER=your_account_number_here
```

The account tools default to `ACCOUNT_NUMBER`, but each account-specific tool
also accepts an explicit `account_number` argument. `TASTYTRADE_SESSION_TOKEN`
or `TASTYTRADE_USERNAME`/`TASTYTRADE_PASSWORD` can still be used as fallback
auth options for sandbox/dev workflows.

## Run

```powershell
uv run tastytrade-mcp-server
```

For MCP clients, adapt [docs/mcp-client-config.example.json](docs/mcp-client-config.example.json).

For remote/server deployment, use `MCP_TRANSPORT=streamable-http` and see
[docs/deployment.md](docs/deployment.md).

Remote clients such as mobile ChatGPT should use a public HTTPS URL, preferably
on a domain name:

```text
https://mcp.yourdomain.com/mcp
```

Plain HTTP on a raw IP address, such as `http://176.57.150.218:8080/mcp`, can be
useful for temporary testing but should not be used for brokerage account data.
Most public clients also expect trusted HTTPS certificates, which normally
requires a domain name rather than a bare IP address.

## Tools

- `list_accounts`
- `get_account_balance`
- `get_account_positions`
- `get_live_orders`
- `search_orders`
- `get_account_transactions`

## Development

```powershell
uv run pytest
uv run ruff check .
```

## Notes

This server returns raw tastytrade API response objects so downstream clients can
preserve broker-specific fields. Keep credentials out of source control; `.env`
is ignored by git.
