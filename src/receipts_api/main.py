"""
receipts_api.main
-----------------
Application entry point.

  Local dev:   uv run uvicorn receipts_api.main:app --reload
  Script:      uv run receipts-api
  Direct:      python -m receipts_api.main
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP

from receipts_api.routers import receipts, stats

app = FastAPI(
    title="Receipts Statistics API",
    description=(
        "Browse receipt records and retrieve SQL-style grouped statistics "
        "loaded from monthly CSV exports. Also available as MCP tools at /mcp."
    ),
    version="1.0.0",
)

# CORS — allow all origins for the public GitHub Pages dashboard demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Register routers — stats must come before receipts so /receipts/stats
# is matched before /receipts/{receipt_id}.
app.include_router(stats.router)
app.include_router(receipts.router)

# Mount MCP server — exposes all FastAPI routes as MCP tools at GET /mcp
# using Streamable HTTP transport (MCP spec 2025-03-26).
mcp = FastApiMCP(app)
mcp.mount_http()


def main() -> None:
    """Entrypoint for `uv run receipts-api`."""
    import uvicorn

    uvicorn.run("receipts_api.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    main()
