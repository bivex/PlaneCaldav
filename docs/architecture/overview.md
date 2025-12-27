# CalPlaneBot Architecture Overview

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** Developers, architects, system administrators
**Purpose:** System design, data flow, and technical architecture documentation

## System Overview

CalPlaneBot is a microservice that synchronizes project management tasks from Plane with CalDAV-compatible calendar systems. It operates as a webhook-driven integration service with periodic full synchronization capabilities.

## Core Principles

### 1. Single Source of Truth
**Plane is the master system.** CalDAV calendars serve as read-only mirrors. Changes made in calendar clients are ignored to prevent data conflicts.

### 2. Event Creation Rule
**No `target_date` = No calendar event.** Only Plane issues with due dates are synchronized to calendars.

### 3. One-Way Synchronization
Data flows only from Plane → CalDAV. Calendar changes do not sync back to Plane.

### 4. Stable Event Identity
Each Plane issue maintains a consistent calendar event UID across updates.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Plane       │    │  CalPlaneBot    │    │    CalDAV       │
│   (Source)      │◄──►│   (Service)     │◄──►│   (Target)      │
│                 │    │                 │    │                 │
│ • Issues        │    │ • Webhook       │    │ • Calendars     │
│ • Projects      │    │   Handler       │    │ • Events        │
│ • Workspaces    │    │ • Sync Engine   │    │ • Alarms        │
│ • Users         │    │ • API Service   │    │ • Categories    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                           ▲
                           │
                    ┌─────────────────┐
                    │  Management     │
                    │  Interface      │
                    │                 │
                    │ • CLI Tools     │
                    │ • Health Checks │
                    │ • Diagnostics   │
                    └─────────────────┘
```

## Component Architecture

### Application Structure

```
CalPlaneBot/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── models/                # Data models and schemas
│   │   ├── plane.py          # Plane API data structures
│   │   └── caldav.py         # CalDAV data structures
│   ├── services/             # Business logic layer
│   │   ├── plane_service.py  # Plane API client
│   │   ├── caldav_service.py # CalDAV client
│   │   ├── sync_service.py   # Synchronization engine
│   │   └── webhook_handler.py # Webhook processing
│   ├── routers/              # API route handlers
│   │   └── webhooks.py       # Webhook endpoints
│   └── utils/                # Utility functions
├── config/
│   └── validation.py         # Configuration validation
├── tests/                    # Test suites
├── docs/                     # Documentation
└── scripts/                  # Deployment scripts
```

### Key Components

#### 1. FastAPI Application (`main.py`)
- **Purpose**: Main application entry point and server
- **Responsibilities**:
  - HTTP server management
  - Route registration
  - Middleware configuration
  - Background task scheduling
- **Key Features**:
  - Async request handling
  - Automatic OpenAPI documentation
  - CORS support
  - Health check endpoints

#### 2. Configuration System (`config.py`)
- **Purpose**: Centralized configuration management
- **Responsibilities**:
  - Environment variable loading
  - Configuration validation
  - Default value management
- **Key Features**:
  - Pydantic-based validation
  - Type safety
  - Environment-specific overrides

#### 3. Data Models (`models/`)
- **Purpose**: Type-safe data structures
- **Responsibilities**:
  - API request/response schemas
  - Data validation
  - Serialization/deserialization
- **Key Features**:
  - Pydantic models
  - Automatic validation
  - JSON schema generation

#### 4. Service Layer (`services/`)

##### Plane Service (`plane_service.py`)
- **Purpose**: Plane API client and data retrieval
- **Responsibilities**:
  - Authentication with Plane API
  - Issue data fetching
  - Project information retrieval
  - Rate limiting and error handling
- **Key Methods**:
  - `get_issues(project_id)`: Fetch issues for a project
  - `get_projects()`: Get all accessible projects
  - `validate_token()`: Verify API token validity

##### CalDAV Service (`caldav_service.py`)
- **Purpose**: CalDAV protocol client
- **Responsibilities**:
  - Calendar discovery and management
  - Event creation, update, deletion
  - Connection pooling and retry logic
- **Key Methods**:
  - `create_calendar(name)`: Create new calendar
  - `sync_event(event_data)`: Create/update calendar event
  - `delete_event(uid)`: Remove event from calendar

##### Sync Service (`sync_service.py`)
- **Purpose**: Core synchronization logic
- **Responsibilities**:
  - Data transformation between systems
  - Sync decision making
  - Conflict resolution
  - Progress tracking
- **Key Methods**:
  - `sync_project(project_id)`: Sync single project
  - `sync_all_projects()`: Full system synchronization
  - `process_webhook(payload)`: Handle real-time updates

##### Webhook Handler (`webhook_handler.py`)
- **Purpose**: Plane webhook processing
- **Responsibilities**:
  - Webhook signature verification
  - Payload validation
  - Event queuing and processing
- **Key Methods**:
  - `verify_signature(payload, signature)`: HMAC verification
  - `process_issue_event(event)`: Handle issue changes

#### 5. API Routes (`routers/`)
- **Purpose**: HTTP endpoint definitions
- **Responsibilities**:
  - Request routing
  - Input validation
  - Response formatting
  - Error handling

## Data Flow Architecture

### Webhook-Driven Sync Flow

```
1. Issue Updated in Plane
        │
        ▼
