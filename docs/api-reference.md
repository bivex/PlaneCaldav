# CalPlaneBot API Reference

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** Developers, integrators
**Purpose:** Technical API documentation for CalPlaneBot

## Overview

CalPlaneBot provides REST API endpoints for service management, monitoring, and integration. The API is built with FastAPI and includes automatic OpenAPI documentation.

## Base URL

```
http://localhost:8765
```

## Authentication

Currently, the API does not require authentication for basic operations. For production deployments, consider implementing authentication middleware.

## Core Endpoints

### Service Information

#### GET /

Returns basic service information.

**Response:**
```json
{
  "name": "CalPlaneBot",
  "version": "1.0.0",
  "description": "Plane ↔ CalDAV Integration Service",
  "status": "running",
  "uptime": "2h 15m 30s"
}
```

### Health Checks

#### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-27T10:30:00Z"
}
```

#### GET /api/v1/health

Detailed health check with metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-27T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2h 15m 30s",
  "metrics": {
    "projects_synced": 5,
    "events_created": 127,
    "events_updated": 23,
    "events_deleted": 3,
    "last_sync": "2025-12-27T10:25:00Z",
    "sync_status": "idle",
    "caldav_connection": "healthy",
    "plane_api_connection": "healthy"
  }
}
```

## Webhook Endpoints

### Plane Webhooks

#### POST /webhooks/plane

Receives webhooks from Plane when issues are created, updated, or deleted.

**Headers:**
```
Content-Type: application/json
X-Plane-Signature: sha256=... (optional, if webhook secret configured)
```

**Request Body:**
```json
{
  "action": "created|updated|deleted",
  "data": {
    "id": "issue-uuid",
    "name": "Issue title",
    "description": "Issue description",
    "state": {
      "name": "Backlog|Todo|In Progress|Done|Cancelled",
      "group": "backlog|unstarted|started|completed|cancelled"
    },
    "target_date": "2025-12-27",
    "start_date": null,
    "sequence_id": 42,
    "priority": "urgent|high|medium|low|none",
    "assignees": [
      {
        "id": "user-uuid",
        "display_name": "User Name",
        "avatar": "https://..."
      }
    ],
    "labels": [
      {
        "id": "label-uuid",
        "name": "bug",
        "color": "#ff0000"
      }
    ],
    "project": {
      "id": "project-uuid",
      "name": "My Project",
      "identifier": "MP"
    }
  },
  "actor": {
    "id": "user-uuid",
    "display_name": "Actor Name"
  },
  "created_at": "2025-12-27T10:30:00Z",
  "workspace": {
    "id": "workspace-uuid",
    "slug": "my-workspace"
  }
}
```

**Response:**
```json
{
  "status": "processed",
  "message": "Issue sync triggered",
  "issue_id": "issue-uuid",
  "action": "created"
}
```

**Error Responses:**
```json
{
  "status": "error",
  "message": "Invalid webhook signature",
  "error_code": "INVALID_SIGNATURE"
}
```

### Synchronization Triggers

#### POST /webhooks/sync

Triggers manual synchronization between Plane and CalDAV.

**Request Body:** None required (empty body)

**Response:**
```json
{
  "status": "triggered",
  "message": "Manual sync initiated",
  "sync_id": "sync-uuid",
  "timestamp": "2025-12-27T10:30:00Z"
}
```

#### GET /webhooks/status

Returns current synchronization status.

**Response:**
```json
{
  "status": "idle|running|error",
  "last_sync": {
    "timestamp": "2025-12-27T10:25:00Z",
    "duration_seconds": 2.34,
    "status": "success|partial|failed",
    "events_processed": 15,
    "errors": []
  },
  "next_sync": "2025-12-27T10:35:00Z",
  "queue_length": 0
}
```

## Data Models

### Issue Data Structure

```typescript
interface PlaneIssue {
  id: string;
  name: string;
  description?: string;
  state: {
    name: string;
    group: 'backlog' | 'unstarted' | 'started' | 'completed' | 'cancelled';
  };
  target_date?: string; // ISO date string (YYYY-MM-DD)
  start_date?: string;  // ISO date string (YYYY-MM-DD)
  sequence_id: number;
  priority: 'urgent' | 'high' | 'medium' | 'low' | 'none';
  assignees: Array<{
    id: string;
    display_name: string;
    avatar?: string;
  }>;
  labels: Array<{
    id: string;
    name: string;
    color: string;
  }>;
  project: {
    id: string;
    name: string;
    identifier: string;
  };
}
```

### Calendar Event Structure

```typescript
interface CalendarEvent {
  uid: string;           // Format: plane-issue-{issue.id}@calplanebot
  summary: string;       // Format: [{sequence_id}] {issue.name}
  description: string;   // Includes assignees, priority, state, URL
  start: Date;           // All-day event (VALUE=DATE)
  end: Date;             // All-day event (start + 1 day)
  status: 'CONFIRMED' | 'CANCELLED';
  categories: string[];  // Issue labels
  url: string;           // Direct link to Plane issue
  color?: string;        // Priority-based color (if supported)
}
```

## Synchronization Logic

### Sync Rules

1. **Issue Selection**: Only issues with `target_date` are synchronized
2. **Event Creation**: Issues become all-day calendar events
3. **Event Updates**: Existing events are updated, not recreated
4. **Event Deletion**: Events are deleted when `target_date` is removed
5. **Status Mapping**:
   - Active issues → `STATUS:CONFIRMED`
   - Completed/Cancelled issues → `STATUS:CANCELLED`

