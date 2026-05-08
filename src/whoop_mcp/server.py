from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from whoop_mcp.auth import TokenStore, build_authorization_url, exchange_code, refresh_token
from whoop_mcp.client import WhoopClient
from whoop_mcp.config import Settings
from whoop_mcp.insights import build_health_overview

settings = Settings.from_env()
token_store = TokenStore(settings.token_file)
client = WhoopClient(settings, token_store)


def build_auth_provider() -> StaticTokenVerifier | None:
    if not settings.mcp_api_key:
        return None
    return StaticTokenVerifier(
        tokens={
            settings.mcp_api_key: {
                "client_id": "whoop-mcp-client",
                "scopes": ["whoop:read"],
            }
        },
        required_scopes=["whoop:read"],
    )


auth_provider = build_auth_provider()

mcp = FastMCP(
    "WHOOP",
    instructions=(
        "Accesses WHOOP health data through the official WHOOP API. "
        "Use get_health_overview first for summaries, then drill into profile, recovery, sleep, "
        "cycle, and workout tools for detail."
    ),
    auth=auth_provider,
)
app = mcp.http_app(path=settings.path, stateless_http=settings.stateless_http)


def _days_ago_iso(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).replace(microsecond=0).isoformat()


def _collection(
    path: str,
    *,
    limit: int = 10,
    start: str | None = None,
    end: str | None = None,
    next_token: str | None = None,
) -> dict[str, Any]:
    return client.get_collection(path, limit=limit, start=start, end=end, next_token=next_token)


@mcp.tool
def auth_status() -> dict[str, Any]:
    """Show whether WHOOP credentials and user tokens are configured locally."""
    status = client.get_token_status()
    status["has_client_credentials"] = bool(settings.client_id and settings.client_secret)
    status["http_auth_enabled"] = auth_provider is not None
    status["redirect_uri"] = settings.redirect_uri
    status["default_scopes"] = list(settings.scopes)
    return status


@mcp.tool
def build_whoop_authorization_url(
    scopes: list[str] | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    """Build the WHOOP OAuth authorization URL for the configured app."""
    return build_authorization_url(settings, scopes=scopes, state=state)


@mcp.tool
def exchange_whoop_authorization_code(code: str) -> dict[str, Any]:
    """Exchange a WHOOP OAuth authorization code and store the resulting token set locally."""
    return exchange_code(settings, token_store, code=code)


@mcp.tool
def refresh_whoop_access_token() -> dict[str, Any]:
    """Refresh the stored WHOOP access token using the refresh token."""
    return refresh_token(settings, token_store)


@mcp.tool
def revoke_whoop_access() -> dict[str, Any]:
    """Revoke WHOOP access for the current user and remove the local token file."""
    client.delete("/developer/v2/user/access")
    token_store.clear()
    return {"message": "WHOOP access revoked and local token file removed."}


@mcp.tool
def get_profile() -> dict[str, Any]:
    """Fetch the authenticated WHOOP user's basic profile."""
    return client.get("/developer/v2/user/profile/basic")


@mcp.tool
def get_body_measurements() -> dict[str, Any]:
    """Fetch the authenticated WHOOP user's body measurements."""
    return client.get("/developer/v2/user/measurement/body")


@mcp.tool
def get_cycles(
    limit: int = 10,
    start: str | None = None,
    end: str | None = None,
    next_token: str | None = None,
) -> dict[str, Any]:
    """Fetch WHOOP cycles ordered by latest start time."""
    return _collection(
        "/developer/v2/cycle",
        limit=limit,
        start=start,
        end=end,
        next_token=next_token,
    )


@mcp.tool
def get_cycle(cycle_id: int) -> dict[str, Any]:
    """Fetch a WHOOP cycle by ID."""
    return client.get(f"/developer/v2/cycle/{cycle_id}")


@mcp.tool
def get_sleep_for_cycle(cycle_id: int) -> dict[str, Any]:
    """Fetch the WHOOP sleep associated with a cycle ID."""
    return client.get(f"/developer/v2/cycle/{cycle_id}/sleep")


@mcp.tool
def get_recoveries(
    limit: int = 10,
    start: str | None = None,
    end: str | None = None,
    next_token: str | None = None,
) -> dict[str, Any]:
    """Fetch WHOOP recoveries ordered by latest related sleep."""
    return _collection(
        "/developer/v2/recovery",
        limit=limit,
        start=start,
        end=end,
        next_token=next_token,
    )


@mcp.tool
def get_recovery_for_cycle(cycle_id: int) -> dict[str, Any]:
    """Fetch the WHOOP recovery associated with a cycle ID."""
    return client.get(f"/developer/v2/cycle/{cycle_id}/recovery")


@mcp.tool
def get_sleeps(
    limit: int = 10,
    start: str | None = None,
    end: str | None = None,
    next_token: str | None = None,
) -> dict[str, Any]:
    """Fetch WHOOP sleeps ordered by latest start time."""
    return _collection(
        "/developer/v2/activity/sleep",
        limit=limit,
        start=start,
        end=end,
        next_token=next_token,
    )


@mcp.tool
def get_sleep(sleep_id: str) -> dict[str, Any]:
    """Fetch a WHOOP sleep record by UUID."""
    return client.get(f"/developer/v2/activity/sleep/{sleep_id}")


@mcp.tool
def get_workouts(
    limit: int = 10,
    start: str | None = None,
    end: str | None = None,
    next_token: str | None = None,
) -> dict[str, Any]:
    """Fetch WHOOP workouts ordered by latest start time."""
    return _collection(
        "/developer/v2/activity/workout",
        limit=limit,
        start=start,
        end=end,
        next_token=next_token,
    )


@mcp.tool
def get_workout(workout_id: str) -> dict[str, Any]:
    """Fetch a WHOOP workout by UUID."""
    return client.get(f"/developer/v2/activity/workout/{workout_id}")


@mcp.tool
def get_health_overview(days: int = 7, workout_limit: int = 5) -> dict[str, Any]:
    """Fetch a compact WHOOP health overview suitable for follow-up analysis."""
    start = _days_ago_iso(days)

    profile = None
    body_measurement = None
    try:
        profile = get_profile()
    except httpx.HTTPStatusError:
        profile = None
    try:
        body_measurement = get_body_measurements()
    except httpx.HTTPStatusError:
        body_measurement = None

    cycles = get_cycles(limit=min(25, days), start=start).get("records", [])
    recoveries = get_recoveries(limit=min(25, days), start=start).get("records", [])
    sleeps = get_sleeps(limit=min(25, days), start=start).get("records", [])
    workouts = get_workouts(limit=min(25, max(workout_limit, days)), start=start).get("records", [])

    return build_health_overview(
        days=days,
        profile=profile,
        body_measurement=body_measurement,
        cycles=cycles,
        recoveries=recoveries,
        sleeps=sleeps,
        workouts=workouts[:workout_limit],
    )


def main() -> None:
    run_kwargs: dict[str, Any] = {}
    if settings.host:
        run_kwargs["host"] = settings.host
    if settings.port:
        run_kwargs["port"] = settings.port
    if settings.path:
        run_kwargs["path"] = settings.path
    if settings.stateless_http:
        run_kwargs["stateless_http"] = True
    mcp.run(transport=settings.transport, **run_kwargs)


if __name__ == "__main__":
    main()
