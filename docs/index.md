# CalPlaneBot Documentation

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Author:** CalPlaneBot Development Team

## Overview

CalPlaneBot is a service that integrates Plane project management tasks with CalDAV-compatible calendars. It automatically synchronizes tasks from [Plane](https://plane.so) with calendars supporting the CalDAV protocol (such as Baïkal, Nextcloud, Radicale).

This documentation provides comprehensive guidance for installing, configuring, administering, and troubleshooting the CalPlaneBot service.

## Documentation Structure

### For End Users and Administrators

| Document | Purpose | Audience |
|----------|---------|----------|
| [User Guide](./user-guide.md) | Complete guide to using CalPlaneBot | End users, administrators |
| [Installation Guide](./installation-guide.md) | Step-by-step installation and setup | System administrators |
| [Administration Guide](./administration-guide.md) | Service management and monitoring | System administrators |
| [Troubleshooting Guide](./troubleshooting-guide.md) | Problem diagnosis and resolution | Support staff, administrators |

### For Developers and Integrators

| Document | Purpose | Audience |
|----------|---------|----------|
| [API Reference](./api-reference.md) | Technical API documentation | Developers, integrators |
| [Architecture](./architecture/) | System design and technical details | Developers, architects |

### Technical Specifications

| Document | Purpose | Audience |
|----------|---------|----------|
| [Plane-CalDAV Integration Contract](./plane-caldav.md) | Technical specification for data synchronization | Developers, QA engineers |

## Quick Start

1. **New Users**: Start with the [Installation Guide](./installation-guide.md)
2. **Administrators**: See the [Administration Guide](./administration-guide.md) for management commands
3. **Troubleshooting**: Refer to the [Troubleshooting Guide](./troubleshooting-guide.md)
4. **Developers**: Check the [API Reference](./api-reference.md) and [Architecture](./architecture/) documentation

## Key Features

- 🔄 **Automatic Synchronization**: Real-time task synchronization from Plane to CalDAV calendars
- 🔔 **Webhook Integration**: Instant updates via Plane webhooks
- 📅 **Calendar Management**: Automatic calendar creation for each Plane project
- 🏷️ **Rich Metadata**: Support for labels, priorities, and assignees
- ⏰ **Flexible Scheduling**: Configurable synchronization intervals
- 🐳 **Docker Support**: Easy deployment with containerization

## System Requirements

- **Runtime**: Python 3.11+
- **External Services**:
  - Plane instance with API access
  - CalDAV server (Baïkal, Nextcloud, Radicale, etc.)
  - Digest or Basic authentication support on CalDAV server

## Support and Contributing

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: API documentation available at `/docs` endpoint when service is running
- **Contributing**: See contribution guidelines in the [User Guide](./user-guide.md)

---

**Note**: This is a beta version. Testing is recommended before production deployment.

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-12-27 | Complete documentation reorganization and English translation |
