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

Linux/macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/roymeshulam/tastytrade-mcp-server.git
cd tastytrade-mcp-server
uv sync
cp .env.example .env
chmod 600 .env
```

Windows PowerShell:

```powershell
uv venv
uv pip install -e ".[dev]"
cp .env.example .env
```

Set your `.env` values:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
DEFAULT_ACCOUNT_NUMBER=your_account_number_here
```

The account tools default to `DEFAULT_ACCOUNT_NUMBER`, but each
account-specific tool also accepts an explicit `account_number` argument.
`TASTYTRADE_SESSION_TOKEN` or `TASTYTRADE_USERNAME`/`TASTYTRADE_PASSWORD` can
still be used as fallback auth options for sandbox/dev workflows.

## Run Locally

For a local MCP client that launches the server over `stdio`:

```bash
uv run tastytrade-mcp-server
```

For a long-running local HTTP MCP server on port `8010`, set:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8010
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=127.0.0.1:8010,localhost:8010
MCP_ALLOWED_ORIGINS=http://127.0.0.1:8010,http://localhost:8010
```

Then run:

```bash
uv run tastytrade-mcp-server
```

The local endpoint is:

```text
http://127.0.0.1:8010/mcp
```

The root path `/` is not a web UI, so `404 Not Found` there is expected.

## Test With MCP Inspector

Run Inspector in a second terminal:

```bash
npx @modelcontextprotocol/inspector
```

Open the URL printed by Inspector and connect with:

```text
Transport: Streamable HTTP
URL: http://127.0.0.1:8010/mcp
```

If Inspector asks for proxy authentication, use the session token printed in
the Inspector terminal. Test `list_accounts` first, then account-specific tools.

## Public HTTPS Deployment

Remote clients such as mobile ChatGPT should use a public HTTPS URL, preferably
on a domain name:

```text
https://mcp.yourdomain.com/mcp
```

1. Point DNS at the server:

```text
Host: mcp
Type: A
Value: <server-public-ip>
```

1. Keep the MCP server bound to localhost in `.env`:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8010
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=mcp.yourdomain.com
MCP_ALLOWED_ORIGINS=https://mcp.yourdomain.com
```

Add `https://chatgpt.com` and `https://chat.openai.com` to
`MCP_ALLOWED_ORIGINS` if your MCP client sends those origins.

1. Install Caddy on Ubuntu from the official Caddy apt repository:

```bash
sudo apt install -y \
  debian-keyring \
  debian-archive-keyring \
  apt-transport-https \
  curl \
  gpg

curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
  | sudo gpg --dearmor \
  -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list

sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

1. Configure Caddy in `/etc/caddy/Caddyfile`:

```caddyfile
mcp.yourdomain.com {
    reverse_proxy 127.0.0.1:8010
}
```

Then reload Caddy:

```bash
caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

1. Run the MCP server persistently with systemd. Example for a checkout in
`/home/meshulro/Projects/tastytrade-mcp-server`:

```ini
[Unit]
Description=tastytrade MCP Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=meshulro
Group=meshulro
WorkingDirectory=/home/meshulro/Projects/tastytrade-mcp-server
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/meshulro/.local/bin/uv run tastytrade-mcp-server
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save that as `/etc/systemd/system/tastytrade-mcp.service`, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tastytrade-mcp
sudo systemctl status tastytrade-mcp
```

1. Verify:

```bash
dig mcp.yourdomain.com +short
systemctl is-active caddy
systemctl is-active tastytrade-mcp
curl -i -H 'Accept: text/event-stream' https://mcp.yourdomain.com/mcp
```

For a raw curl request, `400 Missing session ID` from the MCP server is a useful
sign that HTTPS and proxying work. A real MCP client will establish the session.

Plain HTTP on a raw IP address, such as `http://176.57.150.218:8080/mcp`, can be
useful for temporary testing but should not be used for brokerage account data.
Most public clients also expect trusted HTTPS certificates, which normally
requires a domain name rather than a bare IP address.

### Authentication Note

This server currently authenticates to tastytrade using credentials in `.env`,
but it does not authenticate MCP clients by itself. Caddy `basic_auth` can
protect browser or Inspector testing, but ChatGPT remote MCP setup expects an
OAuth-compatible flow, not Basic Auth. Do not leave a public brokerage-data MCP
endpoint exposed without an access-control layer suitable for your client.

For more deployment detail, see [docs/deployment.md](docs/deployment.md).

For MCP clients that launch this process over stdio, adapt
[docs/mcp-client-config.example.json](docs/mcp-client-config.example.json).

## Tools

- `list_accounts`
- `get_account_balance`
- `get_account_positions`
- `get_live_orders`
- `search_orders`
- `get_account_transactions`

## Development

```bash
uv run pytest
uv run ruff check .
```

## Notes

This server returns raw tastytrade API response objects so downstream clients can
preserve broker-specific fields. Keep credentials out of source control; `.env`
is ignored by git.