2. Plane sends webhook to CalPlaneBot
        │
        ▼
3. Webhook Handler validates signature
        │
        ▼
4. Issue data queued for processing
        │
        ▼
5. Sync Service transforms data
        │
        ▼
6. CalDAV Service creates/updates event
        │
        ▼
7. Calendar clients refresh and show changes
```

### Periodic Full Sync Flow

```
1. Scheduler triggers sync (every 5 minutes)
        │
        ▼
2. Sync Service fetches all projects from Plane
        │
        ▼
3. For each project:
        │
        ▼
4.   Fetch issues with target_dates
        │
        ▼
5.   Compare with existing calendar events
        │
        ▼
6.   Create/update/delete events as needed
        │
        ▼
7. Sync status updated and logged
```

## Data Transformation Rules

### Issue to Event Mapping

| Plane Issue Field | CalDAV Event Field | Transformation Rules |
|-------------------|-------------------|----------------------|
| `id` | `UID` | `plane-issue-{id}@calplanebot` |
| `name` | `SUMMARY` | `[{sequence_id}] {name}` |
| `description` | `DESCRIPTION` | Full description + metadata |
| `target_date` | `DTSTART/DTEND` | All-day event (VALUE=DATE) |
| `state.group` | `STATUS` | `completed/cancelled` → CANCELLED<br>`other` → CONFIRMED |
| `priority` | `COLOR` | `urgent` → red<br>`high` → orange<br>`medium` → yellow<br>`low` → green |
| `labels` | `CATEGORIES` | Array of label names |
| Issue URL | `URL` | Direct link to Plane issue |

### Event Identity Management

- **UID Format**: `plane-issue-{issue.id}@calplanebot`
- **Stability**: UID never changes for the same issue
- **Collision Prevention**: Includes issue ID to ensure uniqueness
- **Update Strategy**: In-place updates preserve client-side modifications

## Synchronization Strategies

### 1. Webhook-Based Real-Time Sync
- **Trigger**: Plane webhooks for issue changes
- **Advantages**: Instant updates, low latency
- **Limitations**: Requires webhook configuration, potential delivery failures

### 2. Periodic Full Synchronization
- **Trigger**: Scheduled every 5 minutes (configurable)
- **Advantages**: Catches missed updates, comprehensive sync
- **Limitations**: Higher resource usage, potential duplicates

### 3. Hybrid Approach
- **Implementation**: Both webhook and periodic sync enabled
- **Benefits**: Real-time updates with periodic consistency checks
- **Conflict Resolution**: Webhook events take precedence

## Error Handling and Resilience

### Retry Mechanisms

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
def sync_with_caldav(event_data):
    # Synchronization logic with automatic retries
    pass
```

### Circuit Breaker Pattern

- **Purpose**: Prevent cascading failures
- **Implementation**: Track CalDAV/Plane API failures
- **Behavior**: Temporarily disable sync on repeated failures

### Dead Letter Queue

- **Purpose**: Handle persistently failing items
- **Implementation**: Failed sync items stored for manual review
- **Recovery**: Manual retry or skip options

## Performance Characteristics

### Scalability Metrics

| Component | Current Limits | Scaling Strategy |
|-----------|----------------|------------------|
| Projects | 100+ | Horizontal partitioning |
| Issues per Project | 10,000+ | Pagination + batching |
| Concurrent Syncs | 1 | Queue-based processing |
| Webhook Throughput | 100/min | Rate limiting + queuing |

### Resource Usage

