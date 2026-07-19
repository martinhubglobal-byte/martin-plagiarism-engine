"""FastAPI app factory for the engine."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from noplag_engine.api.v1 import checks, corpus

_DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"


def create_app() -> FastAPI:
    app = FastAPI(title="Noplag Engine", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe — no DB call. Used by uptime monitors and compose
        healthchecks."""
        return {"status": "ok"}

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
