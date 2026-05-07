from __future__ import annotations

import json
import secrets
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from whoop_mcp.config import Settings

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


@dataclass(slots=True)
class TokenSet:
    access_token: str
    token_type: str
    expires_at: float
    scope: str | None = None
    refresh_token: str | None = None

    @classmethod
    def from_token_response(
        cls,
        payload: dict[str, Any],
        previous: TokenSet | None = None,
    ) -> TokenSet:
        refresh_token = payload.get("refresh_token")
        if refresh_token is None and previous is not None:
            refresh_token = previous.refresh_token
        expires_in = int(payload["expires_in"])
        return cls(
            access_token=payload["access_token"],
            token_type=payload.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            scope=payload.get("scope"),
            refresh_token=refresh_token,
        )

    def is_expired(self, leeway_seconds: int = 60) -> bool:
        return time.time() >= self.expires_at - leeway_seconds

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "token_type": self.token_type,
            "expires_at": self.expires_at,
            "expires_in_seconds": max(0, int(self.expires_at - time.time())),
            "scope": self.scope,
            "has_refresh_token": self.refresh_token is not None,
        }


class TokenStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> TokenSet | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text())
        return TokenSet(**payload)

    def save(self, token_set: TokenSet) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(token_set), indent=2))

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


def build_authorization_url(
    settings: Settings,
    *,
    scopes: list[str] | tuple[str, ...] | None = None,
    state: str | None = None,
) -> dict[str, Any]:
    settings.require_oauth_client()
    resolved_state = state or secrets.token_urlsafe(16)
    resolved_scopes = tuple(scopes or settings.scopes)
    params = {
        "client_id": settings.client_id,
        "redirect_uri": settings.redirect_uri,
        "response_type": "code",
        "scope": " ".join(resolved_scopes),
        "state": resolved_state,
    }
    return {
        "authorization_url": f"{AUTH_URL}?{urlencode(params)}",
        "state": resolved_state,
        "scopes": list(resolved_scopes),
        "redirect_uri": settings.redirect_uri,
    }


def exchange_code(
    settings: Settings,
    token_store: TokenStore,
    *,
    code: str,
) -> dict[str, Any]:
    settings.require_oauth_client()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(TOKEN_URL, data=data)
        response.raise_for_status()
        payload = response.json()

    token_set = TokenSet.from_token_response(payload)
    token_store.save(token_set)
    return {
        "message": "WHOOP access token stored successfully.",
        "token_file": str(token_store.path),
        "token": token_set.to_public_dict(),
    }


def refresh_token(settings: Settings, token_store: TokenStore) -> dict[str, Any]:
    settings.require_oauth_client()
    existing = token_store.load()
    if existing is None or not existing.refresh_token:
        raise RuntimeError("No refresh token found. Run the WHOOP login flow again.")

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "scope": "offline",
        "refresh_token": existing.refresh_token,
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(TOKEN_URL, data=data)
        response.raise_for_status()
        payload = response.json()

    token_set = TokenSet.from_token_response(payload, previous=existing)
    token_store.save(token_set)
    return {
        "message": "WHOOP access token refreshed successfully.",
        "token_file": str(token_store.path),
        "token": token_set.to_public_dict(),
    }
