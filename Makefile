PYTHON ?= python3
UV ?= uv
INSPECTOR ?= npx -y @modelcontextprotocol/inspector
DOCKER_IMAGE ?= whoop-mcp

.PHONY: help sync sync-dev env gen-key login run run-http run-module inspect inspect-module inspect-fastmcp docker-build docker-run docker-run-http compose-up compose-down compose-logs test lint

help:
	@echo "Available targets:"
	@echo "  make sync            Install runtime dependencies"
	@echo "  make sync-dev        Install runtime and dev dependencies"
	@echo "  make env             Create .env from .env.example if missing"
	@echo "  make gen-key         Generate a bearer API key for HTTP auth"
	@echo "  make login           Run the WHOOP OAuth login helper"
	@echo "  make run             Run the WHOOP MCP server"
	@echo "  make run-http        Run the WHOOP MCP server over HTTP on :8000"
	@echo "  make run-module      Run the WHOOP MCP server via python -m"
	@echo "  make inspect         Open MCP Inspector against the installed script"
	@echo "  make inspect-module  Open MCP Inspector against python -m whoop_mcp.server"
	@echo "  make inspect-fastmcp Open FastMCP dev inspector"
	@echo "  make docker-build    Build the Docker image"
	@echo "  make docker-run-http Run the Docker image on :8000"
	@echo "  make compose-up      Start the Docker Compose stack"
	@echo "  make compose-down    Stop the Docker Compose stack"
	@echo "  make compose-logs    Tail Docker Compose logs"
	@echo "  make lint            Run Ruff"
	@echo "  make test            Run pytest"

sync:
	$(UV) sync

sync-dev:
	$(UV) sync --extra dev

env:
	@test -f .env || cp .env.example .env

gen-key:
	$(UV) run whoop-mcp-generate-key

login:
	$(UV) run whoop-mcp-login

run:
	$(UV) run whoop-mcp

run-http:
	WHOOP_MCP_TRANSPORT=http WHOOP_MCP_HOST=127.0.0.1 WHOOP_MCP_PORT=8000 $(UV) run whoop-mcp

run-module:
	$(UV) run $(PYTHON) -m whoop_mcp.server

inspect:
	$(INSPECTOR) $(UV) run whoop-mcp

inspect-module:
	$(INSPECTOR) $(UV) run $(PYTHON) -m whoop_mcp.server

inspect-fastmcp:
	$(UV) run fastmcp dev inspector src/whoop_mcp/server.py

docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run-http:
	docker run --rm -it \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD)/.whoop-token.json:/data/whoop-token.json \
		$(DOCKER_IMAGE)

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f whoop-mcp

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest
