"""FastAPI app factory for the engine."""

from __future__ import annotations
import os
import secrets
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from noplag_engine.api.v1 import checks, corpus
from sqlalchemy import text
from noplag_engine.db import get_sessionmaker

_DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"


def create_app() -> FastAPI:
    app = FastAPI(title="Noplag Engine", version="0.1.0")

    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        configured_key = os.environ.get("NOPLAG_API_KEY")

        if not configured_key:
            return JSONResponse(
                status_code=503,
                content={"detail": "API authentication is not configured"},
            )

        supplied_key = request.headers.get("X-API-Key", "")

        if not secrets.compare_digest(supplied_key, configured_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe — no DB call. Used by uptime monitors and compose
        healthchecks."""
        return {"status": "ok"}
        @app.get("/__diag/database", include_in_schema=False)
async def database_diagnostic():
    """Temporary protected database migration diagnostic."""
    async with get_sessionmaker()() as session:
        result = await session.execute(
            text("""
                SELECT
                    to_regclass('public.firebase_user_tenants')
                        IS NOT NULL AS tenant_table_exists,
                    (
                        SELECT version_num
                        FROM alembic_version
                        LIMIT 1
                    ) AS alembic_revision
            """)
        )
        row = result.mappings().one()

    return {
        "database_connected": True,
        "firebase_user_tenants_exists": row["tenant_table_exists"],
        "alembic_revision": row["alembic_revision"],
    }

    app.include_router(checks.router, prefix="/v1/checks", tags=["checks"])
    app.include_router(corpus.router, prefix="/v1/corpus", tags=["corpus"])

    # Bare demo page: paste text, run a check, see matched sources. Static
    # files only — the real UI belongs to whatever frontend you build on the
    # /v1 API.
    @app.get("/", include_in_schema=False)
    def demo_index() -> FileResponse:
        return FileResponse(_DEMO_DIR / "index.html")

    app.mount("/demo", StaticFiles(directory=_DEMO_DIR), name="demo")

    return app


# Module-level instance for uvicorn / ASGI servers: `uvicorn noplag_engine.api.app:app`.
app = create_app()
