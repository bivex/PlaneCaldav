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

"""
Edge case tests for CalPlaneBot
Tests extreme scenarios, boundary conditions, and unusual data
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, AsyncMock

from app.services.sync_service import SyncService
from app.models.plane import PlaneIssue, PlaneUser, PlaneLabel
from app.models.caldav import CalDAVEvent


class TestIssueEdgeCases:
    """Test edge cases for Plane issues"""

    def setup_method(self):
        self.sync_service = SyncService()

    # ==================== DATETIME EDGE CASES ====================

    @pytest.mark.parametrize("target_date,expected_start", [
        # Leap year date
        (datetime(2024, 2, 29, 0, 0, 0), datetime(2024, 2, 29, 0, 0, 0)),
        # Last day of year
        (datetime(2024, 12, 31, 0, 0, 0), datetime(2024, 12, 31, 0, 0, 0)),
        # First day of year
        (datetime(2025, 1, 1, 0, 0, 0), datetime(2025, 1, 1, 0, 0, 0)),
        # DST transition day (US)
        (datetime(2024, 3, 10, 0, 0, 0), datetime(2024, 3, 10, 0, 0, 0)),
        # Very far future date
        (datetime(2099, 12, 31, 0, 0, 0), datetime(2099, 12, 31, 0, 0, 0)),
        # Very close to epoch
        (datetime(1970, 1, 2, 0, 0, 0), datetime(1970, 1, 2, 0, 0, 0)),
    ])
    def test_extreme_dates(self, target_date, expected_start):
        """Test extreme date values"""
        issue = PlaneIssue(
            id="test-id",
            name="Test Issue",
            sequence_id=1,
            sort_order=1.0,
            target_date=target_date,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert event.start == expected_start
        assert event.all_day is True

    def test_no_target_date(self):
        """Issue without target_date should return None event"""
        issue = PlaneIssue(
            id="test-id",
            name="Test Issue",
            sequence_id=1,
            sort_order=1.0,
            target_date=None,  # No deadline
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is None

    # ==================== STRING EDGE CASES ====================

    @pytest.mark.parametrize("name,expected_prefix", [
        # Empty string
        ("", "[1] "),
        # Single character
        ("x", "[1] x"),
        # Very long name (1000+ chars)
        ("A" * 1000, "[1] " + "A" * 1000),
        # Unicode characters
        ("测试🎉", "[1] 测试🎉"),
        # Emoji only
        ("🔥💻🚀", "[1] 🔥💻🚀"),
        # RTL text
        ("עברית", "[1] עברית"),
        # Mixed RTL and LTR
        ("Test עברית Test", "[1] Test עברית Test"),
        # Special characters
        ("Test\n\r\t<>&\"'", "[1] Test\n\r\t<>&\"'"),
        # SQL injection attempt
        ("'; DROP TABLE--", "[1] '; DROP TABLE--"),
        # XSS attempt
        ("<script>alert('xss')</script>", "[1] <script>alert('xss')</script>"),
        # Null bytes
        ("Test\x00Issue", "[1] Test\x00Issue"),
        # Unicode zero-width characters
        ("Test\u200BIssue", "[1] Test\u200BIssue"),
        # Surrogate pairs
        ("Test 𝕳𝖊𝖑𝖑𝖔", "[1] Test 𝕳𝖊𝖑𝖑𝖔"),
    ])
    def test_extreme_issue_names(self, name, expected_prefix):
        """Test issues with extreme name values"""
        issue = PlaneIssue(
            id="test-id",
            name=name,
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert event.summary.startswith(expected_prefix)

    @pytest.mark.parametrize("description", [
        None,  # No description
        "",  # Empty description
        " ",  # Just whitespace
        "\n\n\n",  # Just newlines
        "A" * 10000,  # Very long description (10k chars)
        "Line1\nLine2\nLine3\n" * 100,  # Many lines
        "<html><body>HTML content</body></html>",  # HTML content
        "```python\ncode = 'test'\n```",  # Markdown code block
    ])
    def test_extreme_descriptions(self, description):
        """Test issues with extreme description values"""
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            description=description,
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        # Should handle gracefully without crashing

    # ==================== PRIORITY EDGE CASES ====================

    @pytest.mark.parametrize("priority,should_work", [
        ("urgent", True),
        ("high", True),
        ("medium", True),
        ("low", True),
        (None, True),  # No priority
        ("", True),  # Empty priority
        ("URGENT", True),  # Uppercase
        ("invalid", True),  # Invalid priority
        ("extremely-urgent", True),  # Non-standard
        ("0", True),  # Numeric string
    ])
    def test_priority_values(self, priority, should_work):
        """Test various priority values"""
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            priority=priority,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert (event is not None) == should_work

    # ==================== ASSIGNEES & LABELS EDGE CASES ====================

    @pytest.mark.parametrize("assignee_count", [0, 1, 10, 100])
    def test_multiple_assignees(self, assignee_count):
        """Test issues with varying numbers of assignees"""
        assignees = [
            PlaneUser(
                id=f"user-{i}",
                display_name=f"User {i}",
                email=f"user{i}@example.com"
            ) for i in range(assignee_count)
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
        assert len(event.attendees) == assignee_count

    def test_assignees_without_email(self):
        """Test assignees missing email addresses"""
        assignees = [
            PlaneUser(id="user-1", display_name="User 1", email=None),
            PlaneUser(id="user-2", display_name="User 2", email=""),
            PlaneUser(id="user-3", display_name="User 3", email="valid@example.com"),
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
        # Should only include assignee with valid email
        assert len(event.attendees) == 1
        assert event.attendees[0] == "valid@example.com"

    @pytest.mark.parametrize("label_count", [0, 1, 50, 200])
    def test_multiple_labels(self, label_count):
        """Test issues with varying numbers of labels"""
        labels = [
            PlaneLabel(
                id=f"label-{i}",
                name=f"Label {i}",
                color="#FF0000"
            ) for i in range(label_count)
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
        # Categories should include labels
        assert len([c for c in event.categories if c.startswith("Label")]) == label_count

    # ==================== ID & SEQUENCE EDGE CASES ====================

    @pytest.mark.parametrize("sequence_id", [
        0,  # Zero
        1,  # Minimum valid
        9999999,  # Very large
        -1,  # Negative (might be invalid but test handling)
    ])
    def test_sequence_id_values(self, sequence_id):
        """Test various sequence ID values"""
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=sequence_id,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert f"[{sequence_id}]" in event.summary

    @pytest.mark.parametrize("issue_id", [
        "simple-id",
        "uuid-with-dashes-12345-67890",
        "id" * 100,  # Very long ID
        "id-with-special-chars-!@#$%",
        "🔥-emoji-id",
    ])
    def test_issue_id_formats(self, issue_id):
        """Test various issue ID formats"""
        issue = PlaneIssue(
            id=issue_id,
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

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        # UID should contain the issue ID
        assert issue_id in event.uid

    # ==================== COMPLETION STATUS EDGE CASES ====================

    @pytest.mark.parametrize("completed_at,expected_status", [
        (None, "CONFIRMED"),  # Not completed
        (datetime.now(), "CANCELLED"),  # Just completed
        (datetime.now() - timedelta(days=365), "CANCELLED"),  # Completed long ago
        (datetime.now() + timedelta(days=1), "CANCELLED"),  # Completed in "future" (clock skew)
    ])
    def test_completion_status(self, completed_at, expected_status):
        """Test various completion states"""
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            completed_at=completed_at,
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None
        assert event.status == expected_status

    # ==================== CONCURRENT MODIFICATION EDGE CASES ====================

    def test_rapidly_changing_issue(self):
        """Test issue that changes rapidly (updated_at vs created_at)"""
        created = datetime(2025, 1, 1, 0, 0, 0)
        updated = datetime(2025, 1, 1, 0, 0, 1)  # 1 second later

        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 15, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=created,
            updated_at=updated
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None

    # ==================== SORT ORDER EDGE CASES ====================

    @pytest.mark.parametrize("sort_order", [
        0.0,
        -1.0,
        999999.99,
        float('inf'),  # Infinity
        float('-inf'),  # Negative infinity
    ])
    def test_extreme_sort_orders(self, sort_order):
        """Test extreme sort order values"""
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=sort_order,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event = self.sync_service.plane_issue_to_caldav_event(issue)
        assert event is not None


class TestCalDAVEventEdgeCases:
    """Test edge cases for CalDAV events"""

    @pytest.mark.parametrize("status", [
        None,
        "TENTATIVE",
        "CONFIRMED",
        "CANCELLED",
    ])
    def test_valid_statuses(self, status):
        """Test all valid ICS status values"""
        event = CalDAVEvent(
            uid="test-uid",
            summary="Test",
            start=datetime(2025, 1, 1, 0, 0, 0),
            status=status
        )
        assert event.status == status

    def test_event_without_end_time(self):
        """Test event with no end time"""
        event = CalDAVEvent(
            uid="test-uid",
            summary="Test",
            start=datetime(2025, 1, 1, 0, 0, 0),
            end=None
        )
        assert event.end is None

    @pytest.mark.parametrize("url", [
        None,
        "",
        "http://example.com",
        "https://example.com/very/long/path?with=many&query=params",
        "ftp://oldschool.com",
        "mailto:test@example.com",
        "invalid-url",
    ])
    def test_event_urls(self, url):
        """Test various URL formats"""
        event = CalDAVEvent(
            uid="test-uid",
            summary="Test",
            start=datetime(2025, 1, 1, 0, 0, 0),
            url=url
        )
        assert event.url == url


class TestSyncEdgeCases:
    """Test edge cases during synchronization"""

    def setup_method(self):
        self.sync_service = SyncService()

    def test_empty_project_mappings(self):
        """Test when no projects are mapped"""
        assert len(self.sync_service.project_mappings) == 0
        calendar_url = self.sync_service.get_calendar_for_project("non-existent")
        assert calendar_url is None

    def test_duplicate_issue_ids(self):
        """Test handling of duplicate issue IDs"""
        # This tests UID generation uniqueness
        issue1 = PlaneIssue(
            id="duplicate-id",
            name="Issue 1",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        issue2 = PlaneIssue(
            id="duplicate-id",
            name="Issue 2",
            sequence_id=2,
            sort_order=2.0,
            target_date=datetime(2025, 1, 2, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        event1 = self.sync_service.plane_issue_to_caldav_event(issue1)
        event2 = self.sync_service.plane_issue_to_caldav_event(issue2)

        # Same ID should generate same UID
        assert event1.uid == event2.uid


class TestNetworkEdgeCases:
    """Test edge cases related to network/API interactions"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of network timeouts"""
        # This would be tested with proper mocking in integration tests
        pass

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test handling of API rate limits"""
        # This would be tested with proper mocking
        pass

    @pytest.mark.asyncio
    async def test_partial_response(self):
        """Test handling of incomplete API responses"""
        # This would be tested with proper mocking
        pass


class TestDataConsistencyEdgeCases:
    """Test data consistency edge cases"""

    def test_timezone_consistency(self):
        """Test that datetimes maintain timezone consistency"""
        # All dates should be treated consistently
        issue = PlaneIssue(
            id="test-id",
            name="Test",
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 12, 0, 0),  # Noon
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        sync_service = SyncService()
        event = sync_service.plane_issue_to_caldav_event(issue)

        # Should be converted to all-day event at midnight
        assert event.start.hour == 0
        assert event.start.minute == 0

    def test_unicode_normalization(self):
        """Test Unicode normalization consistency"""
        # Test that composed vs decomposed Unicode is handled consistently
        composed = "é"  # Single character
        decomposed = "é"  # e + combining accent

        issue1 = PlaneIssue(
            id="test-1",
            name=composed,
            sequence_id=1,
            sort_order=1.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        issue2 = PlaneIssue(
            id="test-2",
            name=decomposed,
            sequence_id=2,
            sort_order=2.0,
            target_date=datetime(2025, 1, 1, 0, 0, 0),
            project_id="proj-1",
            workspace_id="ws-1",
            state_id="state-1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        sync_service = SyncService()
        event1 = sync_service.plane_issue_to_caldav_event(issue1)
        event2 = sync_service.plane_issue_to_caldav_event(issue2)

        # Both should work without crashing
        assert event1 is not None
        assert event2 is not None
