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

Generate an HTTP bearer key:

```bash
make gen-key
```

Then set the generated value in `.env` as `WHOOP_MCP_API_KEY=...`.

By default, the example env uses:

```bash
WHOOP_MCP_AUTH_MODE=static_token
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

For local HTTP usage:

```bash
make run-http
```

Or through the FastMCP CLI:

```bash
uv run fastmcp run src/whoop_mcp/server.py
```

FastMCP also supports HTTP transport:

```bash
uv run fastmcp run src/whoop_mcp/server.py --transport http --host 127.0.0.1 --port 8000
```

The HTTP endpoint is exposed at `http://127.0.0.1:8000/mcp` by default.

## HTTP auth

This server supports three MCP auth modes:

- `none`
- `static_token`
- `oidc`

### Static bearer token

If `WHOOP_MCP_AUTH_MODE=static_token`, FastMCP protects the HTTP transport and clients must send:

```text
Authorization: Bearer <your-key>
```

Generate a key with:

```bash
make gen-key
```

This uses FastMCP's built-in static bearer-token verifier. It is appropriate for a private self-hosted setup behind your own tunnel, but it is still a shared secret, so rotate it if it leaks.

### OIDC with Authentik

If `WHOOP_MCP_AUTH_MODE=oidc`, FastMCP uses an OIDC proxy so ChatGPT, Claude, and other MCP clients can authenticate through Authentik.

Recommended env values:

```bash
WHOOP_MCP_AUTH_MODE=oidc
WHOOP_MCP_BASE_URL=https://whoop.<your-domain>.com
WHOOP_MCP_OIDC_CONFIG_URL=https://auth.example.com/application/o/whoop-mcp/.well-known/openid-configuration
WHOOP_MCP_OIDC_CLIENT_ID=your_authentik_client_id
WHOOP_MCP_OIDC_CLIENT_SECRET=your_authentik_client_secret
WHOOP_MCP_OIDC_SCOPES=openid profile email
WHOOP_MCP_OIDC_REDIRECT_PATH=/auth/callback
```

For Authentik, create an OAuth2/OpenID Provider and Application, then configure:

- OpenID Configuration URL: `https://auth.example.com/application/o/whoop-mcp/.well-known/openid-configuration`
- Redirect URI: `https://whoop.<your-domain>.com/auth/callback`
- Client type: confidential
- Scopes: at least `openid profile email`

The MCP endpoint stays:

```text
https://whoop.<your-domain>.com/mcp
```

The OAuth callback for the MCP server is:

```text
https://whoop.<your-domain>.com/auth/callback
```

FastMCP's OIDC proxy is the recommended path for ChatGPT and Claude, because both products support OAuth-based remote MCP connectors more cleanly than a shared bearer token.

## Docker

Build the image:

```bash
make docker-build
```

Run it over HTTP:

```bash
make docker-run-http
```

That container command:

- binds the server to `0.0.0.0:8000`
- exposes the MCP endpoint at `/mcp`
- mounts your local `.whoop-token.json` into `/data/whoop-token.json`
- stores FastMCP OAuth proxy state under `/data/fastmcp`
- reads WHOOP credentials from `.env`
- enforces the auth mode configured in `.env`

Equivalent raw Docker command:

```bash
docker build -t whoop-mcp .
docker run --rm -it \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/.whoop-token.json:/data/whoop-token.json" \
  whoop-mcp
```

## Docker Compose

For the Raspberry Pi workflow, use Compose:

```bash
make compose-up
```

Or directly:

```bash
docker compose up -d --build
```

Useful commands:

```bash
make compose-logs
make compose-down
```

The compose stack is defined in `docker-compose.yml` and:

- builds from the local `Dockerfile`
- binds the server only on `127.0.0.1:8000` for tunnel-friendly local exposure
- mounts `./.whoop-token.json` into `/data/whoop-token.json`
- persists FastMCP OAuth proxy state in the `fastmcp-oauth-data` volume
- reads WHOOP credentials, static token settings, and OIDC settings from `.env`
- restarts automatically with `unless-stopped`

For Authentik-backed OAuth via Compose, set these in `.env`:

