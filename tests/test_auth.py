from pathlib import Path

from whoop_mcp.auth import build_authorization_url
from whoop_mcp.config import Settings


def test_build_authorization_url_uses_defaults() -> None:
    settings = Settings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://127.0.0.1:8765/callback",
        token_file=Path(".whoop-token.json"),
        scopes=("offline", "read:profile"),
    )

    payload = build_authorization_url(settings, state="fixed-state")

    assert payload["state"] == "fixed-state"
    assert payload["redirect_uri"] == "http://127.0.0.1:8765/callback"
    assert payload["scopes"] == ["offline", "read:profile"]
    assert "client_id=client-id" in payload["authorization_url"]
    assert "state=fixed-state" in payload["authorization_url"]
