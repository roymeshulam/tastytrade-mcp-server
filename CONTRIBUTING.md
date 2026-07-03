# Contributing

Thanks for helping improve `tastytrade-mcp-server`. This project is a small,
read-only MCP server for tastytrade account data, so changes should be cautious,
well-tested, and respectful of user credentials.

## Development Setup

```bash
git clone https://github.com/roymeshulam/tastytrade-mcp-server.git
cd tastytrade-mcp-server
uv sync
cp .env.example .env
```

Use sandbox credentials or mocked HTTP clients for development whenever
possible. Do not commit `.env`, account numbers, tokens, secrets, or captured
brokerage responses that include private data.

## Workflow

1. Create a focused branch for your change.
1. Keep changes scoped to one behavior or documentation topic.
1. Add or update tests for code changes.
1. Run the checks before opening a pull request.

```bash
uv run pytest
uv run ruff check .
npx --yes markdownlint-cli2 "**/*.md"
```

If a tool is unavailable in your environment, mention that in the pull request.

## Code Guidelines

- Preserve the read-only default behavior.
- Prefer typed, explicit helpers over ad hoc parsing.
- Keep tastytrade API response fields intact unless a tool intentionally
  documents a normalized shape.
- Do not add trading, order placement, order replacement, or cancellation tools
  without a separate design discussion.
- Treat MCP client authentication and tastytrade authentication as separate
  concerns.

## Pull Requests

Include:

- What changed and why.
- How you tested it.
- Any deployment or configuration impact.
- Any security or privacy considerations.

Avoid broad refactors in feature PRs. Smaller patches are easier to review and
safer for a broker-facing integration.
