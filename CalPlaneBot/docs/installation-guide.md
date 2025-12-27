# CalPlaneBot Installation Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** System administrators
**Purpose:** Step-by-step installation and configuration guide

## Prerequisites

Before installing CalPlaneBot, ensure you have the following:

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Network**: Internet access for downloading images and dependencies
- **Storage**: At least 2GB free space for containers and data

### External Services

- **Plane Instance**: Access to a running Plane installation with API access
- **CalDAV Server**: A CalDAV-compatible calendar server (Baïkal, Nextcloud, Radicale, etc.)
- **API Token**: Valid Plane API token with appropriate permissions
- **CalDAV Credentials**: Username and password for CalDAV server access

## Installation Methods

CalPlaneBot supports two installation methods:

### Method 1: Docker Compose (Recommended)

This is the easiest and most reliable installation method.

### Method 2: Manual Python Installation

For development or when Docker is not available.

---

## Method 1: Docker Compose Installation

### Step 1: Download the Project

```bash
# Clone the repository
git clone <repository-url>
cd CalPlaneBot

# Verify files are present
ls -la
```

Expected output should show the project files including `docker-compose.yml`, `Dockerfile`, etc.

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration file
nano .env  # or use your preferred editor
```

#### Required Configuration

Edit the `.env` file with your specific values:

```bash
# ===========================================
# REQUIRED: Plane Configuration
# ===========================================
PLANE_BASE_URL=https://your-plane-instance.plane.so
PLANE_API_TOKEN=plane_api_your_token_here
PLANE_WORKSPACE_SLUG=your-workspace-slug

# ===========================================
# REQUIRED: CalDAV Configuration
# ===========================================
CALDAV_URL=https://your-caldav-server.com/caldav
CALDAV_USERNAME=your_caldav_username
CALDAV_PASSWORD=your_caldav_password
CALDAV_AUTH_TYPE=digest  # Use "digest" (recommended) or "basic"
```

#### Optional Configuration

```bash
# ===========================================
# OPTIONAL: Webhook Security
# ===========================================
PLANE_WEBHOOK_SECRET=your_webhook_secret_here

# ===========================================
# OPTIONAL: Synchronization Settings
# ===========================================
SYNC_INTERVAL_SECONDS=300          # 5 minutes
ENABLE_SYNC=true                   # Enable automatic sync
EVENT_DEFAULT_DURATION_HOURS=1     # Default event duration
EVENT_TIMEZONE=Europe/Moscow       # Your timezone

# ===========================================
# OPTIONAL: Logging and Debugging
# ===========================================
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
```

### Step 3: Verify CalDAV Server Setup

Before starting CalPlaneBot, ensure your CalDAV server is properly configured:

#### For Baïkal Server

1. **Access Admin Panel**:
   - Visit: `https://your-domain.com/admin/`
   - Login with admin credentials

2. **Create User**:
   - Go to "Users" section
   - Create a new user with:
     - Username: `your_username`
     - Password: `your_password`
     - Email: `your_email@domain.com`

3. **Create Calendar**:
   - Go to "Calendars" section
   - Create a new calendar for the user
   - Note the calendar URL for verification

#### For Other CalDAV Servers

- **Nextcloud**: Enable CalDAV app, create calendar in web interface
- **Radicale**: Configure users and calendars in configuration file
- **Custom Server**: Follow your server's documentation

#### Test CalDAV Connection

```bash
# Test basic connectivity
curl -u your_username:your_password https://your-caldav-server.com/caldav/

# Expected: XML response with calendar information
```

### Step 4: Verify Plane API Access

#### Generate API Token

1. **Access Plane Settings**:
   - Log in to your Plane instance
   - Go to Account Settings → API Tokens

