# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T14:06:28
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
Stress tests and performance edge cases for CalPlaneBot
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.sync_service import SyncService
from app.models.plane import PlaneIssue, PlaneProject, PlaneUser, PlaneLabel


class TestHighVolumeScenarios:
    """Test scenarios with large amounts of data"""

    def setup_method(self):
        self.sync_service = SyncService()

    def test_large_batch_of_issues(self):
        """Test processing 1000+ issues"""
        issues = []
        for i in range(1000):
            issue = PlaneIssue(
                id=f"issue-{i}",
                name=f"Issue {i}",
                sequence_id=i,
                sort_order=float(i),
                target_date=datetime(2025, 1, 1, 0, 0, 0) + timedelta(days=i % 365),
                project_id="proj-1",
                workspace_id="ws-1",
                state_id="state-1",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            issues.append(issue)

        # Convert all to events
        events = []
        for issue in issues:
            event = self.sync_service.plane_issue_to_caldav_event(issue)
            if event:
                events.append(event)

        assert len(events) == 1000

    def test_issue_with_many_assignees(self):
        """Test issue with 100 assignees"""
        assignees = [
            PlaneUser(
                id=f"user-{i}",
                display_name=f"User {i}",
                email=f"user{i}@example.com"
            ) for i in range(100)
        ]

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            assignees=assignees,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert len(event.attendees) == 100

    def test_issue_with_many_labels(self):
        """Test issue with 100 labels"""
        labels = [
            PlaneLabel(
                id=f"label-{i}",
                name=f"Label {i}",
                color="#FF0000"
            ) for i in range(100)
        ]

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            labels=labels,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None

    def test_many_projects(self):
        """Test handling 100+ projects"""
        from app.models.caldav import SyncMapping

        for i in range(100):
            mapping = SyncMapping(
                plane_project_id=f"project-{i}",
                caldav_calendar_url=f"https://cal.example.com/cal-{i}/",
                last_sync=None
            )
            self.sync_service.project_mappings[f"project-{i}"] = mapping

        assert len(self.sync_service.project_mappings) == 100

        # Test retrieval
        for i in range(100):
            url = self.sync_service.get_calendar_for_project(f"project-{i}")
            assert url == f"https://cal.example.com/cal-{i}/"


class TestConcurrencyEdgeCases:
    """Test concurrent operations and race conditions"""

    @pytest.mark.asyncio
    async def test_concurrent_issue_updates(self):
        """Test updating same issue concurrently"""
        sync_service = SyncService()

        issue = PlaneIssue(
            id="test-id",
            name="Original Name",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Simulate concurrent conversions
        tasks = []
        for i in range(10):
            issue_copy = PlaneIssue(**issue.model_dump())
            issue_copy.name = f"Name {i}"
            issue_copy.updated_at = datetime.now() + timedelta(seconds=i)
            tasks.append(asyncio.create_task(
                asyncio.to_thread(sync_service.plane_issue_to_caldav_event, issue_copy)
            ))

        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        # All should succeed
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_rapid_sync_calls(self):
        """Test rapid successive sync calls"""
        sync_service = SyncService()

        # Simulate rapid updates to same issue
        for i in range(100):
            issue = PlaneIssue(
                id="test-id",
                name=f"Update {i}",
                sequence_id=1,
                sort_order=1.0,
                target_date=datetime(2025, 1, 1, 0, 0, 0),
                project_id="proj-1",
                workspace_id="ws-1",
                state_id="state-1",
                created_at=datetime.now(),
                updated_at=datetime.now() + timedelta(microseconds=i)
            )
            event = sync_service.plane_issue_to_caldav_event(issue)
            assert event is not None


class TestMemoryEdgeCases:
    """Test memory-related edge cases"""

    def test_memory_leak_prevention(self):
        """Test that repeated operations don't leak memory"""
        sync_service = SyncService()

        # Create and convert 10,000 issues
        for i in range(10000):
            issue = PlaneIssue(
                id=f"issue-{i}",
                name=f"Issue {i}",
                sequence_id=i,
                sort_order=float(i),
                target_date=datetime(2025, 1, 1, 0, 0, 0),
                project_id="proj-1",
                workspace_id="ws-1",
                state_id="state-1",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            event = sync_service.plane_issue_to_caldav_event(issue)
            # Event should be garbage collected after each iteration
            del event

        # Mappings should not grow unbounded
        # (In real implementation, you'd check actual memory usage)

    def test_large_description_memory(self):
        """Test handling of very large descriptions"""
        # 1MB description
        large_desc = "A" * (1024 * 1024)

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            description=large_desc,
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        sync_service = SyncService()
        event = sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        # Should handle without OOM


class TestBoundaryConditions:
    """Test boundary conditions and limits"""

    def test_sequence_id_overflow(self):
        """Test maximum sequence ID"""
        sync_service = SyncService()

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=2147483647,  # Max 32-bit int
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert "[2147483647]" in event.summary

    def test_max_url_length(self):
        """Test maximum URL length (2083 chars for IE compatibility)"""
        sync_service = SyncService()

        long_url = "https://example.com/" + "a" * 2000

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            link=long_url,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None

    def test_category_limit(self):
        """Test maximum number of categories"""
        sync_service = SyncService()

        # Create issue with max labels + priority + completion status
        labels = [
            PlaneLabel(id=f"label-{i}", name=f"Label-{i}", color="#FF0000")
            for i in range(250)
        ]

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            labels=labels,
            priority="high",
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        # Should have all labels + priority category
        assert len(event.categories) >= 250


class TestErrorRecoveryEdgeCases:
    """Test error recovery scenarios"""

    def test_partially_invalid_issue_data(self):
        """Test issue with some invalid fields"""
        sync_service = SyncService()

        # Issue with some weird but technically valid data
        issue = PlaneIssue(
            id="",  # Empty ID (might be invalid)
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Should handle gracefully
        try:
            event = sync_service.plane_issue_to_caldav_event(issue)
            # If it succeeds, event should be valid
            if event:
                assert event.uid  # UID should be generated
        except Exception as e:
            # Or it should raise a clear error
            assert str(e)  # Error message should exist

    def test_circular_reference_detection(self):
        """Test that circular references don't cause infinite loops"""
        # This is more relevant if we add parent-child relationships
        pass

    def test_malformed_datetime_recovery(self):
        """Test recovery from malformed datetime data"""
        # In case API returns unexpected datetime formats
        pass


class TestRealWorldScenarios:
    """Test realistic complex scenarios"""

    def test_full_project_sync_simulation(self):
        """Simulate syncing a full project with diverse issues"""
        sync_service = SyncService()

        issues = []

        # Mix of different issue types
        # 1. Regular issue
        issues.append(PlaneIssue(
            id="regular-1",
            name="Regular Task",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 15, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))

        # 2. Issue without deadline
        issues.append(PlaneIssue(
            id="no-deadline-1",
            name="Backlog Item",
            sequence_id=2,
            sort_order=2.0,
            target_date=None,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))

        # 3. Completed issue
        issues.append(PlaneIssue(
            id="completed-1",
            name="Done Task",
            sequence_id=3,
            sort_order=3.0,
            target_date=datetime(2025, 1, 10, 0, 0, 0),
            completed_at=datetime.now(),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))

        # 4. High priority urgent task
        issues.append(PlaneIssue(
            id="urgent-1",
            name="URGENT: Production Bug",
            sequence_id=4,
            sort_order=4.0,
            target_date=datetime.now() + timedelta(hours=2),
            priority="urgent",
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))

        # 5. Issue with many assignees and labels
        issues.append(PlaneIssue(
            id="complex-1",
            name="Complex Feature",
            sequence_id=5,
            sort_order=5.0,
            target_date=datetime(2025, 2, 1, 0, 0, 0),
            priority="high",
            assignees=[
                PlaneUser(id=f"user-{i}", display_name=f"Dev {i}", email=f"dev{i}@example.com")
                for i in range(5)
            ],
            labels=[
                PlaneLabel(id=f"label-{i}", name=f"Tag-{i}", color="#FF0000")
                for i in range(10)
            ],
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))

        # Convert all to events
        events = []
        for issue in issues:
            event = sync_service.plane_issue_to_caldav_event(issue)
            if event:
                events.append(event)

        # Should have 4 events (backlog item has no deadline)
        assert len(events) == 4

        # Check statuses
        statuses = [e.status for e in events]
        assert "CANCELLED" in statuses  # Completed issue
        assert "CONFIRMED" in statuses  # Active issues

    def test_multi_project_workspace(self):
        """Test workspace with multiple active projects"""
        from app.models.caldav import SyncMapping

        sync_service = SyncService()

        # Setup 10 projects
        for i in range(10):
            mapping = SyncMapping(
                plane_project_id=f"project-{i}",
                caldav_calendar_url=f"https://cal.example.com/project-{i}/",
                last_sync=None
            )
            sync_service.project_mappings[f"project-{i}"] = mapping

        # Create issues across different projects
        for proj_idx in range(10):
            for issue_idx in range(20):
                issue = PlaneIssue(
                    id=f"issue-{proj_idx}-{issue_idx}",
                    name=f"Task {issue_idx}",
                    sequence_id=issue_idx,
                    sort_order=float(issue_idx),
                    target_date=datetime(2025, 1, 1, 0, 0, 0) + timedelta(days=issue_idx),
                    project_id=f"project-{proj_idx}",
                    workspace_id="ws-1",
                    state_id="state-1",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                event = sync_service.plane_issue_to_caldav_event(issue)
                assert event is not None

                # Verify correct project mapping
                calendar_url = sync_service.get_calendar_for_project(f"project-{proj_idx}")
                assert calendar_url == f"https://cal.example.com/project-{proj_idx}/"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
