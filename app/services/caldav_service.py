"""CalDAV service for Baïkal integration"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import caldav
from caldav.lib.error import DAVError
from ics import Calendar as ICSCalendar, Event as ICSEvent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models.caldav import CalDAVEvent, CalDAVCalendar, EventMapping


# Helper function to run synchronous caldav operations in thread pool
async def _run_caldav_sync(func, *args, **kwargs):
    """Run synchronous caldav operation in thread pool"""
    return await asyncio.to_thread(func, *args, **kwargs)


logger = logging.getLogger(__name__)


class CalDAVError(Exception):
    """CalDAV error"""
    pass


class CalDAVService:
    """Service for interacting with CalDAV server (Baïkal)"""

    def __init__(self):
        self.url = settings.caldav_url
        self.username = settings.caldav_username
        self.password = settings.caldav_password
        self.auth_type = settings.caldav_auth_type

        # Log configuration (without sensitive data)
        logger.info(f"Initializing CalDAV client with URL: {self.url}")
        logger.info(f"Auth type: {self.auth_type}")
        logger.info(f"Username configured: {'Yes' if self.username else 'No'}")
        logger.info(f"Password configured: {'Yes' if self.password else 'No'}")

        # Initialize client
        try:
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
                auth_type=self.auth_type,
                ssl_verify_cert=True
            )
            logger.debug("CalDAV client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CalDAV client: {e}")
            raise

        # Cache for calendars
        self._calendar_cache: Dict[str, caldav.Calendar] = {}
        self._cache_expiry = datetime.now()

    async def _get_calendar_client(self, calendar_url: str) -> caldav.Calendar:
        """Get or create calendar client"""
        # Check cache expiry (reduced to 10 minutes for better freshness)
        if datetime.now() > self._cache_expiry + timedelta(minutes=10):
            logger.debug("Clearing calendar cache due to expiry")
            self._calendar_cache.clear()
            self._cache_expiry = datetime.now()

        if calendar_url not in self._calendar_cache:
            try:
                logger.debug(f"Fetching calendar {calendar_url} from server")
                principal = await _run_caldav_sync(self.client.principal)
                calendars = await _run_caldav_sync(principal.calendars)

                # Find calendar by URL
                for cal in calendars:
                    if str(cal.url) == calendar_url or str(cal.url).rstrip('/') == calendar_url.rstrip('/'):
                        self._calendar_cache[calendar_url] = cal
                        logger.debug(f"✅ Cached calendar {calendar_url}")
                        return cal

                logger.warning(f"Calendar not found in server response: {calendar_url}")
                raise CalDAVError(f"Calendar not found: {calendar_url}")
            except DAVError as e:
                logger.error(f"CalDAV protocol error getting calendar {calendar_url}: {e}")
                raise CalDAVError(f"Failed to get calendar: {e}")
            except Exception as e:
                logger.error(f"Unexpected error getting calendar {calendar_url}: {e}")
                raise CalDAVError(f"Calendar not found: {calendar_url}")

        return self._calendar_cache[calendar_url]

    async def refresh_calendar_cache(self) -> None:
        """Force refresh of calendar cache"""
        logger.info("Forcing refresh of calendar cache")
        self._calendar_cache.clear()
        self._cache_expiry = datetime.now()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def get_calendars(self) -> List[CalDAVCalendar]:
        """Get all available calendars"""
        try:
            logger.debug("Attempting to connect to CalDAV server...")
            principal = await _run_caldav_sync(self.client.principal)
            calendars = await _run_caldav_sync(principal.calendars)

            result = []
            for cal in calendars:
                calendar_url = str(cal.url)
                calendar_name = cal.name or "Unnamed Calendar"

                # Skip inbox calendar as it's for scheduling/invitations, not regular events
                if 'inbox' in calendar_url.lower() or calendar_name.lower() == 'inbox':
                    logger.debug(f"Skipping inbox calendar: {calendar_url}")
                    continue

                calendar_info = CalDAVCalendar(
                    id=cal.id or cal.url.path.split('/')[-1],
                    name=calendar_name,
                    description=getattr(cal, 'description', None),
                    url=calendar_url,
                    color=getattr(cal, 'color', None),
                    timezone=getattr(cal, 'timezone', None),
                    ctag=getattr(cal, 'ctag', None),
                    sync_token=getattr(cal, 'sync_token', None)
                )
                result.append(calendar_info)

            logger.info(f"Successfully retrieved {len(result)} calendars from CalDAV")
            return result

        except DAVError as e:
            logger.error(f"CalDAV protocol error getting calendars: {e}")
            # Handle specific HTTP status codes
            if hasattr(e, 'status'):
                if e.status == 401:
                    logger.error("Authentication failed - check CalDAV credentials")
                elif e.status == 403:
                    logger.error("Access forbidden - check CalDAV permissions")
                elif e.status == 404:
                    logger.error("CalDAV server not found - check URL")
                elif e.status == 418:
                    logger.warning("Server returned 418 (I'm a teapot) - this may indicate unsupported operation")
                    return []  # Return empty list instead of failing
                else:
                    logger.error(f"CalDAV server returned HTTP {e.status}")
            raise CalDAVError(f"Failed to get calendars: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting calendars: {e}")
            # Don't raise error for connection issues, just log and return empty list
            if "connection" in str(e).lower() or "network" in str(e).lower():
                logger.warning("Network connectivity issue - returning empty calendar list")
                return []
            raise CalDAVError(f"Unexpected error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def create_calendar(self, name: str, description: Optional[str] = None) -> CalDAVCalendar:
        """Create new calendar"""
        try:
            principal = await _run_caldav_sync(self.client.principal)
            calendar = await _run_caldav_sync(principal.make_calendar, name=name)

            calendar_url = str(calendar.url)
            calendar_info = CalDAVCalendar(
                id=calendar.id or calendar.url.path.split('/')[-1],
                name=name,
                description=description,
                url=calendar_url
            )

            # Cache the calendar object immediately
            self._calendar_cache[calendar_url] = calendar

            logger.info(f"Created calendar: {name}")
            return calendar_info

        except DAVError as e:
            logger.error(f"CalDAV error creating calendar: {e}")
            raise CalDAVError(f"Failed to create calendar: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def get_calendar_events(
        self,
        calendar_url: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalDAVEvent]:
        """Get events from calendar"""
        try:
            calendar = await self._get_calendar_client(calendar_url)

            # Get events
            events_data = await _run_caldav_sync(calendar.events)

            result = []
            for event_data in events_data:
                # Parse ICS data
                ics_calendar = ICSCalendar(event_data.data)
                for ics_event in ics_calendar.events:
                    # Handle both datetime and date objects (for all-day events)
                    # ics_event.begin/end can be Arrow datetime or plain date objects
                    if hasattr(ics_event.begin, 'datetime'):
                        start = ics_event.begin.datetime
                    elif isinstance(ics_event.begin, datetime):
                        start = ics_event.begin
                    else:
                        # It's a date object - convert to datetime at midnight
                        start = datetime.combine(ics_event.begin, datetime.min.time())

                    if ics_event.end:
                        if hasattr(ics_event.end, 'datetime'):
                            end = ics_event.end.datetime
                        elif isinstance(ics_event.end, datetime):
                            end = ics_event.end
                        else:
                            # It's a date object - convert to datetime at midnight
                            end = datetime.combine(ics_event.end, datetime.min.time())
                    else:
                        end = None

                    event = CalDAVEvent(
                        uid=ics_event.uid,
                        summary=ics_event.name,
                        description=ics_event.description,
                        location=ics_event.location,
                        start=start,
                        end=end,
                        status=ics_event.status,
                        organizer=str(ics_event.organizer) if ics_event.organizer else None,
                        attendees=[str(att) for att in ics_event.attendees],
                        categories=list(ics_event.categories),
                        url=ics_event.url,
                        created=ics_event.created.datetime if ics_event.created else None,
                        last_modified=ics_event.last_modified.datetime if ics_event.last_modified else None,
                        raw_ics=ics_event.serialize() if hasattr(ics_event, 'serialize') else None
                    )
                    result.append(event)

            logger.info(f"Retrieved {len(result)} events from calendar {calendar_url}")
            return result

        except DAVError as e:
            logger.error(f"CalDAV error getting events: {e}")
            raise CalDAVError(f"Failed to get events: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def create_event(
        self,
        calendar_url: str,
        event: CalDAVEvent
    ) -> str:
        """Create new event in calendar"""
        try:
            calendar = await self._get_calendar_client(calendar_url)

            # Create ICS event
            ics_event = ICSEvent()
            ics_event.uid = event.uid
            ics_event.name = event.summary
            ics_event.description = event.description
            ics_event.location = event.location

            # Handle ALL-DAY events (DATE instead of DATETIME)
            if event.all_day:
                # For all-day events, use date objects (not datetime)
                ics_event.begin = event.start.date()
                ics_event.end = event.end.date() if event.end else (event.start + timedelta(days=1)).date()
                ics_event.make_all_day()
            else:
                # Regular timed events
                ics_event.begin = event.start
                ics_event.end = event.end or (event.start + timedelta(hours=settings.event_default_duration_hours))

            ics_event.status = event.status
            ics_event.categories = set(event.categories) if event.categories else set()
            ics_event.url = event.url

            # Add color for Apple Calendar and other CalDAV clients
            # Note: Colors in ICS are not widely supported, so we skip them for now
            # to avoid compatibility issues with various calendar clients
            # if event.color:
            #     # Color support is limited and non-standard
            #     pass

            if event.organizer:
                ics_event.organizer = event.organizer

            if event.attendees:
                # Ensure proper mailto: format for attendees (RFC 5545)
                ics_event.attendees = [
                    f"mailto:{att}" if not att.startswith("mailto:") else att
                    for att in event.attendees
                ]

            # Create calendar with event
            ics_calendar = ICSCalendar()
            ics_calendar.creator = "CalPlaneBot/1.0"  # Sets PRODID to avoid warnings
            ics_calendar.events.add(ics_event)

            # Save to CalDAV (use serialize() instead of str() to avoid FutureWarning)
            calendar_event = await _run_caldav_sync(calendar.save_event, ics_calendar.serialize())

            logger.info(f"Created event: {event.summary} in calendar {calendar_url}")
            return event.uid

        except DAVError as e:
            logger.error(f"CalDAV error creating event: {e}")
            raise CalDAVError(f"Failed to create event: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def update_event(
        self,
        calendar_url: str,
        event_uid: str,
        updated_event: CalDAVEvent
    ) -> None:
        """Update existing event by UID (uses direct URL lookup, no extra server requests)"""
        try:
            calendar = await self._get_calendar_client(calendar_url)

            # Try to get event directly by UID (more efficient than fetching all events)
            # Build event URL from calendar URL and event UID
            event_url = f"{calendar_url.rstrip('/')}/{event_uid}.ics"

            try:
                # Try direct access first (no server request for event list)
                target_event = await _run_caldav_sync(calendar.event_by_url, event_url)
            except Exception:
                # Fallback: search through all events (slower but more reliable)
                logger.debug(f"Direct event access failed, falling back to search for {event_uid}")
                events = await _run_caldav_sync(calendar.events)
                target_event = None

                for event_data in events:
                    ics_calendar = ICSCalendar(event_data.data)
                    for ics_event in ics_calendar.events:
                        if ics_event.uid == event_uid:
                            target_event = event_data
                            break
                    if target_event:
                        break

            if not target_event:
                raise CalDAVError(f"Event {event_uid} not found")

            # Update ICS event
            ics_event = ICSEvent()
            ics_event.uid = updated_event.uid
            ics_event.name = updated_event.summary
            ics_event.description = updated_event.description
            ics_event.location = updated_event.location

            # Handle ALL-DAY events (DATE instead of DATETIME)
            if updated_event.all_day:
                # For all-day events, use date objects (not datetime)
                ics_event.begin = updated_event.start.date()
                ics_event.end = updated_event.end.date() if updated_event.end else (updated_event.start + timedelta(days=1)).date()
                ics_event.make_all_day()
            else:
                # Regular timed events
                ics_event.begin = updated_event.start
                ics_event.end = updated_event.end or (updated_event.start + timedelta(hours=settings.event_default_duration_hours))

            ics_event.status = updated_event.status
            ics_event.categories = set(updated_event.categories) if updated_event.categories else set()
            # Only set URL if it's a valid string (not None or empty)
            if updated_event.url and isinstance(updated_event.url, str):
                ics_event.url = updated_event.url

            # Add color for Apple Calendar and other CalDAV clients
            # Note: Colors in ICS are not widely supported, so we skip them for now
            # to avoid compatibility issues with various calendar clients
            # if updated_event.color:
            #     # Color support is limited and non-standard
            #     pass

            if updated_event.organizer:
                ics_event.organizer = updated_event.organizer

            if updated_event.attendees:
                # Ensure proper mailto: format for attendees (RFC 5545)
                ics_event.attendees = [
                    f"mailto:{att}" if not att.startswith("mailto:") else att
                    for att in updated_event.attendees
                ]

            # Create calendar with updated event
            ics_calendar = ICSCalendar()
            ics_calendar.creator = "CalPlaneBot/1.0"  # Sets PRODID to avoid warnings
            ics_calendar.events.add(ics_event)

            # Update in CalDAV (use serialize() instead of str() to avoid FutureWarning)
            target_event.data = ics_calendar.serialize()
            await _run_caldav_sync(target_event.save)

            logger.info(f"Updated event: {event_uid}")

        except DAVError as e:
            logger.error(f"CalDAV error updating event: {e}")
            raise CalDAVError(f"Failed to update event: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(CalDAVError)
    )
    async def delete_event(self, calendar_url: str, event_uid: str) -> None:
        """Delete event from calendar by UID (uses direct URL lookup, no extra server requests)"""
        try:
            calendar = await self._get_calendar_client(calendar_url)

            # Try to get event directly by UID (more efficient than fetching all events)
            event_url = f"{calendar_url.rstrip('/')}/{event_uid}.ics"

            try:
                # Try direct access first
                target_event = await _run_caldav_sync(calendar.event_by_url, event_url)
                await _run_caldav_sync(target_event.delete)
                logger.info(f"Deleted event: {event_uid}")
                return
            except Exception:
                # Fallback: search through all events
                logger.debug(f"Direct event access failed, falling back to search for {event_uid}")
                events = await _run_caldav_sync(calendar.events)

                for event_data in events:
                    ics_calendar = ICSCalendar(event_data.data)
                    for ics_event in ics_calendar.events:
                        if ics_event.uid == event_uid:
                            await _run_caldav_sync(event_data.delete)
                            logger.info(f"Deleted event: {event_uid}")
                            return

            raise CalDAVError(f"Event {event_uid} not found")

        except DAVError as e:
            logger.error(f"CalDAV error deleting event: {e}")
            raise CalDAVError(f"Failed to delete event: {e}")

    async def test_connection(self) -> bool:
        """Test CalDAV connection"""
        try:
            logger.info("Testing CalDAV connection...")

            # Force refresh cache before testing
            await self.refresh_calendar_cache()

            calendars = await self.get_calendars()
            logger.info(f"✅ CalDAV connection test successful. Found {len(calendars)} calendars: {[c.name for c in calendars]}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ CalDAV connection test failed: {e}")
            logger.info("Note: This is expected with test credentials. Real credentials should work.")
            return False


# Global instance
caldav_service = CalDAVService()

