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
Script to clean all CalDAV calendars except the main one

Deletes all user calendars, keeping only the main calendar (usually default).
Useful for cleanup after testing.
"""

import sys
import logging
from typing import List

import caldav
from caldav.lib.error import DAVError

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_calendars(
    url: str,
    username: str,
    password: str,
    auth_type: str = "digest",
    keep_default: bool = True,
    auto_confirm: bool = False
) -> int:
    """
    Clean CalDAV calendars

    Args:
        url: CalDAV server URL
        username: Username
        password: Password
        auth_type: Authentication type ('digest' or 'basic')
        keep_default: Whether to keep the default calendar

    Returns:
        int: Number of deleted calendars
    """
    try:
        logger.info(f"Connecting to CalDAV server: {url}")
        logger.info(f"Authentication type: {auth_type}")
        logger.info(f"User: {username}")

        # Create client
        client = caldav.DAVClient(
            url=url,
            username=username,
            password=password,
            auth_type=auth_type.lower(),
            ssl_verify_cert=True,
            timeout=30
        )

        # Get principal
        principal = client.principal()
        logger.info(f"Principal found: {principal.url}")

        # Get calendar list
        calendars = principal.calendars()
        logger.info(f"Calendars found: {len(calendars)}")

        if not calendars:
            logger.info("No calendars to delete")
            return 0

        # List calendars
        for i, cal in enumerate(calendars, 1):
            logger.info(f"  {i}. {cal.name} - {cal.url}")

        # Determine default calendar
        default_calendar = None
        if keep_default:
            # Look for calendar named "default" or first calendar
            for cal in calendars:
                if cal.name and cal.name.lower() in ['default', 'main']:
                    default_calendar = cal
                    break
            # If not found, take first calendar
            if not default_calendar and calendars:
                default_calendar = calendars[0]
                logger.info(f"Default calendar not found, keeping first: {default_calendar.name}")

        # Calendars to delete
        calendars_to_delete = [cal for cal in calendars if cal != default_calendar]

        if not calendars_to_delete:
            logger.info("No calendars to delete")
            return 0

        logger.info(f"Calendars to be deleted: {len(calendars_to_delete)}")

        # Confirm deletion (only if not auto mode)
        if len(calendars_to_delete) > 5 and not auto_confirm:
            print(f"\n⚠️  WARNING: {len(calendars_to_delete)} calendars will be deleted!")
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                logger.info("Operation cancelled by user")
                return 0

        # Delete calendars
        deleted_count = 0
        for cal in calendars_to_delete:
            try:
                logger.info(f"Deleting calendar: {cal.name}")
                cal.delete()
                deleted_count += 1
                logger.info(f"✅ Calendar deleted: {cal.name}")
            except Exception as e:
                logger.error(f"❌ Error deleting calendar {cal.name}: {e}")

        if default_calendar and keep_default:
            logger.info(f"✅ Default calendar kept: {default_calendar.name}")

        logger.info(f"🎉 Calendars deleted: {deleted_count}")
        return deleted_count

    except DAVError as e:
        logger.error(f"❌ DAV error: {e}")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 0


def main():
    """Main script function"""

    # Parse arguments
    auto_confirm = "--auto" in sys.argv
    if auto_confirm:
        sys.argv.remove("--auto")

    if len(sys.argv) >= 4:
        auth_type = sys.argv[1] if len(sys.argv) > 4 else "digest"
        url = sys.argv[-3]
        username = sys.argv[-2]
        password = sys.argv[-1]
    else:
        # Default values
        logger.info("Using default values...")
        auth_type = "digest"
        url = "https://cal.x-x.top/dav.php"
        username = "admin"
        password = "7jLkj0|ZC(*Ebn|m"

    logger.info("=" * 60)
    logger.info("CALDAV CALENDARS CLEANUP")
    if auto_confirm:
        logger.info("🚀 Automatic mode (no confirmation)")
    logger.info("=" * 60)

    # Run cleanup
    deleted_count = clean_calendars(url, username, password, auth_type, auto_confirm=auto_confirm)

    logger.info("=" * 60)
    if deleted_count > 0:
        logger.info(f"✅ SUCCESS: Deleted {deleted_count} calendars")
        sys.exit(0)
    else:
        logger.info("ℹ️  Nothing deleted")
        sys.exit(0)


if __name__ == "__main__":
    main()
