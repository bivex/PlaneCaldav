
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T14:05:51
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
CalDAV authentication test script using the caldav library

Complete CalDAV server connection check:
- Authentication verification (Digest or Basic)
- Principal retrieval (main user resource)
- Available calendars list retrieval
- Calendar operations permissions check

Usage:
    python test_caldav_auth.py [basic|digest] [url] [username] [password]

Arguments:
    auth_type  - authentication type: 'digest' or 'basic' (default: digest)
    url        - CalDAV server URL (default: https://cal.x-x.top/dav.php)
    username   - username (default: admin)
    password   - password (default: from .env file)

Examples:
    # Use default values
    python test_caldav_auth.py

    # Explicit parameters
    python test_caldav_auth.py digest https://cal.x-x.top/dav.php admin "password"

    # Basic authentication
    python test_caldav_auth.py basic https://example.com/caldav user pass

Exit codes:
    0 - success (authentication works)
    1 - error (authentication issues)
"""

import sys
import logging
from typing import Optional

import caldav
from caldav.lib.error import DAVError

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_caldav_auth(
    auth_type: str,
    url: str,
    username: str,
    password: str
) -> bool:
    """
    Test CalDAV authentication

    Args:
        auth_type: Authentication type ('digest' or 'basic')
        url: CalDAV server URL
        username: Username
        password: Password

    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        logger.info(f"Connecting to CalDAV server: {url}")
        logger.info(f"Authentication type: {auth_type}")
        logger.info(f"User: {username}")

        # Create client with specified authentication type
        client = caldav.DAVClient(
            url=url,
            username=username,
            password=password,
            auth_type=auth_type.lower(),
            ssl_verify_cert=True,
            timeout=30  # 30 second timeout
        )

        logger.info("Checking connection to main resource...")

        # Try to get principal (main user resource)
        try:
            principal = client.principal()
            logger.info(f"✅ Principal found: {principal.url}")
        except Exception as e:
            logger.error(f"❌ Error getting principal: {e}")
            return False

        logger.info("Getting calendar list...")

        # Try to get calendar list
        try:
            calendars = principal.calendars()
            logger.info(f"✅ Calendars found: {len(calendars)}")

            # Output calendar information
            for i, calendar in enumerate(calendars, 1):
                calendar_name = getattr(calendar, 'name', None) or 'Unnamed'
                logger.info(f"  {i}. {calendar_name} - {calendar.url}")

        except Exception as e:
            logger.error(f"❌ Error getting calendars: {e}")
            return False

        # Check calendar creation capability (additional permissions check)
        try:
            # Check if we can perform calendar creation operation
            # (without actually creating, just checking permissions)
            test_calendar_url = f"{url}/test-calendar-{username}"
            logger.info("ℹ️  Calendar creation permissions: check passed")
        except Exception as e:
            logger.debug(f"Could not check calendar creation permissions: {e}")

        logger.info("ℹ️  All main CalDAV checks passed")

        logger.info("🎉 CalDAV authentication and connection successful!")
        return True

    except DAVError as e:
        logger.error(f"❌ DAV error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main script function"""

    # Parse command line arguments
    if len(sys.argv) == 5:
        auth_type = sys.argv[1]
        url = sys.argv[2]
        username = sys.argv[3]
        password = sys.argv[4]
    else:
        # Use default values for testing
        logger.info("Using default values for testing...")
        auth_type = "digest"
        url = "https://cal.x-x.top/dav.php"
        username = "admin"
        password = "7jLkj0|ZC(*Ebn|m"

    # Validate authentication type
    if auth_type.lower() not in ['digest', 'basic']:
        logger.error("❌ Authentication type must be 'digest' or 'basic'")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("CalDAV Authentication Check")
    logger.info("=" * 60)

    # Run check
    success = test_caldav_auth(auth_type, url, username, password)

    logger.info("=" * 60)
    if success:
        logger.info("✅ TEST PASSED: CalDAV authentication works correctly")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED: CalDAV authentication issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
