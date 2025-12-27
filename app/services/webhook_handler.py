# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-27T14:00:23
# Last Updated: 2025-12-27T18:43:43
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Webhook handler for Plane updates"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

from app.config import settings
from app.models.plane import PlaneWebhookPayload
from app.services.sync_service import sync_service


logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handler for Plane webhooks"""

    def __init__(self):
        self.secret = settings.plane_webhook_secret

    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature from Plane"""
        if not self.secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True

        try:
            # Plane uses HMAC-SHA256
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    async def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming webhook from Plane"""
        try:
            # Convert payload to string for signature verification
            payload_str = json.dumps(payload, separators=(',', ':'))

            # Verify signature if secret is configured
            if signature and not self.verify_signature(payload_str, signature):
                logger.warning("Webhook signature verification failed")
                return {"status": "error", "message": "Invalid signature"}

            # Parse webhook payload
            webhook_data = PlaneWebhookPayload(**payload)

            # Process based on event type
            if webhook_data.event == "issue":
                await self._process_issue_webhook(webhook_data)
            else:
                logger.info(f"Unhandled webhook event type: {webhook_data.event}")

            logger.info(f"Successfully processed webhook: {webhook_data.action} {webhook_data.event}")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def _process_issue_webhook(self, webhook: PlaneWebhookPayload) -> None:
        """Process issue-related webhook"""
        issue = webhook.data
        action = webhook.action

        logger.info(f"Processing issue webhook: {action} for issue {issue.sequence_id}")

        try:
            # Get calendar for project
            calendar_url = sync_service.get_calendar_for_project(issue.project_id)

            if not calendar_url:
                logger.warning(f"No calendar mapping for project {issue.project_id}")
                return

            if action in ["create", "update"]:
                # Sync issue to calendar
                await sync_service.sync_issue_to_calendar(issue, calendar_url)

            elif action == "delete":
                # Remove event from calendar
                event_uid = f"plane-issue-{issue.id}@{settings.app_name.lower()}"
                try:
                    await sync_service.caldav_service.delete_event(calendar_url, event_uid)
                    logger.info(f"Deleted event for issue {issue.sequence_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete event for issue {issue.sequence_id}: {e}")

            else:
                logger.info(f"Unhandled issue action: {action}")

        except Exception as e:
            logger.error(f"Failed to process issue webhook: {e}")
            raise

    async def handle_plane_webhook(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle webhook request from Plane"""
        # Extract signature from headers
        signature = headers.get("X-Plane-Signature")

        # Process webhook
        return await self.process_webhook(payload, signature)


# Global instance
webhook_handler = WebhookHandler()



