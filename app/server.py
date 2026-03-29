"""
ASGI application (FastAPI). Used by Vercel via api/index.py and locally via main.py + uvicorn.
"""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.llm_service import llm_service
from app.mcp import router as mcp_router
from app.web import router as web_router

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Grafana to Kibana Converter",
    description="Convert Grafana dashboards to Kibana format using Model Context Protocol",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=os.path.join(_BASE_DIR, "static")), name="static")

app.include_router(mcp_router, prefix="/mcp", tags=["Model Context Protocol"])
app.include_router(web_router, tags=["Web Interface"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "grafana-to-kibana-converter",
        "environment": settings.environment,
        "llm_enabled": llm_service.is_available(),
        "llm_provider": settings.llm_provider if llm_service.is_available() else None,
    }
