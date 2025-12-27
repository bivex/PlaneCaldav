# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T14:05:45
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""CalPlaneBot - Plane to CalDAV integration service"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers.webhooks import router as webhook_router
from app.services.scheduler_service import scheduler_service
from app.services.sync_service import sync_service
from app.services.caldav_service import caldav_service


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Suppress caldav library warnings about icalendar compatibility
# (These are harmless - the library auto-fixes the data)
logging.getLogger("caldav").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting CalPlaneBot...")

    # Startup
    try:
        # Test CalDAV connection
        connection_ok = await caldav_service.test_connection()
        if not connection_ok:
            logger.warning("CalDAV connection test failed - some features may not work")

        # Start scheduler
        await scheduler_service.start_scheduler()

        logger.info("CalPlaneBot started successfully")

    except Exception as e:
        logger.error(f"Failed to start CalPlaneBot: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CalPlaneBot...")
    await scheduler_service.stop_scheduler()
    logger.info("CalPlaneBot shut down")


# Create FastAPI app
app = FastAPI(
    title="CalPlaneBot",
    description="Integration service for synchronizing Plane tasks with CalDAV calendars",
    version=settings.version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": "Plane to CalDAV integration service"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.version
    }


@app.get("/api/v1/health")
async def api_health_check():
    """Detailed health check"""
    try:
        # Test CalDAV connection
        caldav_ok = await caldav_service.test_connection()

        # Get sync stats
        sync_stats = sync_service.get_sync_stats()

        # Get scheduler status
        scheduler_status = scheduler_service.get_scheduler_status()

        return {
            "status": "healthy",
            "services": {
                "caldav": "ok" if caldav_ok else "error",
                "scheduler": scheduler_status["status"]
            },
            "stats": sync_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
