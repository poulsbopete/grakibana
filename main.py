#!/usr/bin/env python3
"""
Local development entry point. Production on Vercel uses api/index.py → app.server:app.
"""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level,
    )
