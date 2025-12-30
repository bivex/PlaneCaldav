# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T17:53:28
# Last Updated: 2025-12-30T10:03:06
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Plane API service for CalPlaneBot"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models.plane import PlaneIssue, PlaneProject, PlaneState


logger = logging.getLogger(__name__)


class PlaneAPIError(Exception):
    """Plane API error"""
    pass


class PlaneService:
    """Service for interacting with Plane API"""

    def __init__(self):
        self.base_url = settings.plane_api_url
        self.workspace_slug = settings.plane_workspace_slug
        self.headers = {
            "X-API-Key": settings.plane_api_token,
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(30.0)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Plane API"""
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Plane API error: {e.response.status_code} - {e.response.text}")
                raise PlaneAPIError(f"API request failed: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Plane API request error: {e}")
                raise PlaneAPIError(f"Request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(PlaneAPIError)
    )
    async def get_projects(self) -> List[PlaneProject]:
        """Get all projects in workspace"""
        endpoint = f"/workspaces/{self.workspace_slug}/projects/"
        data = await self._make_request("GET", endpoint)

        projects = []
        for item in data.get("results", []):
            project = PlaneProject(**item)
            projects.append(project)

        logger.info(f"Retrieved {len(projects)} projects from Plane")
        return projects

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(PlaneAPIError)
    )
    async def get_project_issues(
        self,
        project_id: str,
        updated_after: Optional[datetime] = None
    ) -> List[PlaneIssue]:
        """Get issues for a specific project"""
        endpoint = f"/workspaces/{self.workspace_slug}/projects/{project_id}/issues/"

        params = {}
        if updated_after:
            params["updated_at__gt"] = updated_after.isoformat()

        data = await self._make_request("GET", endpoint, params=params)

        issues = []
        for item in data.get("results", []):
            issue = PlaneIssue(**item)
            issues.append(issue)

        logger.info(f"Retrieved {len(issues)} issues for project {project_id}")
        return issues

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(PlaneAPIError)
    )
    async def get_issue(self, project_id: str, issue_id: str) -> PlaneIssue:
        """Get single issue details"""
        endpoint = f"/workspaces/{self.workspace_slug}/projects/{project_id}/issues/{issue_id}/"
        data = await self._make_request("GET", endpoint)

        return PlaneIssue(**data)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(PlaneAPIError)
    )
    async def get_all_issues(
        self,
        updated_after: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PlaneIssue]:
        """Get all issues across all projects"""
        projects = await self.get_projects()

        all_issues = []
        for project in projects:
            try:
                issues = await self.get_project_issues(
                    project.id,
                    updated_after=updated_after
                )
                all_issues.extend(issues)
            except Exception as e:
                logger.error(f"Failed to get issues for project {project.id}: {e}")
                continue

        logger.info(f"Retrieved {len(all_issues)} total issues from all projects")
        return all_issues

    async def get_states(self, project_id: str) -> List[PlaneState]:
        """Get states for a project"""
        endpoint = f"/workspaces/{self.workspace_slug}/projects/{project_id}/states/"
        data = await self._make_request("GET", endpoint)

        states = []
        for item in data.get("results", []):
            state = PlaneState(**item)
            states.append(state)

        return states

    def is_issue_completed(self, issue: PlaneIssue) -> bool:
        """Check if issue is completed"""
        # Issue is completed if it has completed_at timestamp OR is in completed/cancelled state
        return issue.completed_at is not None

    def should_exclude_from_calendar(self, issue: PlaneIssue) -> bool:
        """Check if issue should be excluded from calendar (completed/cancelled)"""
        # Issue should be excluded if it's completed_at is set (legacy way)
        # OR if it's in completed/cancelled state group
        # For now, we use completed_at as it's simpler and doesn't require additional API calls
        return issue.completed_at is not None

    def is_issue_in_completed_group(self, issue: PlaneIssue, states: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Check if issue is in completed/cancelled state group (more accurate method)"""
        if not states:
            # Fallback to completed_at check
            return issue.completed_at is not None

        # Find the state for this issue
        issue_state = None
        for state in states:
            if state.get("id") == issue.state_id:
                issue_state = state
                break

        if not issue_state:
            return issue.completed_at is not None

        # Check if state group indicates completion
        state_group = issue_state.get("group", "").lower()
        return state_group in ["completed", "cancelled"]

    def get_issue_url(self, issue: PlaneIssue) -> str:
        """Generate issue URL"""
        return f"{settings.plane_base_url}/{self.workspace_slug}/projects/{issue.project_id}/issues/{issue.id}"

    def get_issue_priority_color(self, issue: PlaneIssue) -> str:
        """Get priority color for issue (CalDAV compatible)"""
        # Apple Calendar and most CalDAV clients support these colors
        priority_colors = {
            "urgent": "#FF3B30",  # Red
            "high": "#FF9500",    # Orange
            "medium": "#007AFF",  # Blue
            "low": "#34C759"      # Green
        }
        return priority_colors.get(issue.priority, "#8E8E93")  # Default gray

    def format_issue_description(self, issue: PlaneIssue) -> str:
        """Format issue description for calendar event"""
        description_parts = []

        if issue.description:
            description_parts.append(f"Description: {issue.description}")

        if issue.assignees:
            assignee_names = [assignee.display_name for assignee in issue.assignees]
            description_parts.append(f"Assignees: {', '.join(assignee_names)}")

        if issue.labels:
            label_names = [label.name for label in issue.labels]
            description_parts.append(f"Labels: {', '.join(label_names)}")

        description_parts.append(f"URL: {self.get_issue_url(issue)}")

        return "\n\n".join(description_parts)


# Global instance
plane_service = PlaneService()

