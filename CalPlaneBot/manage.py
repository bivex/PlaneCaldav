# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T14:05:29
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
CalPlaneBot Management CLI
Manage and test CalPlaneBot integrations
"""

import argparse
import asyncio
import sys
from datetime import datetime
from typing import Optional

import httpx
from caldav import DAVClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings from .env file"""
    PLANE_BASE_URL: str
    PLANE_API_TOKEN: str
    PLANE_WORKSPACE_SLUG: str
    CALDAV_URL: str
    CALDAV_USERNAME: str
    CALDAV_PASSWORD: str

    class Config:
        env_file = ".env"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_success(text: str):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"✗ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ {text}")


class CalPlaneBotManager:
    """Management commands for CalPlaneBot"""

    def __init__(self):
        try:
            self.settings = Settings()
        except Exception as e:
            print_error(f"Failed to load settings: {e}")
            print_info("Make sure .env file exists and is properly configured")
            sys.exit(1)

    def test_caldav(self):
        """Test CalDAV connection"""
        print_header("Testing CalDAV Connection")

        try:
            print_info(f"Connecting to: {self.settings.CALDAV_URL}")
            print_info(f"Username: {self.settings.CALDAV_USERNAME}")

            client = DAVClient(
                url=self.settings.CALDAV_URL,
                username=self.settings.CALDAV_USERNAME,
                password=self.settings.CALDAV_PASSWORD
            )

            principal = client.principal()
            print_success(f"Connected to CalDAV server")
            print_info(f"Principal: {principal.url}")

            # List calendars
            calendars = principal.calendars()
            print_success(f"Found {len(calendars)} calendar(s)")

            for cal in calendars:
                print(f"  📅 {cal.name}")
                print(f"     URL: {cal.url}")

                # Count events
                events = cal.events()
                print(f"     Events: {len(events)}")

            return True

        except Exception as e:
            print_error(f"CalDAV connection failed: {e}")
            return False

    async def test_plane(self):
        """Test Plane API connection"""
        print_header("Testing Plane API Connection")

        try:
            print_info(f"Connecting to: {self.settings.PLANE_BASE_URL}")
            print_info(f"Workspace: {self.settings.PLANE_WORKSPACE_SLUG}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.PLANE_BASE_URL}/api/v1/workspaces/{self.settings.PLANE_WORKSPACE_SLUG}/",
                    headers={"X-API-Key": self.settings.PLANE_API_TOKEN},
                    timeout=30.0
                )

                if response.status_code == 200:
                    workspace = response.json()
                    print_success("Connected to Plane API")
                    print_info(f"Workspace Name: {workspace.get('name', 'N/A')}")
                    print_info(f"Workspace ID: {workspace.get('id', 'N/A')}")

                    # Get projects
                    projects_response = await client.get(
                        f"{self.settings.PLANE_BASE_URL}/api/v1/workspaces/{self.settings.PLANE_WORKSPACE_SLUG}/projects/",
                        headers={"X-API-Key": self.settings.PLANE_API_TOKEN},
                        timeout=30.0
                    )

                    if projects_response.status_code == 200:
                        projects = projects_response.json()
                        print_success(f"Found {len(projects)} project(s)")
                        for proj in projects[:5]:  # Show first 5
                            print(f"  📁 {proj.get('name', 'Unknown')}")

                    return True
                else:
                    print_error(f"Plane API returned status {response.status_code}")
                    print_info(f"Response: {response.text[:200]}")
                    return False

        except Exception as e:
            print_error(f"Plane API connection failed: {e}")
            return False

    async def trigger_sync(self):
        """Trigger manual sync via API"""
        print_header("Triggering Manual Sync")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8765/api/sync/trigger",
                    timeout=60.0
                )

                if response.status_code == 200:
                    result = response.json()
                    print_success("Sync triggered successfully")
                    print_info(f"Status: {result.get('status', 'unknown')}")
                    if 'events_synced' in result:
                        print_info(f"Events synced: {result['events_synced']}")
                    return True
                else:
                    print_error(f"Sync failed with status {response.status_code}")
                    print_info(f"Response: {response.text[:200]}")
                    return False

        except Exception as e:
            print_error(f"Failed to trigger sync: {e}")
            print_info("Make sure CalPlaneBot service is running on port 8765")
            return False

    async def check_status(self):
        """Check CalPlaneBot service status"""
        print_header("Checking CalPlaneBot Status")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8765/health",
                    timeout=10.0
                )

                if response.status_code == 200:
                    print_success("CalPlaneBot service is running")
                    data = response.json()
                    print_info(f"Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    print_error("CalPlaneBot service returned non-200 status")
                    return False

        except httpx.ConnectError:
            print_error("Cannot connect to CalPlaneBot service")
            print_info("Is the service running? Try: docker-compose ps")
            return False
        except Exception as e:
            print_error(f"Health check failed: {e}")
            return False

    def create_test_event(self, summary: str = "Test Event"):
        """Create a test event in CalDAV"""
        print_header("Creating Test Event")

        try:
            from icalendar import Calendar, Event as iCalEvent
            import uuid

            client = DAVClient(
                url=self.settings.CALDAV_URL,
                username=self.settings.CALDAV_USERNAME,
                password=self.settings.CALDAV_PASSWORD
            )

            principal = client.principal()
            calendars = principal.calendars()

            if not calendars:
                print_error("No calendars found. Create a calendar first.")
                return False

            # Use first calendar
            calendar = calendars[0]
            print_info(f"Using calendar: {calendar.name}")

            # Create event
            cal = Calendar()
            event = iCalEvent()
            event.add('summary', summary)
            event.add('dtstart', datetime.now())
            event.add('dtend', datetime.now())
            event.add('uid', str(uuid.uuid4()))
            cal.add_component(event)

            calendar.save_event(cal.to_ical().decode('utf-8'))
            print_success(f"Created event: {summary}")
            return True

        except Exception as e:
            print_error(f"Failed to create event: {e}")
            return False

    def list_calendars(self):
        """List all calendars and their events"""
        print_header("Listing Calendars and Events")

        try:
            client = DAVClient(
                url=self.settings.CALDAV_URL,
                username=self.settings.CALDAV_USERNAME,
                password=self.settings.CALDAV_PASSWORD
            )

            principal = client.principal()
            calendars = principal.calendars()

            if not calendars:
                print_info("No calendars found")
                return True

            for cal in calendars:
                print(f"\n📅 Calendar: {cal.name}")
                print(f"   URL: {cal.url}")

                try:
                    events = cal.events()
                    print(f"   Events: {len(events)}")

                    for event in events[:10]:  # Show first 10
                        ical = event.icalendar_component
                        summary = ical.get('summary', 'No title')
                        dtstart = ical.get('dtstart')
                        print(f"     • {summary}")
                        if dtstart:
                            print(f"       {dtstart.dt}")

                except Exception as e:
                    print_error(f"   Failed to list events: {e}")

            return True

        except Exception as e:
            print_error(f"Failed to list calendars: {e}")
            return False

    async def run_diagnostics(self):
        """Run full diagnostic tests"""
        print_header("Running Full Diagnostics")

        results = {
            'caldav': False,
            'plane': False,
            'service': False
        }

        # Test CalDAV
        results['caldav'] = self.test_caldav()

        # Test Plane
        results['plane'] = await self.test_plane()

        # Test Service
        results['service'] = await self.check_status()

        # Summary
        print_header("Diagnostic Summary")
        print(f"CalDAV Connection: {'✓ OK' if results['caldav'] else '✗ FAILED'}")
        print(f"Plane API:         {'✓ OK' if results['plane'] else '✗ FAILED'}")
        print(f"Service Status:    {'✓ OK' if results['service'] else '✗ FAILED'}")

        all_ok = all(results.values())
        if all_ok:
            print_success("\nAll systems operational!")
        else:
            print_error("\nSome systems are not working properly")

        return all_ok

    def show_config(self):
        """Show current configuration"""
        print_header("Current Configuration")

        print(f"Plane Base URL:      {self.settings.PLANE_BASE_URL}")
        print(f"Plane Workspace:     {self.settings.PLANE_WORKSPACE_SLUG}")
        print(f"Plane API Token:     {self.settings.PLANE_API_TOKEN[:20]}...")
        print(f"CalDAV URL:          {self.settings.CALDAV_URL}")
        print(f"CalDAV Username:     {self.settings.CALDAV_USERNAME}")
        print(f"CalDAV Password:     {'*' * len(self.settings.CALDAV_PASSWORD)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CalPlaneBot Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s test-caldav              # Test CalDAV connection
  %(prog)s test-plane               # Test Plane API connection
  %(prog)s sync                     # Trigger manual sync
  %(prog)s diagnostics              # Run full diagnostics
  %(prog)s create-event "My Event"  # Create test event
  %(prog)s list                     # List calendars and events
        """
    )

    parser.add_argument(
        'command',
        choices=[
            'test-caldav',
            'test-plane',
            'sync',
            'status',
            'diagnostics',
            'create-event',
            'list',
            'config'
        ],
        help='Command to execute'
    )

    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments'
    )

    args = parser.parse_args()

    manager = CalPlaneBotManager()

    # Execute command
    if args.command == 'test-caldav':
        success = manager.test_caldav()
        sys.exit(0 if success else 1)

    elif args.command == 'test-plane':
        success = asyncio.run(manager.test_plane())
        sys.exit(0 if success else 1)

    elif args.command == 'sync':
        success = asyncio.run(manager.trigger_sync())
        sys.exit(0 if success else 1)

    elif args.command == 'status':
        success = asyncio.run(manager.check_status())
        sys.exit(0 if success else 1)

    elif args.command == 'diagnostics':
        success = asyncio.run(manager.run_diagnostics())
        sys.exit(0 if success else 1)

    elif args.command == 'create-event':
        summary = args.args[0] if args.args else "Test Event"
        success = manager.create_test_event(summary)
        sys.exit(0 if success else 1)

    elif args.command == 'list':
        success = manager.list_calendars()
        sys.exit(0 if success else 1)

    elif args.command == 'config':
        manager.show_config()
        sys.exit(0)


if __name__ == '__main__':
    main()
