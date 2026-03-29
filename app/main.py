"""
Main FastAPI application for Grafana to Kibana converter
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from .web import router as web_router
from .mcp import router as mcp_router
from .config import settings, is_llm_enabled

# Create FastAPI app
app = FastAPI(
    title="Grakibana - Grafana to Kibana Converter",
    description="Convert Grafana dashboards to Kibana format with MCP support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(web_router, tags=["web"])
app.include_router(mcp_router, prefix="/mcp", tags=["mcp"])

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.environment,
            "llm_available": is_llm_enabled(),
            "llm_provider": settings.llm_provider if is_llm_enabled() else None
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return await health_check()

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    try:
        import time
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f'"{int(time.time())}"'
        }
        
        return FileResponse(
            "static/favicon.ico", 
            media_type="image/x-icon",
            headers=headers
        )
    except FileNotFoundError:
        # Return a simple 1x1 transparent PNG if favicon doesn't exist
        from fastapi.responses import Response
        return Response(
            content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82',
            media_type="image/png",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    ) 