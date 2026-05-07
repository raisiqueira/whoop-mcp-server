# whoop-mcp

A local MCP server built with [FastMCP](https://gofastmcp.com/getting-started/welcome) for reading data from the [WHOOP API](https://developer.whoop.com/docs/introduction).

It exposes WHOOP profile, body measurements, recovery, cycle, sleep, workout, and overview tools so an MCP client such as ChatGPT can analyze your recent health data.

## What it includes

- OAuth helpers to generate the WHOOP authorization URL, exchange an authorization code, refresh tokens, and revoke access.
- A local `whoop-mcp-login` CLI that completes the WHOOP OAuth flow with a localhost callback.
- MCP tools for the main WHOOP v2 endpoints.
- A `get_health_overview` tool that aggregates recent data into a compact summary for follow-up analysis.

## WHOOP app setup

Create a WHOOP app in the Developer Dashboard and configure at least these values:

- Redirect URI: `http://127.0.0.1:8765/callback`
- Scopes: `offline read:profile read:body_measurement read:recovery read:cycles read:sleep read:workout`

WHOOP documents the OAuth authorization URL as `https://api.prod.whoop.com/oauth/oauth2/auth`, the token URL as `https://api.prod.whoop.com/oauth/oauth2/token`, and the v2 API base under `https://api.prod.whoop.com/developer/v2`.

## Local setup

```bash
uv sync
cp .env.example .env
```

Fill in `.env` with your WHOOP client credentials.

Or use `make`:

```bash
make sync
make env
```

## Authenticate once

Run the local login helper:

```bash
uv run whoop-mcp-login
```

Or:

```bash
make login
```

This starts a temporary localhost callback server, opens the WHOOP authorization page, and stores your token set in `.whoop-token.json`.

If you prefer to do the OAuth flow manually, you can also:

1. Run `uv run python -m whoop_mcp.server` or connect the MCP server in your client.
2. Call `build_whoop_authorization_url`.
3. Open the returned URL and approve access.
4. Exchange the returned `code` through `exchange_whoop_authorization_code`.

## Run the MCP server

For local stdio usage:

```bash
uv run whoop-mcp
```

Or:

```bash
make run
```

Or through the FastMCP CLI:

```bash
uv run fastmcp run src/whoop_mcp/server.py
```

FastMCP also supports HTTP transport:

```bash
uv run fastmcp run src/whoop_mcp/server.py --transport http --host 127.0.0.1 --port 8000
```

## Inspector

Using the MCP Inspector:

```bash
make inspect
```

Using the module entrypoint:

```bash
make inspect-module
```

Using FastMCP's built-in dev inspector:

```bash
make inspect-fastmcp
```

## Suggested MCP config

Example `mcp.json` entry:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/whoop-mcp",
        "whoop-mcp"
      ]
    }
  }
}
```

## Main tools

- `auth_status`
- `build_whoop_authorization_url`
- `exchange_whoop_authorization_code`
- `refresh_whoop_access_token`
- `revoke_whoop_access`
- `get_profile`
- `get_body_measurements`
- `get_cycles`
- `get_cycle`
- `get_recoveries`
- `get_recovery_for_cycle`
- `get_sleeps`
- `get_sleep`
- `get_sleep_for_cycle`
- `get_workouts`
- `get_workout`
- `get_health_overview`

## Development

Run tests:

```bash
uv run pytest
```

Lint:

```bash
uv run ruff check .
```

## Notes

- `get_health_overview` is intentionally compact. The idea is to give ChatGPT a strong starting point and then let it ask for more specific WHOOP records through the other tools.
- WHOOP access tokens are short-lived. The server refreshes them automatically when a refresh token is available.
- The login helper assumes a localhost redirect URI. If you use a non-local redirect URI, complete OAuth outside the helper and use the manual exchange tool instead.