2. **Create Token**:
   - Click "Create API Token"
   - Give it a descriptive name (e.g., "CalPlaneBot Integration")
   - Copy the generated token immediately (it won't be shown again)

3. **Verify Permissions**:
   - The token needs read access to projects and issues
   - Test the token with a simple API call

#### Test Plane API Connection

```bash
# Test API connectivity
curl -H "X-API-Key: your_plane_api_token" \
     https://your-plane-instance.plane.so/api/v1/workspaces/

# Expected: JSON response with workspace information
```

### Step 5: Start the Service

```bash
# Start CalPlaneBot with Docker Compose
docker-compose up -d

# Verify containers are running
docker ps | grep calplanebot
```

Expected output should show the CalPlaneBot container running.

### Step 6: Verify Installation

#### Check Service Health

```bash
# Test basic health endpoint
curl http://localhost:8765/health

# Expected response:
# {"status":"healthy","timestamp":"2025-12-27T..."}
```

#### Run Comprehensive Diagnostics

```bash
# Run built-in diagnostics
docker exec calplanebot_calplanebot_1 python /app/manage.py diagnostics
```

Expected successful output:
```
============================================================
  Diagnostic Summary
============================================================
CalDAV Connection: ✓ OK
Plane API:         ✓ OK
Service Status:    ✓ OK

✓ All systems operational!
```

#### Check Logs

```bash
# View recent logs
docker logs calplanebot_calplanebot_1 --tail 20

# Follow logs in real-time
docker logs calplanebot_calplanebot_1 -f
```

---

## Method 2: Manual Python Installation

### Step 1: System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# or
sudo yum update -y                      # CentOS/RHEL
# or
brew update                             # macOS
```

### Step 2: Install Python

```bash
# Install Python 3.11+ if not present
python3 --version

# If needed, install Python
sudo apt install python3.11 python3.11-venv -y
```

### Step 3: Create Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv calplanebot_env
source calplanebot_env/bin/activate

# Verify activation
which python
# Should show: /path/to/calplanebot_env/bin/python
```

### Step 4: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, caldav, requests; print('Dependencies OK')"
```

### Step 5: Configure Environment

```bash
# Copy and edit environment file
cp env.example .env
nano .env  # Edit with your configuration
```

### Step 6: Start the Service

```bash
# Start with uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload

# Or run directly
python app/main.py
```

---

## Post-Installation Configuration

### Configure Plane Webhooks

1. **Access Workspace Settings**:
   - Go to your Plane workspace settings
   - Navigate to "Webhooks" or "Integrations" section

2. **Create Webhook**:
   - URL: `https://your-domain.com/webhooks/plane`
   - Events: Issue created, updated, deleted
   - Secret: Your `PLANE_WEBHOOK_SECRET` (if configured)

3. **Test Webhook**:
   - Create a test issue in Plane
   - Verify it appears in your CalDAV calendar

### SSL Configuration (Production)

For production deployments, configure SSL:

#### Using Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/calplanebot
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/calplanebot /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Firewall Configuration

```bash
# Allow HTTP/HTTPS traffic
sudo ufw allow 80
sudo ufw allow 443

# Allow SSH (if needed)
sudo ufw allow ssh
```

---

## Troubleshooting Installation Issues

### CalDAV Connection Problems

**Symptom**: "CalDAV Connection: ✗ FAILED"

**Possible Causes**:
- Incorrect URL or credentials
- Server not supporting required authentication method
- SSL certificate issues

**Solutions**:
```bash
# Test basic connectivity
curl -k https://your-caldav-server.com/

# Test with credentials
curl -u username:password https://your-caldav-server.com/caldav/
```

### Plane API Authentication Issues

**Symptom**: "Plane API: ✗ FAILED (401 Unauthorized)"

**Possible Causes**:
- Invalid or expired API token
- Incorrect workspace slug
- Insufficient token permissions

**Solutions**:
```bash
# Test API token
curl -H "X-API-Key: your_token" https://your-plane.com/api/v1/workspaces/

# Check token permissions in Plane UI
# Regenerate token if necessary
```

### Service Startup Problems

**Symptom**: Container exits immediately or health endpoint fails

**Solutions**:
```bash
# Check container logs
docker logs calplanebot_calplanebot_1

# Check for missing environment variables
docker exec calplanebot_calplanebot_1 env | grep -E "(PLANE|CALDAV)"

# Verify configuration file syntax
python -c "import os; [print(f'{k}={v}') for k,v in os.environ.items() if k.startswith(('PLANE_', 'CALDAV_'))]"
```

### Network Connectivity Issues

**Symptom**: Connection timeouts or DNS resolution failures

**Solutions**:
```bash
# Test DNS resolution
nslookup your-plane-instance.com
nslookup your-caldav-server.com

# Test network connectivity
ping your-plane-instance.com
ping your-caldav-server.com

# Check firewall settings
sudo ufw status
sudo iptables -L
```

---

## Verification Checklist

Use this checklist to verify your installation:

### Infrastructure Setup
- [ ] SSL certificates configured
- [ ] Reverse proxy (nginx) configured
- [ ] Firewall rules in place
- [ ] Docker containers running

### Service Configuration
- [ ] Environment variables set correctly
- [ ] CalDAV server accessible
- [ ] Plane API token valid
- [ ] Webhook secret configured (optional)

### Service Verification
- [ ] Health endpoint responding
- [ ] Diagnostic commands pass
- [ ] Logs show successful startup
- [ ] Manual sync works

### Integration Testing
- [ ] Webhook events processed
- [ ] Calendar events created
- [ ] Synchronization working
- [ ] No duplicate events

## Next Steps

After successful installation:

1. **Configure Monitoring**: Set up log monitoring and alerts
2. **Schedule Backups**: Regular backups of configuration and data
3. **Performance Tuning**: Adjust sync intervals based on usage
4. **Security Hardening**: Implement additional security measures
5. **Documentation**: Keep installation documentation current

## Support

If you encounter issues during installation:

1. Check the [Troubleshooting Guide](./troubleshooting-guide.md)
2. Review service logs: `docker logs calplanebot_calplanebot_1`
3. Run diagnostics: `docker exec calplanebot_calplanebot_1 python /app/manage.py diagnostics`
4. Check GitHub Issues for similar problems
5. Create a new issue with detailed error information

