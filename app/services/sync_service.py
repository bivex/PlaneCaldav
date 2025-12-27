# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T19:37:51
# Last Updated: 2025-12-27T19:37:51
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Synchronization service between Plane and CalDAV"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import uuid4

from app.config import settings
from app.models.plane import PlaneIssue, PlaneProject
from app.models.caldav import CalDAVEvent, SyncMapping, EventMapping
from app.services.plane_service import plane_service
from app.services.caldav_service import caldav_service


logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing Plane issues with CalDAV events"""

    def __init__(self):
        # In-memory mappings (should be persisted in production)
        self.project_mappings: Dict[str, SyncMapping] = {}
        self.event_mappings: Dict[str, EventMapping] = {}

        # Per-sync events cache: calendar_url -> {event_uid -> CalDAVEvent}
        # This cache is populated at the start of sync and cleared at the end
        self._events_cache: Dict[str, Dict[str, CalDAVEvent]] = {}

        # Sync lock to prevent overlapping syncs
        self._sync_in_progress = False

    async def initialize_project_mappings(self) -> None:
        """Initialize calendar mappings for Plane projects"""
        try:
            logger.info("=== STARTING PROJECT MAPPINGS INITIALIZATION ===")

            # Get all Plane projects
            projects = await plane_service.get_projects()
            logger.info(f"Found {len(projects)} Plane projects: {[p.name for p in projects]}")

            # Refresh CalDAV cache and get all calendars
            await caldav_service.refresh_calendar_cache()
            calendars = await caldav_service.get_calendars()
            logger.info(f"Found {len(calendars)} existing calendars: {[c.name for c in calendars]}")

            # Track which calendar URLs have been assigned to avoid duplicates
            used_calendar_urls = set()

            # Create mappings for each project
            for project in projects:
                expected_calendar_name = f"Plane: {project.name}"
                logger.info(f"Processing project '{project.name}' → looking for calendar '{expected_calendar_name}'")

                # Find existing calendar that matches this project and hasn't been used yet
                calendar = None
                for cal in calendars:
                    # Skip if this calendar URL was already assigned to another project
                    if cal.url in used_calendar_urls:
                        logger.debug(f"  Skipping {cal.name} (already assigned)")
                        continue

                    # Check if calendar name matches (exact match, case-insensitive)
                    if cal.name.lower() == expected_calendar_name.lower():
                        calendar = cal
                        logger.info(f"  ✓ Found existing calendar: {cal.name}")
                        break

                if not calendar:
                    # No existing calendar found - create new one
                    logger.info(f"  No existing calendar found, creating new: {expected_calendar_name}")
                    calendar = await caldav_service.create_calendar(
                        name=expected_calendar_name,
                        description=f"Tasks from Plane project: {project.name}"
                    )
                    logger.info(f"  ✓ Created new calendar: {expected_calendar_name}")

                # Mark this calendar URL as used
                used_calendar_urls.add(calendar.url)

                # Store mapping
                mapping = SyncMapping(
                    plane_project_id=project.id,
                    caldav_calendar_url=calendar.url,
                    last_sync=None
                )
                self.project_mappings[project.id] = mapping

                logger.info(f"  ✓ Mapped project '{project.name}' → calendar '{calendar.name}' ({calendar.url})")

            logger.info(f"=== FINISHED: Created {len(self.project_mappings)} project→calendar mappings ===")

        except Exception as e:
            logger.error(f"Failed to initialize project mappings: {e}")
            raise

    def get_calendar_for_project(self, project_id: str) -> Optional[str]:
        """Get CalDAV calendar URL for Plane project"""
        mapping = self.project_mappings.get(project_id)
        return mapping.caldav_calendar_url if mapping else None

    async def _get_events_cache(self, calendar_url: str) -> Dict[str, CalDAVEvent]:
        """Get or populate events cache for a calendar (O(1) lookup by UID)"""
        if calendar_url not in self._events_cache:
            events = await caldav_service.get_calendar_events(calendar_url)
            # Build a dict for O(1) lookup by UID
            self._events_cache[calendar_url] = {event.uid: event for event in events}
            logger.debug(f"Cached {len(events)} events for calendar {calendar_url}")
        return self._events_cache[calendar_url]

    def _clear_events_cache(self) -> None:
        """Clear the per-sync events cache"""
        self._events_cache.clear()
        logger.debug("Cleared events cache")

    def _invalidate_event_in_cache(self, calendar_url: str, event_uid: str, new_event: Optional[CalDAVEvent] = None) -> None:
        """Update or remove a single event from cache"""
        if calendar_url in self._events_cache:
            if new_event:
                self._events_cache[calendar_url][event_uid] = new_event
            elif event_uid in self._events_cache[calendar_url]:
                del self._events_cache[calendar_url][event_uid]

    def plane_issue_to_caldav_event(self, issue: PlaneIssue) -> Optional[CalDAVEvent]:
        """Convert Plane issue to CalDAV event

        Returns None if issue has no target_date (no deadline = no calendar event)
        """
        # CRITICAL RULE: No target_date → no event
        if not issue.target_date:
            return None

        # Generate unique UID
        uid = f"plane-issue-{issue.id}@{settings.app_name.lower()}"

        # Create ALL-DAY event using Plane dates
        # Plane has: start_date (optional) and target_date (due date)
        # - If both exist: event spans from start_date to target_date
        # - If only target_date: single-day event on target_date
        if issue.start_date and issue.start_date < issue.target_date:
            # Multi-day event: start_date to target_date
            start_time = datetime.combine(issue.start_date, datetime.min.time())
            end_time = datetime.combine(issue.target_date, datetime.min.time())
        else:
            # Single-day event on target_date
            start_time = datetime.combine(issue.target_date, datetime.min.time())
            end_time = start_time
        all_day = True

        # Set status based on completion state
        # ICS library only supports: None, 'TENTATIVE', 'CONFIRMED', 'CANCELLED'
        # Use CANCELLED for completed issues (will show as strikethrough in most clients)
        if plane_service.is_issue_completed(issue):
            status = "CANCELLED"
        else:
            status = "CONFIRMED"

        # Set categories (labels + priority + completion status)
        categories = []
        if plane_service.is_issue_completed(issue):
            categories.append("Completed")
        if issue.labels:
            categories.extend([label.name for label in issue.labels])
        if issue.priority:
            categories.append(f"Priority: {issue.priority}")

        # Set attendees
        attendees = []
        if issue.assignees:
            attendees.extend([assignee.email for assignee in issue.assignees if assignee.email])

        # Set event color based on priority
        event_color = plane_service.get_issue_priority_color(issue)

        # Create description
        description = plane_service.format_issue_description(issue)

        return CalDAVEvent(
            uid=uid,
            summary=f"[{issue.sequence_id}] {issue.name}",
            description=description,
            start=start_time,
            end=end_time,
            all_day=all_day,
            status=status,
            categories=categories,
            attendees=attendees,
            color=event_color,
            url=plane_service.get_issue_url(issue)
        )

    async def sync_issue_to_calendar(
        self,
        issue: PlaneIssue,
        calendar_url: str,
        use_cache: bool = True
    ) -> None:
        """Sync single issue to calendar

        Args:
            issue: Plane issue to sync
            calendar_url: Target CalDAV calendar URL
            use_cache: If True, use cached events for O(1) lookup (default: True)
        """
        try:
            # Convert to CalDAV event
            event = self.plane_issue_to_caldav_event(issue)
            event_uid = f"plane-issue-{issue.id}@{settings.app_name.lower()}"

            # If no target_date → no event
            if event is None:
                # Check if event exists in calendar and delete it
                try:
                    await caldav_service.delete_event(calendar_url, event_uid)
                    self._invalidate_event_in_cache(calendar_url, event_uid)
                    logger.info(f"Deleted event for issue {issue.sequence_id} (no target_date)")
                except Exception:
                    # Event doesn't exist or already deleted - that's fine
                    pass
                return

            # Check if event already exists using cache (O(1) lookup)
            if use_cache:
                events_cache = await self._get_events_cache(calendar_url)
                existing_event = events_cache.get(event.uid)
            else:
                # Fallback to direct query (for webhook handlers, etc.)
                existing_events = await caldav_service.get_calendar_events(calendar_url)
                existing_event = next((e for e in existing_events if e.uid == event.uid), None)

            if existing_event:
                # Update existing event
                await caldav_service.update_event(calendar_url, event.uid, event)
                self._invalidate_event_in_cache(calendar_url, event.uid, event)
                logger.info(f"Updated event for issue {issue.sequence_id}: {issue.name}")
            else:
                # Create new event
                await caldav_service.create_event(calendar_url, event)
                self._invalidate_event_in_cache(calendar_url, event.uid, event)
                logger.info(f"Created event for issue {issue.sequence_id}: {issue.name}")

            # Update mapping
            mapping = EventMapping(
                plane_issue_id=issue.id,
                caldav_event_uid=event.uid,
                caldav_calendar_url=calendar_url,
                last_sync=datetime.now(),
                plane_updated_at=issue.updated_at
            )
            self.event_mappings[issue.id] = mapping

        except Exception as e:
            logger.error(f"Failed to sync issue {issue.id} to calendar: {e}")
            raise

    async def sync_project_issues_with_cleanup(self, project_id: str, calendar_url: str) -> tuple[int, int]:
        """Sync all issues for a project and return (synced_count, deleted_count)

        Uses cached events for O(1) lookups - only 1 CalDAV request per project!
        """
        try:
            # Get ALL issues from Plane (including completed ones)
            # Completed issues will be synced with STATUS:COMPLETED (strikethrough in calendar)
            issues = await plane_service.get_project_issues(project_id)

            logger.info(f"Syncing {len(issues)} issues (including completed) for project {project_id}")

            # Get existing events from cache (single CalDAV request, O(1) lookup)
            events_cache = await self._get_events_cache(calendar_url)

            # Create sets of UIDs for comparison
            current_issue_uids: Set[str] = set()
            for issue in issues:
                uid = f"plane-issue-{issue.id}@{settings.app_name.lower()}"
                current_issue_uids.add(uid)

            existing_event_uids = set(events_cache.keys())

            # Find events to delete (exist in calendar but not in current issues)
            events_to_delete = existing_event_uids - current_issue_uids

            # Delete old events
            deleted_count = 0
            for event_uid in events_to_delete:
                try:
                    await caldav_service.delete_event(calendar_url, event_uid)
                    self._invalidate_event_in_cache(calendar_url, event_uid)
                    logger.info(f"Deleted old event {event_uid} for project {project_id}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete event {event_uid}: {e}")

            # Sync each current issue (uses cache internally)
            synced_count = 0
            for issue in issues:
                await self.sync_issue_to_calendar(issue, calendar_url, use_cache=True)
                synced_count += 1

            # Update project mapping sync time
            if project_id in self.project_mappings:
                self.project_mappings[project_id].last_sync = datetime.now()
                self.project_mappings[project_id].events_created = len(issues)

            return synced_count, deleted_count

        except Exception as e:
            logger.error(f"Failed to sync project {project_id}: {e}")
            raise

    async def sync_project_issues(self, project_id: str) -> None:
        """Sync all issues for a project

        Uses cached events for O(1) lookups - only 1 CalDAV request per project!
        """
        try:
            # Get calendar for project
            calendar_url = self.get_calendar_for_project(project_id)
            if not calendar_url:
                logger.warning(f"No calendar mapping found for project {project_id}")
                return

            # Get ALL issues from Plane (including completed ones)
            # Completed issues will be synced with STATUS:COMPLETED (strikethrough in calendar)
            issues = await plane_service.get_project_issues(project_id)

            logger.info(f"Syncing {len(issues)} issues (including completed) for project {project_id}")

            # Get existing events from cache (single CalDAV request, O(1) lookup)
            events_cache = await self._get_events_cache(calendar_url)

            # Create sets of UIDs for comparison
            current_issue_uids: Set[str] = set()
            for issue in issues:
                uid = f"plane-issue-{issue.id}@{settings.app_name.lower()}"
                current_issue_uids.add(uid)

            existing_event_uids = set(events_cache.keys())

            # Find events to delete (exist in calendar but not in current issues)
            events_to_delete = existing_event_uids - current_issue_uids

            # Delete old events
            deleted_count = 0
            for event_uid in events_to_delete:
                try:
                    await caldav_service.delete_event(calendar_url, event_uid)
                    self._invalidate_event_in_cache(calendar_url, event_uid)
                    logger.info(f"Deleted old event {event_uid} for project {project_id}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete event {event_uid}: {e}")

            # Sync each current issue (uses cache internally)
            synced_count = 0
            for issue in issues:
                await self.sync_issue_to_calendar(issue, calendar_url, use_cache=True)
                synced_count += 1

            # Update project mapping sync time
            if project_id in self.project_mappings:
                self.project_mappings[project_id].last_sync = datetime.now()
                self.project_mappings[project_id].events_created = len(issues)

            logger.info(f"Synced {synced_count} issues, deleted {deleted_count} old events for project {project_id}")

        except Exception as e:
            logger.error(f"Failed to sync project {project_id}: {e}")
            raise

    async def sync_all_projects(self) -> None:
        """Sync all projects with sync lock and cache management"""
        # Prevent overlapping syncs
        if self._sync_in_progress:
            logger.warning("Sync already in progress, skipping this cycle")
            return

        self._sync_in_progress = True
        try:
            # Initialize mappings if needed
            if not self.project_mappings:
                await self.initialize_project_mappings()

            # Sync each project (cache is populated per-calendar automatically)
            for project_id in self.project_mappings.keys():
                await self.sync_project_issues(project_id)

            logger.info("Completed sync of all projects")

        except Exception as e:
            logger.error(f"Failed to sync all projects: {e}")
            raise
        finally:
            # Always clear cache and release lock
            self._clear_events_cache()
            self._sync_in_progress = False

    async def sync_updated_issues(self, since: datetime) -> None:
        """Sync all projects to detect deleted issues and sync updates.

        IMPORTANT: We sync ALL projects, not just those with updated issues.
        This is necessary because deleted issues don't appear in 'updated_after' queries,
        so we need to compare calendar events with current Plane issues for each project.
        """
        # Prevent overlapping syncs
        if self._sync_in_progress:
            logger.warning("Sync already in progress, skipping this cycle")
            return

        self._sync_in_progress = True
        try:
            logger.info(f"sync_updated_issues called with since={since}")
            # Always reinitialize mappings to avoid stale data after container restarts
            logger.info("Reinitializing project mappings...")
            await self.initialize_project_mappings()

            # Sync ALL projects to detect deleted issues
            # (deleted issues don't appear in updated_after queries)
            total_synced = 0
            total_deleted = 0

            for project_id, mapping in self.project_mappings.items():
                calendar_url = mapping.caldav_calendar_url
                if calendar_url:
                    synced_count, deleted_count = await self.sync_project_issues_with_cleanup(
                        project_id, calendar_url
                    )
                    total_synced += synced_count
                    total_deleted += deleted_count

            logger.info(f"Synced {total_synced} issues, deleted {total_deleted} old events across all projects")

        except Exception as e:
            logger.error(f"Failed to sync updated issues: {e}")
            raise
        finally:
            # Always clear cache and release lock
            self._clear_events_cache()
            self._sync_in_progress = False

    async def cleanup_completed_events(self) -> None:
        """Remove events for completed issues (optional cleanup)"""
        try:
            # This could be implemented to remove old completed events
            # to keep calendars clean
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup completed events: {e}")

    def get_sync_stats(self) -> Dict[str, int]:
        """Get synchronization statistics"""
        total_projects = len(self.project_mappings)
        total_events = len(self.event_mappings)

        completed_events = sum(
            1 for mapping in self.event_mappings.values()
            if mapping.plane_updated_at and mapping.last_sync
        )

        return {
            "total_projects": total_projects,
            "total_events": total_events,
            "synced_events": completed_events
        }


# Global instance
sync_service = SyncService()

