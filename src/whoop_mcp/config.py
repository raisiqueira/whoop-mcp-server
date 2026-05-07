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


def load_environment() -> None:
    load_dotenv()


def _split_scopes(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_SCOPES
    scopes = tuple(part.strip() for part in raw_value.replace(",", " ").split() if part.strip())
    return scopes or DEFAULT_SCOPES


@dataclass(slots=True)
class Settings:
    client_id: str | None
    client_secret: str | None
    redirect_uri: str | None
    token_file: Path
    scopes: tuple[str, ...]
    api_base_url: str = "https://api.prod.whoop.com"

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
