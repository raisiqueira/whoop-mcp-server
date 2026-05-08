from whoop_mcp.keys import generate_api_key


def test_generate_api_key_returns_non_empty_string() -> None:
    key = generate_api_key()

    assert isinstance(key, str)
    assert len(key) >= 32
