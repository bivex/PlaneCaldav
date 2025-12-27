# CalPlaneBot

# CalPlaneBot

🚀 **CalPlaneBot** - Plane ↔ CalDAV Integration Service

Synchronizes tasks from [Plane](https://plane.so) with calendars supporting the CalDAV protocol (such as Baïkal, Nextcloud, Radicale).

## ✨ Key Features

- 🔄 **Automatic Synchronization**: Real-time task synchronization from Plane to CalDAV calendars
- 🔔 **Webhook Integration**: Instant updates via Plane webhooks
- 📅 **Calendar Management**: Automatic calendar creation for each Plane project
- 🏷️ **Rich Metadata**: Support for labels, priorities, and assignees
- ⏰ **Flexible Scheduling**: Configurable synchronization intervals
- 🐳 **Docker Support**: Easy deployment with containerization

## 📋 Requirements

- Python 3.11+
- Access to a Plane instance
- CalDAV server (Baïkal, Nextcloud, Radicale, etc.)
- Digest or Basic authentication support on CalDAV server

## 🧪 Testing & Diagnostics

### CalDAV Connection Test

```bash
# Simple test (uses .env settings)
./test-caldav.sh

# Direct Python script
python test_caldav_auth.py

# With explicit parameters
./test-caldav.sh digest https://your-caldav-server.com/caldav username password
```

The script performs comprehensive checks:
- ✅ CalDAV server authentication
- ✅ Principal resource access
- ✅ Calendar listing and permissions
- ✅ SSL certificates and timeouts

### Full Diagnostics

```bash
# Run comprehensive system diagnostics
docker exec calplanebot_calplanebot_1 python /app/manage.py diagnostics
```

Expected output:
```
============================================================
  Diagnostic Summary
============================================================
CalDAV Connection: ✓ OK
Plane API:         ✓ OK
Service Status:    ✓ OK

✓ All systems operational!
```

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd CalPlaneBot

# Configure environment
cp env.example .env
# Edit .env with your settings

# Start service
docker-compose up -d
```

Service will be available at `http://localhost:8765`

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env file

# Start application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

## 📖 Documentation

Complete documentation is available in the [`docs/`](./docs/) directory:

### For Users
- **[User Guide](./docs/user-guide.md)** - Complete usage guide
- **[Installation Guide](./docs/installation-guide.md)** - Step-by-step setup
- **[Administration Guide](./docs/administration-guide.md)** - Service management
- **[Troubleshooting Guide](./docs/troubleshooting-guide.md)** - Problem resolution

### For Developers
- **[API Reference](./docs/api-reference.md)** - Technical API documentation
- **[Architecture](./docs/architecture/)** - System design and technical details

### Quick Links
- [📋 Setup Checklist](./docs/installation-guide.md#verification-checklist)
- [🔧 Management Commands](./docs/administration-guide.md#available-commands)
- [🐛 Troubleshooting](./docs/troubleshooting-guide.md#common-issues-and-solutions)
- [📊 API Documentation](http://localhost:8765/docs) (when running)


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- Create [Issues](https://github.com/your-repo/issues) for bugs and features
- API documentation available at `/docs` endpoint when service is running
- See [Troubleshooting Guide](./docs/troubleshooting-guide.md) for common issues

---

**Note**: This is a beta version. Testing is recommended before production use.
