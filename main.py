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
os.makedirs("uploads", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(mcp_router, prefix="/mcp", tags=["Model Context Protocol"])
app.include_router(web_router, tags=["Web Interface"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "grafana-to-kibana-converter"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 