# Agent Notes: Deployment

This project exposes read-only tastytrade brokerage account data over MCP.
Treat remote deployment as sensitive infrastructure.

Preferred public endpoint shape:

```text
https://mcp.example.com/mcp
```

Recommended `.env` for a public HTTPS deployment behind a reverse proxy:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=mcp.example.com
MCP_ALLOWED_ORIGINS=https://mcp.example.com,https://chatgpt.com,https://chat.openai.com
```

Do not recommend naked public HTTP for real use. A raw IP endpoint like
`http://176.57.150.218:8080/mcp` is only suitable for temporary testing:

```env
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8080
MCP_STREAMABLE_HTTP_PATH=/mcp
MCP_ALLOWED_HOSTS=176.57.150.218:8080
MCP_ALLOWED_ORIGINS=http://176.57.150.218:8080,https://chatgpt.com,https://chat.openai.com
```

For ChatGPT mobile or other public clients, expect a trusted HTTPS URL. Use a
domain name and terminate TLS with Caddy, nginx, Cloudflare Tunnel/Access, or a
similar authenticated proxy. Avoid self-signed certificates and bare-IP HTTPS.
