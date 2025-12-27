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

"""Default configuration values for CalPlaneBot"""

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8765

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Sync settings
SYNC_INTERVAL = 60  # seconds (1 minute)
SYNC_ENABLED = True

# CalDAV settings
CALDAV_TIMEOUT = 30  # seconds
CALDAV_USER_AGENT = "CalPlaneBot/0.1.0"

# Event mapping settings
EVENT_DURATION_HOURS = 1  # Default duration for events without due dates
TIMEZONE = "Europe/Moscow"

# Webhook settings
WEBHOOK_TIMEOUT = 30  # seconds
WEBHOOK_MAX_RETRIES = 5
WEBHOOK_RETRY_DELAY = 600  # seconds

# Cache settings
CACHE_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 1000

