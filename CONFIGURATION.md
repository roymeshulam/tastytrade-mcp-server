# Configuration

This project reads configuration from environment variables. It also loads a
local `.env` file by walking upward from the current working directory.

Copy the example file before running locally:

```bash
cp .env.example .env
chmod 600 .env
```

## Required tastytrade Settings

Preferred production authentication:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
DEFAULT_ACCOUNT_NUMBER=your_account_number_here
```

`DEFAULT_ACCOUNT_NUMBER` is used by account-specific tools when the
`account_number` argument is omitted.

## Authentication Variables

| Variable | Required | Description |
| --- | --- | --- |
| `REFRESH_TOKEN` | Preferred | OAuth refresh token for tastytrade. |
| `CLIENT_SECRET` | Preferred | OAuth client secret for tastytrade. |
| `DEFAULT_ACCOUNT_NUMBER` | Recommended | Default account for account tools. |
| `TASTYTRADE_SESSION_TOKEN` | Fallback | Existing tastytrade session token. |
| `TASTYTRADE_USERNAME` | Fallback | tastytrade username for session login. |
| `TASTYTRADE_PASSWORD` | Fallback | tastytrade password for session login. |

Authentication precedence:

1. `REFRESH_TOKEN` plus `CLIENT_SECRET`.
1. `TASTYTRADE_SESSION_TOKEN`.
1. `TASTYTRADE_USERNAME` plus `TASTYTRADE_PASSWORD`.

Production username/password login may require a device challenge. The OAuth
refresh-token flow is preferred for remote deployments.

## API Environment

| Variable | Default | Description |
| --- | --- | --- |
| `TASTYTRADE_ENV` | `sandbox` | Use `production`, `prod`, or `live` for live. |
| `TASTYTRADE_API_BASE_URL` | derived | Override the tastytrade API URL. |

Default URLs:

- Sandbox: `https://api.cert.tastytrade.com`
- Production: `https://api.tastytrade.com`

## MCP Transport

Local client-launched mode:

```env
MCP_TRANSPORT=stdio
```

Remote HTTP mode:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8010
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com
```

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_TRANSPORT` | `stdio` | `stdio`, `sse`, or `streamable-http`. |
| `MCP_HOST` | `127.0.0.1` | Interface to bind for HTTP transports. |
| `MCP_PORT` | `8000` | Port to bind for HTTP transports. |
| `MCP_STREAMABLE_HTTP_PATH` | `/mcp` | HTTP endpoint path. |
| `MCP_ALLOWED_HOSTS` | SDK default | Comma-separated allowed host headers. |
| `MCP_ALLOWED_ORIGINS` | SDK default | Comma-separated allowed origins. |
| `MCP_JSON_RESPONSE` | `false` | Return JSON responses for HTTP transport. |
| `MCP_STATELESS_HTTP` | `false` | Enable stateless HTTP mode. |
| `MCP_DNS_REBINDING_PROTECTION` | `true` | Enable SDK host checks. |

For a public deployment, keep `MCP_HOST=127.0.0.1` and expose the server through
an HTTPS reverse proxy.

## Example Configurations

Local stdio:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
DEFAULT_ACCOUNT_NUMBER=your_account_number_here
MCP_TRANSPORT=stdio
```

Local HTTP testing:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
DEFAULT_ACCOUNT_NUMBER=your_account_number_here
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8010
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=127.0.0.1:8010,localhost:8010
MCP_ALLOWED_ORIGINS=http://127.0.0.1:8010,http://localhost:8010
```

Public HTTPS behind a reverse proxy:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
DEFAULT_ACCOUNT_NUMBER=your_account_number_here
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8010
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com
```
