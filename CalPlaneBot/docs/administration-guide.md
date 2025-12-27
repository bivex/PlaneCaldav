# CalPlaneBot Administration Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** System administrators, DevOps engineers
**Purpose:** Service management, monitoring, and maintenance procedures

## Overview

This guide covers the administration and management of CalPlaneBot after installation. It includes command-line tools, monitoring procedures, maintenance tasks, and troubleshooting techniques.

## Management Tools

CalPlaneBot provides a comprehensive management CLI tool (`manage.py`) for administrative tasks.

### Installation

The management script uses the same dependencies as CalPlaneBot:

```bash
# Install dependencies
pip install -r requirements.txt

# Or run via Docker
docker exec calplanebot_calplanebot_1 python /app/manage.py <command>
```

### Usage

```bash
# Local execution
./manage.py <command> [args]

# Docker execution
docker exec calplanebot_calplanebot_1 python /app/manage.py <command> [args]
```

## Available Commands

### Connection Testing

#### Test CalDAV Connection

```bash
./manage.py test-caldav
```

**Purpose**: Verify CalDAV server connectivity and authentication.

**What it does**:
- Connects to CalDAV server using credentials from `.env`
- Lists all available calendars for the user
- Shows event count for each calendar
- Validates read/write permissions

**Expected output**:
```
============================================================
  Testing CalDAV Connection
============================================================

ℹ Connecting to: https://your-caldav-server.com/caldav
ℹ Username: your_username
✓ Connected to CalDAV server
ℹ Principal: https://your-caldav-server.com/caldav/principals/your_username/
✓ Found 2 calendar(s)
  📅 Personal
     URL: https://your-caldav-server.com/caldav/calendars/your_username/personal/
     Events: 15
  📅 Work
     URL: https://your-caldav-server.com/caldav/calendars/your_username/work/
     Events: 8
```

**Troubleshooting**:
- "Unauthorized": Check username/password in `.env`
- "Connection failed": Verify server URL and network connectivity
- "No calendars found": Ensure user has calendars created

#### Test Plane API Connection

```bash
./manage.py test-plane
```

**Purpose**: Verify Plane API connectivity and permissions.

**What it does**:
- Connects to Plane API using token from `.env`
- Retrieves workspace information
- Lists available projects
- Validates API token permissions

**Expected output**:
```
============================================================
  Testing Plane API Connection
============================================================

ℹ Connecting to: https://your-plane-instance.plane.so
ℹ Workspace: your-workspace
✓ Connected to Plane API
ℹ Workspace Name: Your Workspace
ℹ Workspace ID: workspace-uuid
✓ Found 5 project(s)
  📁 Project Alpha
  📁 Project Beta
  📁 Project Gamma
```

**Troubleshooting**:
- "401 Unauthorized": Check API token validity
- "Workspace not found": Verify workspace slug
- "Connection timeout": Check network and server status

### Service Management

#### Check Service Status

```bash
./manage.py status
```

**Purpose**: Verify CalPlaneBot service availability.

**What it does**:
- Tests HTTP connectivity to service on port 8765
- Checks health endpoint response
- Validates service responsiveness

**Expected output**:
```
============================================================
  Service Status Check
============================================================

ℹ Service URL: http://localhost:8765
✓ Service is responding
✓ Health endpoint: OK
ℹ Uptime: 2 hours 15 minutes
ℹ Active sync tasks: 0
```

#### Run Full Diagnostics

```bash
./manage.py diagnostics
```

**Purpose**: Comprehensive system health check.

**What it does**:
- Tests CalDAV connection
- Tests Plane API connection
- Checks service status
- Provides summary report with actionable recommendations

**Expected output**:
```
============================================================
  Diagnostic Summary
============================================================
CalDAV Connection: ✓ OK
Plane API:         ✓ OK
Service Status:    ✓ OK

✓ All systems operational!

Recommendations:
- Consider adjusting sync interval if high load detected
- Review log rotation settings for long-term operation
```

### Synchronization Management

#### Trigger Manual Sync

```bash
./manage.py sync
```

**Purpose**: Manually initiate synchronization between Plane and CalDAV.

**What it does**:
- Retrieves all Plane issues with target dates
- Creates/updates corresponding CalDAV events
- Reports sync results and statistics

**Expected output**:
```
============================================================
  Manual Sync Triggered
============================================================

ℹ Starting synchronization...
ℹ Found 12 Plane projects
ℹ Processing issues with target dates...

📊 Sync Results:
  ✓ Created: 3 events
  ✓ Updated: 7 events
  ✓ Deleted: 1 event (issue completed)
  ⚠ Skipped: 2 events (no target_date)

✓ Sync completed successfully (0.8s)
```

#### View Synchronization Status

```bash
# Via API endpoint
curl http://localhost:8765/webhooks/status

# Via management tool
./manage.py sync-status
```

### Calendar and Event Management

#### List Calendars and Events

