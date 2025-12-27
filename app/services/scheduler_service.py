# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T18:43:42
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Scheduler service for periodic synchronization"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.sync_service import sync_service


logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic tasks"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False

    async def start_scheduler(self) -> None:
        """Start the scheduler"""
        if self.scheduler:
            return

        self.scheduler = AsyncIOScheduler()

        # Add regular sync job (updated issues)
        if settings.enable_sync:
            sync_trigger = IntervalTrigger(
                seconds=settings.sync_interval_seconds,
                start_date=datetime.now() + timedelta(seconds=10)  # Start after 10 seconds
            )

            self.scheduler.add_job(
                self._sync_job,
                trigger=sync_trigger,
                id="plane_caldav_sync",
                name="Sync Plane issues to CalDAV",
                max_instances=1,
                replace_existing=True
            )

            logger.info(f"Scheduled sync job every {settings.sync_interval_seconds} seconds")

            # Add cleanup job (full sync every hour)
            logger.info("Adding cleanup job...")
            cleanup_trigger = IntervalTrigger(
                hours=1,
                start_date=datetime.now() + timedelta(seconds=30)  # Start after 30 seconds
            )

            self.scheduler.add_job(
                self._cleanup_job,
                trigger=cleanup_trigger,
                id="plane_caldav_cleanup",
                name="Cleanup deleted/archived Plane issues from CalDAV",
                max_instances=1,
                replace_existing=True
            )

            logger.info("Scheduled cleanup job every hour")
            logger.info("Cleanup job added successfully")

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        logger.info("Scheduler started")

    async def stop_scheduler(self) -> None:
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
            self.is_running = False

        logger.info("Scheduler stopped")

    async def _sync_job(self) -> None:
        """Scheduled sync job"""
        try:
            logger.info("Starting scheduled sync")

            # Get last sync time (simplified - should be persisted)
            last_sync = datetime.now() - timedelta(seconds=settings.sync_interval_seconds)

            # Sync updated issues
            await sync_service.sync_updated_issues(last_sync)

            logger.info("Scheduled sync completed")

        except Exception as e:
            logger.error(f"Scheduled sync failed: {e}")

    async def _cleanup_job(self) -> None:
        """Scheduled cleanup job - full sync to remove deleted/archived issues"""
        try:
            logger.info("Starting scheduled cleanup (full sync)")

            # Perform full sync to clean up deleted/archived issues
            await sync_service.sync_all_projects()

            logger.info("Scheduled cleanup completed")

        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")

    async def trigger_manual_sync(self) -> Dict[str, Any]:
        """Trigger manual synchronization"""
        try:
            logger.info("Starting manual sync")

            start_time = datetime.now()
            await sync_service.sync_all_projects()
            end_time = datetime.now()

            stats = sync_service.get_sync_stats()

            result = {
                "status": "success",
                "duration_seconds": (end_time - start_time).total_seconds(),
                "stats": stats
            }

            logger.info(f"Manual sync completed in {result['duration_seconds']:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        if not self.scheduler:
            return {"status": "stopped"}

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "status": "running",
            "jobs": jobs
        }


# Global instance
scheduler_service = SchedulerService()

