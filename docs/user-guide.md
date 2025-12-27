# CalPlaneBot User Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** End users, system administrators

## Overview

CalPlaneBot is a service that integrates Plane project management tasks with CalDAV-compatible calendars. It automatically synchronizes tasks from [Plane](https://plane.so) with calendars supporting the CalDAV protocol (such as Baïkal, Nextcloud, Radicale).

## Key Features

- 🔄 **Automatic Synchronization**: Real-time task synchronization from Plane to CalDAV calendars
- 🔔 **Webhook Integration**: Instant updates via Plane webhooks
- 📅 **Calendar Management**: Automatic calendar creation for each Plane project
- 🏷️ **Rich Metadata**: Support for labels, priorities, and assignees
- ⏰ **Flexible Scheduling**: Configurable synchronization intervals
- 🐳 **Docker Support**: Easy deployment with containerization

## Prerequisites

- Access to a Plane instance
- CalDAV-compatible calendar server (Baïkal, Nextcloud, Radicale, etc.)
- Docker and Docker Compose (for containerized deployment)
- Python 3.11+ (for manual installation)

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CalPlaneBot
```

### 2. Configure Environment Variables

```bash
cp env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Plane Configuration
PLANE_BASE_URL=https://your-plane-instance.plane.so
PLANE_API_TOKEN=your_api_token_here
PLANE_WORKSPACE_SLUG=default

# CalDAV Configuration
CALDAV_URL=https://your-caldav-server.com/caldav
CALDAV_USERNAME=your_username
CALDAV_PASSWORD=your_password
CALDAV_AUTH_TYPE=digest  # "digest" (recommended) or "basic"
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

The service will be available at `http://localhost:8765`

## Manual Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp env.example .env
# Edit .env file with your configuration
```

### 3. Start the Application

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PLANE_BASE_URL` | URL of your Plane instance | `https://mycompany.plane.so` |
| `PLANE_API_TOKEN` | Plane API token | `plane_xxxxxxxxxxxxxxxx` |
| `PLANE_WORKSPACE_SLUG` | Workspace slug | `default` |
| `CALDAV_URL` | CalDAV server URL | `https://baikal.mycompany.com/caldav` |
| `CALDAV_USERNAME` | CalDAV username | `username` |
| `CALDAV_PASSWORD` | CalDAV password | `password` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLANE_WEBHOOK_SECRET` | Webhook secret | - |
| `SYNC_INTERVAL_SECONDS` | Sync interval in seconds | `300` |
| `ENABLE_SYNC` | Enable automatic synchronization | `true` |
| `EVENT_DEFAULT_DURATION_HOURS` | Default event duration | `1` |
| `EVENT_TIMEZONE` | Event timezone | `Europe/Moscow` |
| `LOG_LEVEL` | Logging level | `INFO` |

## API Endpoints

The service provides the following endpoints when running:

### Core Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /api/v1/health` - Detailed health check

### Webhook Endpoints

- `POST /webhooks/plane` - Receive webhooks from Plane
- `POST /webhooks/sync` - Manual sync trigger
- `GET /webhooks/status` - Sync status

### Plane Webhook Configuration

1. Go to Plane workspace settings
2. Add webhook URL: `https://your-domain.com/webhooks/plane`
3. Select events to monitor: Issue created, updated, deleted
4. Set secret (if using `PLANE_WEBHOOK_SECRET`)

## Usage Examples

### Check Service Status

```bash
curl http://localhost:8765/health
```

### Manual Synchronization

```bash
curl -X POST http://localhost:8765/webhooks/sync
```

### Check Sync Status

```bash
curl http://localhost:8765/webhooks/status
```

## Calendar Integration

### Calendar Naming

Calendars are automatically created with the pattern: `Plane: {project_name}`

### Event Properties

| Plane Field | CalDAV Field | Notes |
|-------------|--------------|-------|
| `target_date` | DTSTART/DTEND | All-day format |
| `name` | SUMMARY | Prefixed with `[{sequence_id}]` |
| `description` | DESCRIPTION | Includes assignees, priority, state |
| `completed_at` | STATUS | COMPLETED if set, CONFIRMED otherwise |
| `labels` | CATEGORIES | - |
| `priority` | COLOR | urgent=red, high=orange, etc. |
| Issue URL | URL | Direct link to Plane |

### Event Types

- **All-day events only**: Tasks with target dates become all-day calendar events
- **Status mapping**: Active tasks show as confirmed, completed tasks show as completed (strikethrough)
- **UID stability**: Each task maintains a consistent calendar event UID

## Monitoring

### Logs

Logs are saved to the `logs/` directory:

```bash
tail -f logs/calplanebot.log
```

### Metrics

Available via `/api/v1/health` endpoint:
- Number of projects
- Number of synchronized events
- CalDAV connection status
- Scheduler status

## Troubleshooting

### Common Issues

#### Plane API Connection Problems

1. Verify `PLANE_BASE_URL` is accessible
2. Ensure `PLANE_API_TOKEN` is valid
3. Check token permissions (read access to projects and issues)

#### CalDAV Connection Problems

1. Verify CalDAV server URL
2. Confirm credentials are correct
3. Ensure server supports CalDAV protocol

### Log Analysis

```bash
# View recent errors
grep ERROR logs/calplanebot.log | tail -10

# Check successful synchronizations
grep "Sync completed" logs/calplanebot.log | tail -5
```

## Architecture Overview

```
CalPlaneBot/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models/              # Pydantic models
│   │   ├── plane.py         # Plane models
│   │   └── caldav.py        # CalDAV models
│   ├── services/            # Business logic
│   │   ├── plane_service.py # Plane API integration
│   │   ├── caldav_service.py# CalDAV integration
│   │   ├── sync_service.py  # Synchronization logic
│   │   └── webhook_handler.py# Webhook processing
│   └── routers/
│       └── webhooks.py      # API routes
├── config/
│   └── validation.py        # Configuration validation
├── docs/                    # Documentation
├── logs/                    # Log files
└── tests/                   # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create [Issues](https://github.com/your-repo/issues) for bugs and feature requests
- API documentation available at `/docs` endpoint when running

---

**Note**: This is a beta version. Testing is recommended before production use.

