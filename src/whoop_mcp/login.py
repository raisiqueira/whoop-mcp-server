from __future__ import annotations

import argparse
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from whoop_mcp.auth import TokenStore, build_authorization_url, exchange_code
from whoop_mcp.config import Settings


class OAuthCallbackServer(HTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler: type[BaseHTTPRequestHandler],
    ) -> None:
        super().__init__(server_address, request_handler)
        self.event = threading.Event()
        self.result: dict[str, Any] = {}


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: OAuthCallbackServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        self.server.result = {
            "code": query.get("code", [None])[0],
            "state": query.get("state", [None])[0],
            "error": query.get("error", [None])[0],
        }
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>WHOOP authentication complete</h1>"
            b"<p>You can close this tab and return to the terminal.</p></body></html>"
        )
        self.server.event.set()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def _parse_local_redirect_uri(redirect_uri: str) -> tuple[str, int]:
    parsed = urlparse(redirect_uri)
    if parsed.scheme != "http":
        raise RuntimeError("WHOOP_REDIRECT_URI must use http:// for the local login helper.")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("WHOOP_REDIRECT_URI must point to localhost or 127.0.0.1.")
    if parsed.port is None:
        raise RuntimeError("WHOOP_REDIRECT_URI must include an explicit port.")
    return parsed.hostname, parsed.port


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WHOOP OAuth login flow locally.")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the URL instead of opening it.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.require_oauth_client()
    host, port = _parse_local_redirect_uri(settings.redirect_uri or "")

    token_store = TokenStore(settings.token_file)
    auth_payload = build_authorization_url(settings)
    expected_state = auth_payload["state"]

    callback_server = OAuthCallbackServer((host, port), OAuthCallbackHandler)
    thread = threading.Thread(target=callback_server.serve_forever, daemon=True)
    thread.start()

    print("Waiting for WHOOP OAuth callback on", settings.redirect_uri)
    print("Authorization URL:")
    print(auth_payload["authorization_url"])
    if not args.no_browser:
        webbrowser.open(auth_payload["authorization_url"])

    callback_server.event.wait(timeout=300)
    callback_server.shutdown()
    thread.join(timeout=5)

    if not callback_server.result:
        raise RuntimeError("Timed out waiting for the WHOOP OAuth callback.")
    if callback_server.result.get("error"):
        raise RuntimeError(f"WHOOP returned an OAuth error: {callback_server.result['error']}")
    if callback_server.result.get("state") != expected_state:
        raise RuntimeError("OAuth state mismatch. Aborting token exchange.")

    code = callback_server.result.get("code")
    if not code:
        raise RuntimeError("WHOOP did not return an authorization code.")

    result = exchange_code(settings, token_store, code=code)
    print(result["message"])
    print("Token file:", result["token_file"])
