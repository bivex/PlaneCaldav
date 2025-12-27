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

"""CalDAV data models"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ics import Event as ICSEvent


class CalDAVEvent(BaseModel):
    """CalDAV event model"""
    uid: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None

    # Timing
    start: datetime
    end: Optional[datetime] = None
    duration: Optional[timedelta] = None
    all_day: bool = False  # True for all-day events (DATE instead of DATETIME)

    # Status and classification
    status: Optional[str] = None  # TENTATIVE, CONFIRMED, CANCELLED
    classification: Optional[str] = None  # PUBLIC, PRIVATE, CONFIDENTIAL

    # Organizer and attendees
    organizer: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)

    # Categories and other metadata
    categories: List[str] = Field(default_factory=list)

    # Event color (CalDAV compatible)
    color: Optional[str] = None

    # URLs and references
    url: Optional[str] = None

    # Timestamps
    created: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    # Raw ICS data for advanced operations
    raw_ics: Optional[str] = None

    class Config:
        from_attributes = True


class CalDAVCalendar(BaseModel):
    """CalDAV calendar model"""
    id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

    # Calendar properties
    timezone: Optional[str] = None
    supported_components: List[str] = Field(default_factory=lambda: ["VEVENT"])

    # URLs
    url: str

    # Metadata
    ctag: Optional[str] = None  # Change tag for sync optimization
    sync_token: Optional[str] = None

    class Config:
        from_attributes = True


class CalDAVPrincipal(BaseModel):
    """CalDAV principal (user) model"""
    id: str
    url: str
    display_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class SyncMapping(BaseModel):
    """Mapping between Plane and CalDAV entities"""
    plane_project_id: str
    caldav_calendar_url: str

    # Sync metadata
    last_sync: Optional[datetime] = None
    sync_token: Optional[str] = None

    # Statistics
    events_created: int = 0
    events_updated: int = 0
    events_deleted: int = 0

    class Config:
        from_attributes = True


class EventMapping(BaseModel):
    """Mapping between Plane issue and CalDAV event"""
    plane_issue_id: str
    caldav_event_uid: str
    caldav_calendar_url: str

    # Sync metadata
    last_sync: datetime
    plane_updated_at: datetime
    caldav_updated_at: Optional[datetime] = None

    # Conflict resolution
    conflict_resolution: Optional[str] = None  # "plane_wins", "caldav_wins", "manual"

    class Config:
        from_attributes = True

