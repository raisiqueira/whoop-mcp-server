from __future__ import annotations

import secrets


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def main() -> None:
    key = generate_api_key()
    print("Generated WHOOP_MCP_API_KEY:")
    print(key)
    print()
    print("Add this to your .env file:")
    print(f"WHOOP_MCP_API_KEY={key}")
