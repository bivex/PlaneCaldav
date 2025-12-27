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

"""Plane data models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PlaneUser(BaseModel):
    """Plane user model"""
    id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class PlaneState(BaseModel):
    """Plane state model"""
    id: str
    name: str
    color: str
    group: str


class PlanePriority(BaseModel):
    """Plane priority model"""
    id: str
    name: str
    color: str


class PlaneLabel(BaseModel):
    """Plane label model"""
    id: str
    name: str
    color: str


class PlaneIssue(BaseModel):
    """Plane issue model"""
    id: str
    name: str
    description: Optional[str] = None
    description_html: Optional[str] = None
    sequence_id: int
    sort_order: float
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Relations - API returns IDs as strings, not objects
    project_id: str = Field(alias="project")
    workspace_id: str = Field(alias="workspace")

    # State and priority - API returns ID as string
    state_id: str = Field(alias="state")
    priority: Optional[str] = None

    # Assignments
    assignee_ids: List[str] = Field(default_factory=list)
    assignees: List[PlaneUser] = Field(default_factory=list)

    # Labels and other metadata
    label_ids: List[str] = Field(default_factory=list)
    labels: List[PlaneLabel] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # URLs
    link: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class PlaneProject(BaseModel):
    """Plane project model"""
    id: str
    name: str
    description: Optional[str] = None
    identifier: str
    emoji: Optional[str] = None
    color: Optional[str] = None

    # Relations
    workspace_id: str = Field(alias="workspace")

    # Settings
    is_favorite: bool = False
    sort_order: Optional[float] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class PlaneWebhookPayload(BaseModel):
    """Plane webhook payload model"""
    event: str  # "issue"
    action: str  # "create", "update", "delete"
    webhook_id: str
    workspace_id: str

    data: PlaneIssue
    activity: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True