### Data Mapping

| Plane Field | CalDAV Field | Notes |
|-------------|--------------|-------|
| `id` | `UID` | `plane-issue-{id}@calplanebot` |
| `name` | `SUMMARY` | Prefixed with `[{sequence_id}]` |
| `description` | `DESCRIPTION` | Includes metadata |
| `target_date` | `DTSTART/DTEND` | All-day format (VALUE=DATE) |
| `state.group` | `STATUS` | CONFIRMED/CANCELLED |
| `labels[].name` | `CATEGORIES` | Array of label names |
| `priority` | `COLOR` | urgent=red, high=orange, etc. |
| Issue URL | `URL` | Direct link to Plane |

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful operation
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "specific_field_name",
    "reason": "validation_reason"
  },
  "timestamp": "2025-12-27T10:30:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_SIGNATURE` | Webhook signature verification failed |
| `MISSING_REQUIRED_FIELD` | Required field missing in request |
| `INVALID_DATE_FORMAT` | Date field has invalid format |
| `CALDAV_CONNECTION_ERROR` | Cannot connect to CalDAV server |
| `PLANE_API_ERROR` | Plane API request failed |
| `SYNC_IN_PROGRESS` | Another sync operation is running |

## Rate Limiting

- Webhook endpoints: 100 requests per minute per IP
- Health endpoints: Unlimited
- Sync trigger: 10 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
```

## Webhook Security

### Signature Verification

If `PLANE_WEBHOOK_SECRET` is configured, webhooks include HMAC-SHA256 signatures:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Best Practices

1. **Validate Signatures**: Always verify webhook signatures
2. **Use HTTPS**: Ensure webhook endpoints use HTTPS
3. **IP Whitelisting**: Restrict webhook sources to known IPs
4. **Secret Rotation**: Regularly rotate webhook secrets

## Integration Examples

### Python Integration

```python
import requests

# Health check
response = requests.get("http://localhost:8765/health")
print(response.json())

# Trigger sync
response = requests.post("http://localhost:8765/webhooks/sync")
print(response.json())

# Check sync status
response = requests.get("http://localhost:8765/webhooks/status")
print(response.json())
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');

async function checkHealth() {
  try {
    const response = await axios.get('http://localhost:8765/health');
    console.log('Service healthy:', response.data);
  } catch (error) {
    console.error('Health check failed:', error.message);
  }
}

async function triggerSync() {
  try {
    const response = await axios.post('http://localhost:8765/webhooks/sync');
    console.log('Sync triggered:', response.data);
  } catch (error) {
    console.error('Sync trigger failed:', error.message);
  }
}
```

### Shell Script Integration

```bash
#!/bin/bash

# Health check
curl -s http://localhost:8765/health | jq .

# Trigger sync
curl -X POST http://localhost:8765/webhooks/sync

# Check sync status
curl -s http://localhost:8765/webhooks/status | jq .status
```

### Webhook Handler Example

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

def verify_signature(payload, signature):
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.route('/webhook/plane', methods=['POST'])
def handle_plane_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Plane-Signature')

    if WEBHOOK_SECRET and not verify_signature(payload, signature):
        return jsonify({"error": "Invalid signature"}), 401

    data = request.get_json()

    # Forward to CalPlaneBot
    import requests
    response = requests.post('http://localhost:8765/webhooks/plane',
                           json=data,
                           headers={'Content-Type': 'application/json'})

    return jsonify({"status": "forwarded", "response": response.json()})
```

## Monitoring and Metrics

### Available Metrics

- **Service Health**: Overall system status
- **Sync Statistics**: Events processed, success/failure rates
- **Performance**: Response times, throughput
- **Errors**: Error counts by type and endpoint

### Metrics Endpoint

```bash
curl http://localhost:8765/api/v1/health
```

### Log Integration

All API operations are logged with structured data:

```
INFO 2025-12-27 10:30:00 - Webhook received: action=created, issue_id=issue-123
INFO 2025-12-27 10:30:01 - Sync started: 15 issues to process
INFO 2025-12-27 10:30:03 - Sync completed: 15 created, 0 updated, 0 deleted
ERROR 2025-12-27 10:30:04 - CalDAV connection failed: timeout
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLANE_WEBHOOK_SECRET` | Secret for webhook signature verification | None |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `SYNC_INTERVAL_SECONDS` | Automatic sync interval | 300 |

### Runtime Configuration

The API automatically reloads configuration changes without restart for most settings.

## Development

### OpenAPI Documentation

Interactive API documentation is available at:
```
http://localhost:8765/docs
```

### Testing

```bash
# Run API tests
pytest tests/test_api.py -v

# Test with curl
curl -X POST http://localhost:8765/webhooks/sync \
  -H "Content-Type: application/json"

# Load testing
ab -n 1000 -c 10 http://localhost:8765/health
```

### Local Development

```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765

# View logs
tail -f logs/calplanebot.log

# Debug mode
export LOG_LEVEL=DEBUG
```

## Security Considerations

1. **Input Validation**: All inputs are validated using Pydantic models
2. **Rate Limiting**: Implemented to prevent abuse
3. **Error Handling**: Sensitive information not exposed in errors
4. **HTTPS**: Recommended for production deployments
5. **Webhook Security**: Optional signature verification

## Support

- **API Documentation**: Visit `/docs` endpoint when service is running
- **GitHub Issues**: Report API bugs and request features
- **Community**: Check existing issues for similar problems

