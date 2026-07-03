# Security Policy

This MCP server can expose brokerage account data. Treat deployment and logs as
sensitive, even though the current tool surface is read-only.

## Supported Versions

Security fixes target the latest `main` branch until formal releases are
introduced.

## Reporting a Vulnerability

Do not open a public issue with secrets, tokens, account numbers, private URLs,
or exploit details.

Report security concerns privately to the repository owner. Include:

- A short description of the issue.
- Steps to reproduce, using redacted values.
- Impact and affected configuration.
- Suggested fix, if known.

## Secret Handling

- Keep real credentials in `.env` or a secret manager.
- Never commit `.env`.
- Restrict `.env` permissions on Linux with `chmod 600 .env`.
- Rotate `REFRESH_TOKEN`, `CLIENT_SECRET`, and session tokens after accidental
  exposure.
- Avoid logging full API responses from live brokerage accounts.

## Deployment Guidance

Do not expose this server as naked public HTTP. Use a trusted HTTPS endpoint and
an access-control layer appropriate for your MCP client, such as:

- VPN or private network.
- Cloudflare Tunnel or Cloudflare Access.
- mTLS.
- Reverse proxy authentication.
- A future OAuth-compatible MCP client authentication flow.

For public clients such as mobile ChatGPT, prefer:

```text
https://mcp.example.com/mcp
```

Avoid self-signed certificates and bare-IP HTTPS for public clients.

## Scope

This project authenticates to tastytrade. It does not currently authenticate MCP
clients by itself. Any remote deployment must provide client access control
outside this process unless and until native MCP client authentication is added.
