#!/usr/bin/env python3
"""
Grafana to Kibana Dashboard Converter
Main application entry point
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.mcp import router as mcp_router
from app.web import router as web_router
from app.config import settings
from app.llm_service import llm_service

# Create FastAPI app
app = FastAPI(
    title="Grafana to Kibana Converter",
    description="Convert Grafana dashboards to Kibana format using Model Context Protocol",
    version="1.0.0"
)

# Create necessary directories
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.download_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(mcp_router, prefix="/mcp", tags=["Model Context Protocol"])
app.include_router(web_router, tags=["Web Interface"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "grafana-to-kibana-converter",
        "environment": settings.environment,
        "llm_enabled": llm_service.is_available(),
        "llm_provider": settings.llm_provider if llm_service.is_available() else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level
    ) 