```bash
WHOOP_MCP_AUTH_MODE=oidc
WHOOP_MCP_BASE_URL=https://whoop.<your-domain>.com
WHOOP_MCP_OIDC_CONFIG_URL=https://auth.example.com/application/o/whoop-mcp/.well-known/openid-configuration
WHOOP_MCP_OIDC_CLIENT_ID=your_authentik_client_id
WHOOP_MCP_OIDC_CLIENT_SECRET=your_authentik_client_secret
WHOOP_MCP_OIDC_SCOPES=openid profile email
WHOOP_MCP_OIDC_REDIRECT_PATH=/auth/callback
```

Then restart:

```bash
make compose-down
make compose-up
```

For Raspberry Pi 4, `python:3.12-slim` is multi-arch, so the same `Dockerfile` should build on ARM64. If your Pi OS is 32-bit, move it to a 64-bit image first. The modern Python base images and FastMCP dependencies are much less predictable on 32-bit ARM.

### Cloudflare Tunnel

Once the container is running on the Pi, expose `http://127.0.0.1:8000` with your Cloudflare Tunnel and point the public hostname to the MCP endpoint.

Example public URL:

```text
https://whoop-mcp.your-domain.com/mcp
```

Clients should use the public MCP URL plus your bearer key.

For FastMCP clients, the auth shape is:

```python
from fastmcp import Client

async with Client(
    "https://whoop-mcp.your-domain.com/mcp",
    auth="your-generated-bearer-key",
) as client:
    await client.ping()
```

For OAuth-enabled clients, use the standard FastMCP OAuth mode instead of a static bearer token:

```python
from fastmcp import Client

async with Client(
    "https://whoop-mcp.your-domain.com/mcp",
    auth="oauth",
) as client:
    await client.ping()
```

### Important security note

This server exposes your WHOOP health data to whoever can reach the MCP endpoint and use the tools. Do not publish it on the open internet without an access-control layer in front of it. A Cloudflare Tunnel alone is not enough if the hostname is public and unprotected.

## Inspector

Using the MCP Inspector:

```bash
make inspect
```

Using the MCP Inspector against a remote HTTP server:

```bash
make inspect-remote
```

With a custom URL:

```bash
make inspect-remote REMOTE_MCP_URL=http://pi01.local:8000/mcp
```

With bearer auth:

```bash
make inspect-remote \
  REMOTE_MCP_URL=http://pi01.local:8000/mcp \
  REMOTE_MCP_AUTH_HEADER="Authorization: Bearer your-key"
```

Using the module entrypoint:

```bash
make inspect-module
```

Using FastMCP's built-in dev inspector:

```bash
make inspect-fastmcp
```

## Connect from Codex

This repository includes a repo-local Codex plugin scaffold:

- `plugins/whoop-mcp/.codex-plugin/plugin.json`
- `plugins/whoop-mcp/.mcp.json`
- `.agents/plugins/marketplace.json`

The plugin points Codex at this hosted remote MCP endpoint:

```text
https://whoop.raisiqueira.io/mcp
```

To use it from Codex:

1. Open this repository in Codex.
2. Install the `WHOOP MCP` plugin from the local marketplace for this repo.
3. If the server is running with `WHOOP_MCP_AUTH_MODE=oidc`, complete the OAuth flow when Codex prompts for it.
4. Ask Codex to use the WHOOP MCP tools.

## Connect from ChatGPT

For ChatGPT, use the hosted remote MCP endpoint directly instead of the local Codex plugin.

1. In ChatGPT, enable Developer Mode in `Settings -> Connectors -> Advanced`.
2. Create an app for your remote MCP server.
3. Enter this server URL:

```text
https://whoop.raisiqueira.io/mcp
```

4. If the server uses OIDC, complete the OAuth flow.
5. Enable the imported tools in the app details page and use them from Developer Mode in chat.

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
- HTTP deployment is controlled through `WHOOP_MCP_TRANSPORT`, `WHOOP_MCP_HOST`, `WHOOP_MCP_PORT`, `WHOOP_MCP_PATH`, and `WHOOP_MCP_STATELESS_HTTP`.
- MCP auth is controlled through `WHOOP_MCP_AUTH_MODE`. Use `static_token` for private testing and `oidc` for ChatGPT/Claude-friendly OAuth.
