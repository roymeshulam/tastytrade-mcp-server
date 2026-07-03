# Deployment

This server supports local `stdio` MCP and remote HTTP MCP.

Use `stdio` for local clients that launch the process for you, such as MCP
Inspector during local testing. Use `streamable-http` when running it as a
long-lived server process.

## Environment

Create `/opt/tastytrade-mcp-server/.env`:

```env
TASTYTRADE_ENV=production
REFRESH_TOKEN=your_refresh_token_here
CLIENT_SECRET=your_client_secret_here
ACCOUNT_NUMBER=your_account_number_here

MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=127.0.0.1:8000,localhost:8000
MCP_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

For direct LAN/VPN access, set `MCP_HOST=0.0.0.0` and include the real host
header clients will use in `MCP_ALLOWED_HOSTS`, such as
`mcp.example.com,10.0.0.12:8000`.

For a public client such as mobile ChatGPT, use a public HTTPS URL on a domain:

```text
https://mcp.example.com/mcp
```

Point the domain's DNS `A` record at the server IP, then run the MCP server on
localhost behind a reverse proxy that terminates TLS:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com,https://chatgpt.com,https://chat.openai.com
```

Avoid using a raw IP address for HTTPS. Free certificate authorities such as
Let's Encrypt generally issue certificates for DNS names, not bare IP addresses,
and mobile/public MCP clients are likely to reject self-signed certificates.

If you temporarily test over plain HTTP on a raw IP address, such as
`http://176.57.150.218:8080/mcp`, use:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=176.57.150.218:8080
MCP_ALLOWED_ORIGINS=http://176.57.150.218:8080,https://chatgpt.com,https://chat.openai.com
```

Do not expose this service directly to the public internet without an access
control layer. It can read brokerage account data. Prefer VPN/Tailscale,
Cloudflare Access, mTLS, or an HTTPS reverse proxy with authentication.

## Install

Example on Ubuntu:

```bash
sudo useradd --system --home /opt/tastytrade-mcp-server --shell /usr/sbin/nologin tastytrade-mcp
sudo mkdir -p /opt/tastytrade-mcp-server
sudo chown tastytrade-mcp:tastytrade-mcp /opt/tastytrade-mcp-server

cd /opt/tastytrade-mcp-server
git clone <your-repo-url> .
uv sync
```

Put `.env` in `/opt/tastytrade-mcp-server/.env` and restrict it:

```bash
sudo chown tastytrade-mcp:tastytrade-mcp /opt/tastytrade-mcp-server/.env
sudo chmod 600 /opt/tastytrade-mcp-server/.env
```

## systemd

Create `/etc/systemd/system/tastytrade-mcp.service`:

```ini
[Unit]
Description=tastytrade MCP Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tastytrade-mcp
Group=tastytrade-mcp
WorkingDirectory=/opt/tastytrade-mcp-server
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/uv run tastytrade-mcp-server
Restart=on-failure
RestartSec=5

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/tastytrade-mcp-server

[Install]
WantedBy=multi-user.target
```

Enable and inspect logs:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tastytrade-mcp
sudo systemctl status tastytrade-mcp
journalctl -u tastytrade-mcp -f
```

## Reverse Proxy

Run the MCP server on localhost and expose it through a reverse proxy that
handles TLS and authentication.

For Caddy, which can automatically issue and renew certificates:

```caddyfile
mcp.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

For nginx, the upstream is:

```nginx
location /mcp {
    proxy_pass http://127.0.0.1:8000/mcp;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

If your public hostname is `mcp.example.com`, include this in `.env`:

```env
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com
```