- **Memory**: ~50MB base + 10MB per active sync
- **CPU**: Minimal (<5%) during idle, spikes during sync
- **Network**: ~1KB per issue for API calls
- **Storage**: ~100KB for logs + temporary files

### Performance Optimizations

1. **Connection Pooling**: Reuse HTTP connections
2. **Caching**: Calendar discovery results (1-hour TTL)
3. **Batching**: Group multiple operations
4. **Async Processing**: Non-blocking I/O operations

## Security Architecture

### Authentication Methods

#### Plane API Authentication
- **Method**: Bearer token via X-API-Key header
- **Storage**: Environment variable (not logged)
- **Validation**: Token format and permissions check

#### CalDAV Authentication
- **Methods**: Digest (preferred) or Basic authentication
- **Storage**: Environment variables
- **Transmission**: HTTPS only

#### Webhook Security
- **Optional**: HMAC-SHA256 signature verification
- **Configuration**: `PLANE_WEBHOOK_SECRET` environment variable
- **Validation**: Payload integrity checking

### Data Protection

- **In Transit**: HTTPS/TLS 1.2+ for all external communications
- **At Rest**: Sensitive data encrypted in configuration
- **Logging**: Credentials masked in logs
- **Access Control**: No authentication required for basic operations

## Deployment Architecture

### Containerized Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  calplanebot:
    image: calplanebot:latest
    environment:
      - PLANE_BASE_URL=${PLANE_BASE_URL}
      - PLANE_API_TOKEN=${PLANE_API_TOKEN}
      # ... other env vars
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "8765:8765"
    restart: unless-stopped
```

### Environment Configuration

#### Development
- Local Python environment
- Debug logging enabled
- Auto-reload on code changes
- Test database/calendars

#### Production
- Docker container deployment
- Structured logging
- Health monitoring
- SSL termination

### High Availability Considerations

1. **Stateless Design**: No local state persistence
2. **External Dependencies**: Plane and CalDAV availability
3. **Graceful Degradation**: Continue operation despite partial failures
4. **Monitoring Integration**: Health checks and metrics

## Monitoring and Observability

### Health Checks

- **Application**: `/health` - Basic service availability
- **Detailed**: `/api/v1/health` - Comprehensive system status
- **Dependencies**: CalDAV and Plane API connectivity

### Logging Strategy

```python
# Structured logging with context
logger.info("Sync completed", extra={
    "project_id": project_id,
    "events_created": created_count,
    "events_updated": updated_count,
    "duration_seconds": duration
})
```

### Metrics Collection

- **Sync Operations**: Success/failure rates, duration
- **API Calls**: Request counts, error rates, latency
- **Resource Usage**: Memory, CPU, network I/O
- **Queue Status**: Pending operations, processing rates

## Testing Strategy

### Unit Testing
- **Coverage**: Core business logic, data transformation
- **Tools**: pytest, coverage.py
- **Mocking**: External API calls and services

### Integration Testing
- **Scope**: End-to-end synchronization workflows
- **Environment**: Test instances of Plane and CalDAV
- **Data**: Realistic test datasets with edge cases

### Edge Case Testing
- **Datetime Handling**: Leap years, DST transitions, timezone conversions
- **Unicode Support**: International characters, emojis, special symbols
- **Large Datasets**: 1000+ issues, 100+ projects
- **Network Conditions**: Timeouts, connection failures, rate limits

## Extensibility

### Plugin Architecture

- **Service Interface**: Abstract base classes for sync services
- **Event Hooks**: Pre/post sync operation callbacks
- **Custom Mappings**: Configurable field transformation rules

### API Extensions

- **Additional Endpoints**: Custom integration APIs
- **Webhook Types**: Support for different event sources
- **Output Formats**: Multiple calendar formats (iCal, CalDAV, etc.)

## Migration and Upgrade

### Version Compatibility

- **API Stability**: REST API maintains backward compatibility
- **Configuration**: Environment variables are additive
- **Data Migration**: Automatic handling of schema changes

### Upgrade Process

1. **Backup**: Configuration and logs
2. **Update**: Container image or code
3. **Migrate**: Run migration scripts if needed
4. **Validate**: Health checks and test sync
5. **Rollback**: Previous version available if issues

## Conclusion

CalPlaneBot implements a robust, scalable architecture for Plane-CalDAV integration with strong emphasis on reliability, maintainability, and extensibility. The modular design allows for easy testing, deployment, and future enhancements while maintaining clear separation of concerns and comprehensive error handling.

