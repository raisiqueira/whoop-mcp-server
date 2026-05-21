FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md uv.lock ./
COPY src ./src

RUN python -m pip install --upgrade pip && \
    python -m pip install .

RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
    mkdir -p /data/fastmcp && \
    chown -R appuser:appuser /data
USER appuser

ENV WHOOP_MCP_TRANSPORT=http \
    WHOOP_MCP_HOST=0.0.0.0 \
    WHOOP_MCP_PORT=8000 \
    WHOOP_MCP_PATH=/mcp \
    WHOOP_MCP_STATELESS_HTTP=true \
    FASTMCP_HOME=/data/fastmcp \
    WHOOP_TOKEN_FILE=/data/whoop-token.json

VOLUME ["/data"]

EXPOSE 8000

CMD ["python", "-m", "whoop_mcp.server"]
