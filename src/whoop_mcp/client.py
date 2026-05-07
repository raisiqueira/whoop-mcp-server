from __future__ import annotations

from typing import Any

import httpx

from whoop_mcp.auth import TokenSet, TokenStore, refresh_token
from whoop_mcp.config import Settings


class WhoopClient:
    def __init__(self, settings: Settings, token_store: TokenStore) -> None:
        self.settings = settings
        self.token_store = token_store

    def get_token_status(self) -> dict[str, Any]:
        token_set = self.token_store.load()
        if token_set is None:
            return {
                "authenticated": False,
                "token_file": str(self.token_store.path),
            }
        return {
            "authenticated": True,
            "token_file": str(self.token_store.path),
            "token": token_set.to_public_dict(),
        }

    def _load_valid_token(self) -> TokenSet:
        token_set = self.token_store.load()
        if token_set is None:
            raise RuntimeError(
                "No WHOOP token found. Run `whoop-mcp-login` or exchange an auth code first."
            )
        if token_set.is_expired():
            if not token_set.refresh_token:
                raise RuntimeError("WHOOP access token expired and no refresh token is available.")
            refresh_token(self.settings, self.token_store)
            token_set = self.token_store.load()
            if token_set is None:
                raise RuntimeError("WHOOP token refresh failed.")
        return token_set

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
        token_set = self._load_valid_token()
        url = f"{self.settings.api_base_url}{path}"
        headers = {"Authorization": f"Bearer {token_set.access_token}"}

        with httpx.Client(timeout=30) as client:
            response = client.request(method, url, params=params, headers=headers)
            if response.status_code == 401 and token_set.refresh_token:
                refresh_token(self.settings, self.token_store)
                refreshed = self._load_valid_token()
                headers["Authorization"] = f"Bearer {refreshed.access_token}"
                response = client.request(method, url, params=params, headers=headers)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def get_collection(
        self,
        path: str,
        *,
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        if next_token is not None:
            params["nextToken"] = next_token
        return self._request("GET", path, params=params)