```bash
./manage.py list
```

**Purpose**: Display all calendars and their events.

**What it does**:
- Lists all CalDAV calendars
- Shows recent events (first 10 per calendar)
- Displays event summaries and dates

**Expected output**:
```
============================================================
  Calendar Overview
============================================================

📅 Plane: Project Alpha (3 events)
  • [PA-001] Implement login system (2025-01-15)
  • [PA-002] Design database schema (2025-01-20)
  • [PA-003] Write API documentation (2025-01-25)

📅 Plane: Project Beta (5 events)
  • [PB-001] Setup CI/CD pipeline (2025-01-10)
  • [PB-002] Implement testing framework (2025-01-18)
  ...
```

#### Create Test Event

```bash
./manage.py create-event "Test Event Title"
```

**Purpose**: Create a test event for CalDAV connectivity verification.

**What it does**:
- Creates a test event in the default calendar
- Useful for testing write permissions
- Event includes timestamp and test metadata

### Configuration Management

#### Show Current Configuration

```bash
./manage.py config
```

**Purpose**: Display current configuration settings.

**What it does**:
- Shows all environment variables
- Masks sensitive information (passwords, tokens)
- Indicates configuration source (.env file)

**Expected output**:
```
============================================================
  Configuration Overview
============================================================

📁 Configuration file: /app/.env

Plane Configuration:
  PLANE_BASE_URL: https://your-plane-instance.plane.so
  PLANE_API_TOKEN: plane_api_****masked****
  PLANE_WORKSPACE_SLUG: your-workspace

CalDAV Configuration:
  CALDAV_URL: https://your-caldav-server.com/caldav
  CALDAV_USERNAME: your_username
  CALDAV_PASSWORD: ****masked****
  CALDAV_AUTH_TYPE: digest

Sync Configuration:
  SYNC_INTERVAL_SECONDS: 300
  ENABLE_SYNC: true
  EVENT_TIMEZONE: Europe/Moscow
```

#### Validate Configuration

```bash
./manage.py validate-config
```

**Purpose**: Validate configuration file syntax and required variables.

**What it does**:
- Checks for required environment variables
- Validates URL formats
- Tests configuration file accessibility

## Monitoring and Maintenance

### Log Management

#### View Service Logs

```bash
# Docker logs
docker logs calplanebot_calplanebot_1 --tail 50

# Follow logs in real-time
docker logs calplanebot_calplanebot_1 -f

# Service logs (when running locally)
tail -f logs/calplanebot.log
```

#### Log Analysis

```bash
# Recent errors
grep ERROR logs/calplanebot.log | tail -10

# Successful synchronizations
grep "Sync completed" logs/calplanebot.log | tail -5

# Failed operations
grep "FAILED\|ERROR" logs/calplanebot.log | tail -20
```

### Health Monitoring

#### Health Endpoints

```bash
# Basic health check
curl http://localhost:8765/health

# Detailed health check
curl http://localhost:8765/api/v1/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-27T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2h 15m",
  "metrics": {
    "projects_synced": 5,
    "events_created": 127,
    "last_sync": "2025-12-27T10:25:00Z",
    "sync_status": "idle"
  }
}
```

### Performance Monitoring

#### Sync Performance Metrics

```bash
# View sync performance
curl http://localhost:8765/api/v1/metrics

# Recent sync durations
grep "Sync completed" logs/calplanebot.log | tail -10 | grep -o "[0-9.]*s"
```

### Backup and Recovery

#### Configuration Backup

```bash
# Backup environment file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

#### Data Recovery

```bash
# Restore configuration
cp .env.backup.20251227_100000 .env

# Restore from backup
tar -xzf logs_backup_20251227.tar.gz
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Weekly Tasks

```bash
# 1. Check service health
./manage.py diagnostics

# 2. Review recent errors
grep ERROR logs/calplanebot.log | tail -20

# 3. Clean old logs (optional)
find logs/ -name "*.log" -mtime +30 -delete

# 4. Verify sync performance
./manage.py sync-status
```

#### Monthly Tasks

```bash
# 1. Update dependencies
pip install --upgrade -r requirements.txt

# 2. Review configuration settings
./manage.py config

# 3. Check disk space
df -h

# 4. Backup configuration
cp .env .env.monthly.$(date +%Y%m)
```

### Service Restart Procedures

#### Graceful Restart

```bash
# Docker Compose
docker-compose restart

# Individual container
docker restart calplanebot_calplanebot_1
```

#### Full Service Restart

```bash
# Stop services
docker-compose down

# Rebuild if code changes
docker-compose up -d --build

# Or just restart
docker-compose up -d
```

### Emergency Procedures

#### Service Not Responding

```bash
# 1. Check container status
docker ps | grep calplanebot

# 2. View recent logs
docker logs calplanebot_calplanebot_1 --tail 50

# 3. Restart service
docker-compose restart

# 4. If restart fails, check resource usage
docker stats calplanebot_calplanebot_1
```

