from whoop_mcp.config import DEFAULT_MCP_OIDC_SCOPES


def test_default_mcp_oidc_scopes_request_refresh_token_scope() -> None:
    assert DEFAULT_MCP_OIDC_SCOPES == (
        "openid",
        "profile",
        "email",
        "offline_access",
    )
