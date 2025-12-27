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

"""Configuration validation for CalPlaneBot"""

import os
from typing import Dict, Any, List
from urllib.parse import urlparse


class ConfigValidationError(Exception):
    pass


def validate_required_env_vars(required_vars: List[str]) -> None:
    """Validate that all required environment variables are set"""
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        raise ConfigValidationError(f"Missing required environment variables: {', '.join(missing)}")


def validate_urls(urls: Dict[str, str]) -> None:
    """Validate URL format"""
    for name, url in urls.items():
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ConfigValidationError(f"Invalid URL format for {name}: {url}")
        except Exception as e:
            raise ConfigValidationError(f"Invalid URL format for {name}: {url} - {e}")


def validate_caldav_url(url: str) -> None:
    """Validate CalDAV URL format"""
    if not url:
        return

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise ConfigValidationError(f"CalDAV URL must use http or https scheme: {url}")

        # Check if it's a valid CalDAV path
        if not any(path in parsed.path for path in ['/caldav', '/dav', '/calendar']):
            print(f"Warning: CalDAV URL path might be incorrect: {parsed.path}")

    except Exception as e:
        raise ConfigValidationError(f"Invalid CalDAV URL format: {url} - {e}")


def validate_config() -> None:
    """Validate all configuration"""
    # Required environment variables
    required_vars = [
        "PLANE_BASE_URL",
        "PLANE_API_TOKEN",
        "PLANE_WORKSPACE_SLUG",
        "CALDAV_URL",
        "CALDAV_USERNAME",
        "CALDAV_PASSWORD"
    ]

    validate_required_env_vars(required_vars)

    # Validate URLs
    urls = {
        "PLANE_BASE_URL": os.getenv("PLANE_BASE_URL"),
        "CALDAV_URL": os.getenv("CALDAV_URL")
    }

    validate_urls(urls)

    # Validate CalDAV URL specifically
    validate_caldav_url(os.getenv("CALDAV_URL"))



