from whoop_mcp.mcp_auth import append_www_authenticate_scope


def test_append_www_authenticate_scope_adds_scope_to_bearer_challenge() -> None:
    header = (
        'Bearer error="invalid_token", '
        'resource_metadata="https://whoop.example.com/.well-known/oauth-protected-resource/mcp"'
    )

    assert append_www_authenticate_scope(
        header,
        ("openid", "profile", "email", "offline_access"),
    ) == (
        'Bearer error="invalid_token", '
        'resource_metadata="https://whoop.example.com/.well-known/oauth-protected-resource/mcp", '
        'scope="openid profile email offline_access"'
    )


def test_append_www_authenticate_scope_keeps_existing_scope() -> None:
    header = 'Bearer error="invalid_token", scope="openid"'

    assert append_www_authenticate_scope(header, ("offline_access",)) == header
