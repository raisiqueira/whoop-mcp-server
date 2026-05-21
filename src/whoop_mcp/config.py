from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_SCOPES = (
    "offline",
    "read:profile",
    "read:body_measurement",
    "read:recovery",
    "read:cycles",
    "read:sleep",
    "read:workout",
)

DEFAULT_MCP_OIDC_SCOPES = (
    "openid",
    "profile",
    "email",
)


def load_environment() -> None:
    load_dotenv()


def _split_scopes(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_SCOPES
    scopes = tuple(part.strip() for part in raw_value.replace(",", " ").split() if part.strip())
    return scopes or DEFAULT_SCOPES


def _split_values(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return ()
    return tuple(part.strip() for part in raw_value.replace(",", " ").split() if part.strip())


def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    client_id: str | None
    client_secret: str | None
    redirect_uri: str | None
    token_file: Path
    scopes: tuple[str, ...]
    api_base_url: str = "https://api.prod.whoop.com"
    auth_mode: str = "static_token"
    mcp_api_key: str | None = None
    public_base_url: str | None = None
    oidc_config_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_scopes: tuple[str, ...] = DEFAULT_MCP_OIDC_SCOPES
    oidc_redirect_path: str = "/auth/callback"
    oidc_allowed_client_redirect_uris: tuple[str, ...] = ()
    oidc_verify_id_token: bool = False
    oidc_trust_upstream_token: bool = False
    transport: str | None = None
    host: str | None = None
    port: int | None = None
    path: str | None = None
    stateless_http: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        load_environment()
        return cls(
            client_id=os.getenv("WHOOP_CLIENT_ID"),
            client_secret=os.getenv("WHOOP_CLIENT_SECRET"),
            redirect_uri=os.getenv("WHOOP_REDIRECT_URI"),
            token_file=Path(os.getenv("WHOOP_TOKEN_FILE", ".whoop-token.json")).expanduser(),
            scopes=_split_scopes(os.getenv("WHOOP_SCOPES")),
            api_base_url=os.getenv("WHOOP_API_BASE_URL", "https://api.prod.whoop.com").rstrip("/"),
            auth_mode=os.getenv("WHOOP_MCP_AUTH_MODE", "static_token").strip().lower(),
            mcp_api_key=os.getenv("WHOOP_MCP_API_KEY"),
            public_base_url=os.getenv("WHOOP_MCP_BASE_URL"),
            oidc_config_url=os.getenv("WHOOP_MCP_OIDC_CONFIG_URL"),
            oidc_client_id=os.getenv("WHOOP_MCP_OIDC_CLIENT_ID"),
            oidc_client_secret=os.getenv("WHOOP_MCP_OIDC_CLIENT_SECRET"),
            oidc_scopes=_split_scopes(os.getenv("WHOOP_MCP_OIDC_SCOPES"))
            if os.getenv("WHOOP_MCP_OIDC_SCOPES")
            else DEFAULT_MCP_OIDC_SCOPES,
            oidc_redirect_path=os.getenv("WHOOP_MCP_OIDC_REDIRECT_PATH", "/auth/callback"),
            oidc_allowed_client_redirect_uris=_split_values(
                os.getenv("WHOOP_MCP_OIDC_ALLOWED_CLIENT_REDIRECT_URIS")
            ),
            oidc_verify_id_token=_env_bool("WHOOP_MCP_OIDC_VERIFY_ID_TOKEN"),
            oidc_trust_upstream_token=_env_bool("WHOOP_MCP_OIDC_TRUST_UPSTREAM_TOKEN"),
            transport=os.getenv("WHOOP_MCP_TRANSPORT"),
            host=os.getenv("WHOOP_MCP_HOST"),
            port=int(os.getenv("WHOOP_MCP_PORT", "8000")),
            path=os.getenv("WHOOP_MCP_PATH"),
            stateless_http=_env_bool("WHOOP_MCP_STATELESS_HTTP"),
        )

    def require_oauth_client(self) -> None:
        missing = []
        if not self.client_id:
            missing.append("WHOOP_CLIENT_ID")
        if not self.client_secret:
            missing.append("WHOOP_CLIENT_SECRET")
        if not self.redirect_uri:
            missing.append("WHOOP_REDIRECT_URI")
        if missing:
            missing_list = ", ".join(missing)
            raise RuntimeError(f"Missing WHOOP configuration: {missing_list}")

    def require_mcp_oidc(self) -> None:
        missing = []
        if not self.public_base_url:
            missing.append("WHOOP_MCP_BASE_URL")
        if not self.oidc_config_url:
            missing.append("WHOOP_MCP_OIDC_CONFIG_URL")
        if not self.oidc_client_id:
            missing.append("WHOOP_MCP_OIDC_CLIENT_ID")
        if not self.oidc_client_secret:
            missing.append("WHOOP_MCP_OIDC_CLIENT_SECRET")
        if missing:
            missing_list = ", ".join(missing)
            raise RuntimeError(f"Missing MCP OIDC configuration: {missing_list}")
