PYTHON ?= python3
UV ?= uv
INSPECTOR ?= npx -y @modelcontextprotocol/inspector

.PHONY: help sync sync-dev env login run run-module inspect inspect-module inspect-fastmcp test lint

help:
	@echo "Available targets:"
	@echo "  make sync            Install runtime dependencies"
	@echo "  make sync-dev        Install runtime and dev dependencies"
	@echo "  make env             Create .env from .env.example if missing"
	@echo "  make login           Run the WHOOP OAuth login helper"
	@echo "  make run             Run the WHOOP MCP server"
	@echo "  make run-module      Run the WHOOP MCP server via python -m"
	@echo "  make inspect         Open MCP Inspector against the installed script"
	@echo "  make inspect-module  Open MCP Inspector against python -m whoop_mcp.server"
	@echo "  make inspect-fastmcp Open FastMCP dev inspector"
	@echo "  make lint            Run Ruff"
	@echo "  make test            Run pytest"

sync:
	$(UV) sync

sync-dev:
	$(UV) sync --extra dev

env:
	@test -f .env || cp .env.example .env

login:
	$(UV) run whoop-mcp-login

run:
	$(UV) run whoop-mcp

run-module:
	$(UV) run $(PYTHON) -m whoop_mcp.server

inspect:
	$(INSPECTOR) $(UV) run whoop-mcp

inspect-module:
	$(INSPECTOR) $(UV) run $(PYTHON) -m whoop_mcp.server

inspect-fastmcp:
	$(UV) run fastmcp dev inspector src/whoop_mcp/server.py

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest
