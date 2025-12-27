# Data Flow and Synchronization Architecture

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** Developers, system architects
**Purpose:** Detailed data flow diagrams and synchronization logic

## Core Synchronization Principles

### 1. Single Source of Truth
**Plane is the authoritative source.** All changes originate in Plane and are mirrored to CalDAV calendars.

### 2. Event-Driven Architecture
Synchronization is triggered by:
- **Webhooks**: Real-time updates from Plane
- **Scheduled Sync**: Periodic full synchronization (default: 5 minutes)
- **Manual Triggers**: API calls for immediate sync

### 3. Idempotent Operations
All sync operations are designed to be safe to run multiple times without side effects.

## Data Flow Diagrams

### High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Plane    │────►│ CalPlaneBot │────►│   CalDAV    │
│             │     │             │     │             │
│ • API       │     │ • Webhook   │     │ • Calendar  │
│ • Webhooks  │     │ • Sync      │     │ • Events    │
│ • Issues    │     │ • Transform │     │ • Alarms    │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   ▲                   │
       │                   │                   ▼
       └───────────────────┼───────────────────┘
                       No feedback loop
```

### Webhook Processing Flow

```
1. Issue Changed in Plane
        │
        ▼
2. Plane sends HTTP POST to /webhooks/plane
        │
        ▼
3. Webhook Handler
   ├── Verify HMAC signature (if configured)
   ├── Validate payload structure
   ├── Extract issue data
   └── Queue for processing
        │
        ▼
4. Sync Service
   ├── Fetch full issue details from Plane API
   ├── Transform to calendar event format
   ├── Check existing event in CalDAV
   └── Create/update/delete event
        │
        ▼
5. CalDAV Service
   ├── Connect to CalDAV server
   ├── Execute calendar operation
   ├── Handle retries on failure
   └── Log operation result
        │
        ▼
6. Calendar Client Updates
   └── Users see changes in calendar applications
```

### Periodic Synchronization Flow

```
Scheduler (every 5 minutes)
        │
        ▼
1. Fetch all accessible projects from Plane
        │
        ▼
2. For each project:
   ├── Get project details
   ├── Fetch issues with target_dates
   ├── Transform to event format
   └── Compare with existing calendar events
        │
        ▼
3. Synchronization Decisions:
   ├── New issues → Create events
   ├── Changed issues → Update events
   ├── Completed issues → Update status
   ├── Deleted issues → Delete events
   └── Issues without dates → Skip
        │
        ▼
4. Batch CalDAV operations
   ├── Group by calendar
   ├── Execute in transaction-like manner
   └── Handle partial failures
        │
        ▼
5. Update sync status and metrics
   └── Log completion with statistics
```

## Data Transformation Pipeline

### Input Processing

#### Plane Issue Data Structure

```json
{
  "id": "issue-uuid",
  "name": "Implement user authentication",
  "description": "Add login and registration functionality",
  "state": {
    "name": "In Progress",
    "group": "started"
  },
  "target_date": "2025-12-27",
  "start_date": null,
  "sequence_id": 42,
  "priority": "high",
  "assignees": [
    {
      "id": "user-uuid",
      "display_name": "John Doe",
      "avatar": "https://example.com/avatar.jpg"
    }
  ],
  "labels": [
    {
      "id": "label-uuid",
      "name": "backend",
      "color": "#ff0000"
    },
    {
      "id": "label-uuid-2",
      "name": "security",
      "color": "#00ff00"
    }
  ],
  "project": {
    "id": "project-uuid",
    "name": "Web Application",
    "identifier": "WA"
  }
}
```

### Transformation Rules

#### 1. Issue Filtering
```python
# Only issues with target dates are synchronized
if issue.get('target_date') is None:
    return None  # Skip this issue
```

#### 2. UID Generation
```python
# Stable, unique identifier for calendar events
uid = f"plane-issue-{issue['id']}@calplanebot"
```

#### 3. Summary Generation
```python
# Format: [{sequence_id}] {issue_name}
summary = f"[{issue['sequence_id']}] {issue['name']}"
```

#### 4. Description Enhancement
```python
description_parts = []

# Original description
if issue.get('description'):
    description_parts.append(issue['description'])

# Add metadata
description_parts.append(f"\n---")
description_parts.append(f"Priority: {issue.get('priority', 'none')}")
description_parts.append(f"State: {issue['state']['name']}")

# Assignees
if issue.get('assignees'):
    assignees = [a['display_name'] for a in issue['assignees']]
    description_parts.append(f"Assignees: {', '.join(assignees)}")

# Labels
if issue.get('labels'):
    labels = [l['name'] for l in issue['labels']]
    description_parts.append(f"Labels: {', '.join(labels)}")

# Project info
description_parts.append(f"Project: {issue['project']['name']}")

description = "\n".join(description_parts)
```

#### 5. Status Mapping
```python
# Map Plane states to CalDAV statuses
state_group = issue['state']['group']

if state_group in ['completed', 'cancelled']:
    status = 'CANCELLED'  # Strikethrough in calendars
else:
    status = 'CONFIRMED'  # Normal display
```

#### 6. Priority Color Mapping
```python
priority_colors = {
    'urgent': '#dc3545',  # Red
    'high': '#fd7e14',    # Orange
    'medium': '#ffc107',  # Yellow
    'low': '#28a745',     # Green
    'none': None
}

color = priority_colors.get(issue.get('priority'), None)
```

#### 7. All-Day Event Creation
```python
from datetime import datetime, timedelta
import icalendar

# Parse target date
target_date = datetime.fromisoformat(issue['target_date']).date()

# Create all-day event (DTEND = DTSTART + 1 day per RFC 5545)
event = icalendar.Event()
event.add('dtstart', target_date, parameters={'VALUE': 'DATE'})
event.add('dtend', target_date + timedelta(days=1), parameters={'VALUE': 'DATE'})
```

### Output Structure

#### CalDAV Event Format

```ical
BEGIN:VEVENT
UID:plane-issue-issue-uuid@calplanebot
SUMMARY:[42] Implement user authentication
DESCRIPTION:Add login and registration functionality\n---\nPriority: high\nState: In Progress\nAssignees: John Doe\nLabels: backend, security\nProject: Web Application
DTSTART;VALUE=DATE:20251227
DTEND;VALUE=DATE:20251228
STATUS:CONFIRMED
CATEGORIES:backend,security
URL:https://plane.so/project/project-uuid/issues/issue-uuid
COLOR:#fd7e14
END:VEVENT
```

## Synchronization Strategies

### Conflict Resolution

#### Last-Write-Wins
- Webhook events always take precedence over scheduled sync
- Scheduled sync resolves any missed updates
- No merge conflicts possible due to one-way sync

#### Event Updates vs Recreates
- **Update Preferred**: Preserves calendar client state (alarms, custom notes)
- **Recreate Only When Necessary**: UID changes or major structural changes
- **Delete Strategy**: Clean removal when issues lose target dates

### Error Handling

#### Transient Failures
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, HTTPError))
)
def sync_event_with_retry(event_data):
    return caldav_service.sync_event(event_data)
```

#### Permanent Failures
- Invalid data → Log and skip
- Permission denied → Alert administrator
- Calendar full → Queue for retry

#### Partial Sync Handling
- Track successful/failed operations per batch
- Allow partial success (some events sync, others fail)
- Report detailed status for troubleshooting

## Performance Optimization

### Batching Strategies

#### Calendar-Level Batching
```python
# Group events by calendar for efficient CalDAV operations
events_by_calendar = defaultdict(list)

for event in events_to_sync:
    calendar_name = f"Plane: {event['project_name']}"
    events_by_calendar[calendar_name].append(event)

# Process each calendar as a batch
for calendar_name, calendar_events in events_by_calendar.items():
    caldav_service.sync_calendar_events(calendar_name, calendar_events)
```

#### API Request Optimization
- Use pagination for large project lists
- Implement connection pooling for CalDAV requests
- Cache calendar discovery results (1-hour TTL)

### Caching Strategy

#### Calendar Discovery Cache
```python
@dataclass
class CalendarCache:
    calendars: Dict[str, str]  # name -> URL mapping
    last_updated: datetime
    ttl_seconds: int = 3600  # 1 hour

    def is_expired(self) -> bool:
        return (datetime.now() - self.last_updated).seconds > self.ttl_seconds
```

#### Project Metadata Cache
- Store project names and identifiers
- Reduce API calls for repeated syncs
- Invalidate on webhook notifications

## Monitoring and Metrics

### Sync Metrics

#### Operation Counts
- Events created, updated, deleted per sync cycle
- Success/failure rates by operation type
- Average processing time per event

#### Performance Metrics
- API response times for Plane and CalDAV
- Memory usage during large sync operations
- Network I/O for data transfer

#### Error Metrics
- Failure rates by error type
- Retry counts and success rates
- Calendar-specific error patterns

### Health Monitoring

#### Dependency Checks
```python
async def health_check():
    return {
        "plane_api": await check_plane_connectivity(),
        "caldav_server": await check_caldav_connectivity(),
        "last_sync": get_last_sync_timestamp(),
        "sync_status": get_current_sync_status(),
        "queue_depth": get_queued_operations_count()
    }
```

#### Alert Conditions
- Sync failures > 3 consecutive times
- Queue depth > 1000 pending operations
- API response time > 30 seconds
- Memory usage > 80%

## Data Integrity

### Consistency Checks

#### UID Stability
- UIDs must remain constant for the same issue
- Format validation: `plane-issue-{uuid}@calplanebot`
- Collision detection and prevention

#### Event Completeness
- All required iCalendar fields present
- Valid date formats and ranges
- Proper encoding for special characters

### Audit Trail

#### Operation Logging
```python
logger.info("Event synchronized", extra={
    "operation": "create|update|delete",
    "issue_id": issue_id,
    "event_uid": event_uid,
    "calendar_name": calendar_name,
    "processing_time_ms": processing_time,
    "success": True
})
```

#### Change Tracking
- Before/after state comparison
- Field-level change detection
- Historical sync operation log

## Scalability Considerations

### Horizontal Scaling

#### Service Instances
- Stateless design allows multiple instances
- Load balancer distributes webhook requests
- Shared queue for coordination (future enhancement)

#### Database Partitioning
- Partition by project for large deployments
- Time-based partitioning for historical data
- Archive old sync logs regularly

### Resource Management

#### Memory Optimization
- Stream processing for large issue lists
- Garbage collection tuning
- Memory pool reuse for frequent operations

#### Network Optimization
- Connection pooling for CalDAV servers
- Request compression for large payloads
- CDN integration for static assets (future)

## Future Enhancements

### Advanced Features
- **Bi-directional sync** (with conflict resolution)
- **Custom field mapping** (configurable transformations)
- **Calendar templates** (custom event formats)
- **Bulk operations** (mass update/delete)
- **Event relationships** (dependencies, blockers)

### Performance Improvements
- **Database integration** for metadata storage
- **Message queuing** for high-throughput scenarios
- **CDN caching** for calendar data
- **Edge computing** for global deployments

### Monitoring Enhancements
- **Distributed tracing** across services
- **Predictive analytics** for issue detection
- **Automated remediation** for common issues
- **Custom dashboards** for stakeholders