#### Database Corruption Recovery

```bash
# 1. Stop service
docker-compose down

# 2. Backup corrupted data (if recoverable)
docker run --rm -v calplanebot_data:/data alpine tar czf - /data > corrupted_backup.tar.gz

# 3. Clear corrupted data
docker volume rm calplanebot_data

# 4. Restart service (fresh start)
docker-compose up -d
```

## Security Management

### API Token Management

#### Rotate Plane API Token

```bash
# 1. Generate new token in Plane UI
# 2. Update .env file
echo "PLANE_API_TOKEN=plane_api_new_token_here" >> .env

# 3. Test new token
./manage.py test-plane

# 4. Restart service
docker-compose restart
```

#### Update CalDAV Credentials

```bash
# 1. Update password in CalDAV server
# 2. Update .env file
echo "CALDAV_PASSWORD=new_password" >> .env

# 3. Test connection
./manage.py test-caldav

# 4. Restart service
docker-compose restart
```

### Access Control

#### Webhook Security

```bash
# Enable webhook secret
echo "PLANE_WEBHOOK_SECRET=your_secure_secret" >> .env

# Restart service
docker-compose restart
```

### Network Security

#### Firewall Configuration

```bash
# Allow service port
sudo ufw allow 8765

# Allow webhook port (if different)
sudo ufw allow 443

# Verify rules
sudo ufw status
```

## Troubleshooting Procedures

### Automated Troubleshooting

```bash
# Run comprehensive diagnostics
./manage.py diagnostics

# Check all connections
./manage.py test-caldav && ./manage.py test-plane && ./manage.py status
```

### Manual Troubleshooting Steps

#### Connection Issues

```bash
# 1. Test network connectivity
ping your-plane-instance.plane.so
ping your-caldav-server.com

# 2. Test SSL certificates
openssl s_client -connect your-caldav-server.com:443 -servername your-caldav-server.com

# 3. Check DNS resolution
nslookup your-plane-instance.plane.so
```

#### Performance Issues

```bash
# Check resource usage
docker stats calplanebot_calplanebot_1

# Monitor sync performance
time ./manage.py sync

# Check log for bottlenecks
grep "slow\|timeout" logs/calplanebot.log
```

#### Data Synchronization Issues

```bash
# Check for duplicate events
./manage.py list | grep -c "duplicate\|DUPLICATE"

# Verify event creation
./manage.py create-event "Troubleshooting Test $(date)"

# Check sync logs
grep "sync\|Sync" logs/calplanebot.log | tail -20
```

## Advanced Administration

### Custom Synchronization Schedules

#### Modify Sync Interval

```bash
# Update environment
echo "SYNC_INTERVAL_SECONDS=600" >> .env  # 10 minutes

# Restart service
docker-compose restart
```

#### Disable Automatic Sync

```bash
# For maintenance
echo "ENABLE_SYNC=false" >> .env
docker-compose restart

# Re-enable after maintenance
echo "ENABLE_SYNC=true" >> .env
docker-compose restart
```

### Log Level Management

#### Increase Logging for Debugging

```bash
# Set debug level
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart

# Monitor detailed logs
docker logs calplanebot_calplanebot_1 -f
```

#### Reduce Logging for Production

```bash
# Set warning level only
echo "LOG_LEVEL=WARNING" >> .env
docker-compose restart
```

### Scaling Considerations

#### Multiple Instances

```bash
# Scale horizontally (if supported)
docker-compose up -d --scale calplanebot=3

# Load balancer configuration required
```

#### Resource Allocation

```yaml
# docker-compose.yml adjustments
services:
  calplanebot:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## Support and Escalation

### Getting Help

1. **Run Diagnostics**: Always start with `./manage.py diagnostics`
2. **Check Logs**: Review recent logs for error patterns
3. **Test Connections**: Verify both CalDAV and Plane API connectivity
4. **Search Issues**: Check GitHub repository for similar issues

### Escalation Checklist

- [ ] Basic diagnostics run and reviewed
- [ ] Service logs examined for errors
- [ ] Network connectivity verified
- [ ] External service status checked
- [ ] Configuration validated
- [ ] Recent changes documented
- [ ] Reproduction steps identified

### Contact Information

- **Issues**: Create GitHub issue with diagnostic output
- **Security**: Report security issues privately
- **Commercial Support**: Contact enterprise support team

## Quick Reference

### Most Used Commands

```bash
# Health check
./manage.py diagnostics

# Manual sync
./manage.py sync

# View logs
docker logs calplanebot_calplanebot_1 -f

# Restart service
docker-compose restart

# Check configuration
./manage.py config
```

### Emergency Commands

```bash
# Force stop all
docker-compose down --remove-orphans

# Clean restart
docker-compose down && docker system prune -f && docker-compose up -d

# Full rebuild
docker-compose down && docker-compose up -d --build --force-recreate
```

