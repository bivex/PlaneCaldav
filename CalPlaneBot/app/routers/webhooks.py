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

"""Webhook API routes"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

from app.services.webhook_handler import webhook_handler
from app.services.scheduler_service import scheduler_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/plane")
async def plane_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle webhook from Plane"""
    try:
        # Get headers
        headers = dict(request.headers)

        # Get payload
        payload = await request.json()

        logger.info(f"Received webhook from Plane: {payload.get('action', 'unknown')} {payload.get('event', 'unknown')}")

        # Process webhook in background
        background_tasks.add_task(
            webhook_handler.handle_plane_webhook,
            headers,
            payload
        )

        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"Failed to process Plane webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")


@router.post("/sync")
async def trigger_sync() -> Dict[str, Any]:
    """Manually trigger synchronization"""
    try:
        result = await scheduler_service.trigger_manual_sync()
        return result

    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")


@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """Get synchronization status"""
    try:
        scheduler_status = scheduler_service.get_scheduler_status()
        sync_stats = scheduler_service.sync_service.get_sync_stats()

        return {
            "scheduler": scheduler_status,
            "sync_stats": sync_stats
        }

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")



