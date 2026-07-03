# Deployment

This server supports local `stdio` MCP and remote HTTP MCP.

Use `stdio` for local clients that launch the process for you, such as MCP
Inspector during local testing. Use `streamable-http` when running it as a
long-lived server process.

## Environment

For the public HTTPS setup used by this project, the MCP process stays on
localhost port `8010` and Caddy exposes `https://mcp.example.com/mcp`.

Create `.env` in the project checkout:

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
MCP_ALLOWED_ORIGINS=https://mcp.example.com,https://chatgpt.com,https://chat.openai.com
```

For direct LAN/VPN access, set `MCP_HOST=0.0.0.0` and include the real host
header clients will use in `MCP_ALLOWED_HOSTS`, such as
`mcp.example.com,10.0.0.12:8000`.

For a public client such as mobile ChatGPT, use a public HTTPS URL on a domain:

```text
https://mcp.example.com/mcp
```

Point the domain's DNS `A` record at the server IP:

```text
Host: mcp
Type: A
Value: <server-public-ip>
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
mkdir -p ~/Projects
cd ~/Projects
git clone <your-repo-url> tastytrade-mcp-server
cd tastytrade-mcp-server
uv sync
```

Put `.env` in the project root and restrict it:

```bash
chmod 600 .env
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

Enable and inspect logs:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tastytrade-mcp
sudo systemctl status tastytrade-mcp
journalctl -u tastytrade-mcp -f
```

## Reverse Proxy

Run the MCP server on localhost and expose it through a reverse proxy that
handles TLS.

Install Caddy from the official repository:

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

Configure `/etc/caddy/Caddyfile`:

```caddyfile
mcp.example.com {
	reverse_proxy 127.0.0.1:8010
}
```

Validate and reload:

```bash
caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

For nginx, the upstream is:

```nginx
location /mcp {
    proxy_pass http://127.0.0.1:8010/mcp;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

If your public hostname is `mcp.example.com`, include this in `.env`:

```env
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com,https://chatgpt.com,https://chat.openai.com
```

## Verify

```bash
dig mcp.example.com +short
systemctl is-active caddy
systemctl is-active tastytrade-mcp
ss -ltnp
curl -i -H 'Accept: text/event-stream' https://mcp.example.com/mcp
```

Expected listeners include Caddy on `:80` and `:443`, plus the MCP server on
`127.0.0.1:8010`. A raw curl request can return `400 Missing session ID`; that
still confirms that Caddy is reaching the MCP app.

## Authentication

This deployment terminates HTTPS but does not authenticate MCP clients. Caddy
`basic_auth` can be added for MCP Inspector testing, but ChatGPT remote MCP
connectors expect OAuth, not Basic Auth. For production brokerage data, add an
OAuth-compatible layer or restrict access with VPN/Tailscale/Cloudflare Access
before relying on this endpoint publicly.
