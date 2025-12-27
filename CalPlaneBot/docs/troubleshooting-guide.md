# CalPlaneBot Troubleshooting Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Audience:** System administrators, support staff
**Purpose:** Problem diagnosis and resolution procedures

## Quick Diagnostic Commands

Always start troubleshooting with these commands:

```bash
# Run comprehensive diagnostics
docker exec calplanebot_calplanebot_1 python /app/manage.py diagnostics

# Check service logs
docker logs calplanebot_calplanebot_1 --tail 20

# Test individual connections
docker exec calplanebot_calplanebot_1 python /app/manage.py test-caldav
docker exec calplanebot_calplanebot_1 python /app/manage.py test-plane
```

## Common Issues and Solutions

### 1. CalDAV Connection Problems

#### Symptom: "CalDAV Connection: ✗ FAILED (Unauthorized)"

**Possible Causes**:
- User not created in CalDAV server
- Incorrect username/password
- Wrong CalDAV server URL

**Solutions**:

1. **Create CalDAV User (Most Common)**:
   - Access your CalDAV server admin panel
   - Create user with credentials matching `.env` file
   - Ensure user has calendar creation permissions

2. **Verify Credentials**:
   ```bash
   # Test with curl
   curl -u your_username:your_password https://your-caldav-server.com/caldav/

   # Or use management tool
   ./manage.py test-caldav
   ```

3. **Check URL Format**:
   ```bash
   # Common CalDAV URLs:
   # Baïkal: https://your-server.com/dav.php
   # Nextcloud: https://your-server.com/remote.php/dav
   # Radicale: https://your-server.com/radicale/username/
   ```

#### Symptom: "CalDAV Connection: ✗ FAILED (Connection refused)"

**Possible Causes**:
- CalDAV server not running
- Firewall blocking connections
- Incorrect port or protocol

**Solutions**:
```bash
# Test network connectivity
ping your-caldav-server.com

# Test specific port
telnet your-caldav-server.com 443

# Check if service is running
curl -k https://your-caldav-server.com/
```

### 2. Plane API Authentication Issues

#### Symptom: "Plane API: ✗ FAILED (401 Unauthorized)"

**Possible Causes**:
- Invalid or expired API token
- Incorrect workspace slug
- Wrong API endpoint format

**Solutions**:

1. **Generate New API Token**:
   - Log in to Plane web interface
   - Go to Settings → API Tokens
   - Generate new token
   - Update `PLANE_API_TOKEN` in `.env`

2. **Verify Workspace Slug**:
   - Check Plane URL when viewing your workspace
   - Update `PLANE_WORKSPACE_SLUG` in `.env`
   - Should match the slug in Plane URL

3. **Test API Endpoint**:
   ```bash
   # Test different API versions
   curl -H "X-API-Key: your_token" https://your-plane.com/api/v1/workspaces/
   curl -H "X-API-Key: your_token" https://your-plane.com/api/workspaces/
   ```

#### Symptom: "Plane API: ✗ FAILED (404 Not Found)"

**Possible Causes**:
- Incorrect base URL
- API version mismatch
- Workspace doesn't exist

**Solutions**:
```bash
# Test base URL accessibility
curl https://your-plane-instance.com/

# Check API documentation for correct endpoints
# Verify workspace exists and is accessible
```

### 3. Service Health Issues

#### Symptom: "Service Status: ✗ FAILED"

**Possible Causes**:
- Service crashed or not started
- Port 8765 not accessible
- Configuration errors

**Solutions**:

1. **Check Service Status**:
   ```bash
   # Docker status
   docker ps | grep calplanebot

   # Service logs
   docker logs calplanebot_calplanebot_1 --tail 50
   ```

2. **Restart Service**:
   ```bash
   # Graceful restart
   docker-compose restart

   # Full rebuild
   docker-compose down && docker-compose up -d --build
   ```

3. **Verify Configuration**:
   ```bash
   # Check environment variables
   docker exec calplanebot_calplanebot_1 python /app/manage.py config

   # Validate .env file
   docker exec calplanebot_calplanebot_1 python /app/manage.py validate-config
   ```

### 4. Synchronization Problems

#### Symptom: Sync fails with errors

**Common Issues**:

1. **ICS Library Errors**:
   ```
   Error: 'str' object has no attribute 'clone'
   ```
   **Fix**: Update to compatible ICS library version

2. **Invalid Status Values**:
   ```
   Error: Invalid status "COMPLETED"
   ```
   **Fix**: Use only supported ICS statuses: `CONFIRMED`, `CANCELLED`, `TENTATIVE`

3. **Date Parsing Issues**:
   ```
   Error: datetime vs date object mismatch
   ```
   **Fix**: Handle both datetime and date objects properly

#### Manual Sync Testing

```bash
# Trigger manual sync
./manage.py sync

# Monitor sync logs
docker logs calplanebot_calplanebot_1 -f | grep -i sync
```

### 5. Calendar Event Issues

#### Symptom: Events not appearing in calendar

**Possible Causes**:
- Calendar client not refreshing
- Events created in wrong calendar
- Timezone issues

**Solutions**:

1. **Force Calendar Refresh**:
   - Thunderbird: F5 or View → Refresh
   - macOS Calendar: View → Refresh Calendars
   - iOS Calendar: Pull down to refresh

2. **Verify Event Creation**:
   ```bash
   # List calendars and events
   ./manage.py list

   # Create test event
   ./manage.py create-event "Test Event"
   ```

3. **Check Timezone Settings**:
   - Verify `EVENT_TIMEZONE` in `.env`
   - Ensure calendar client uses same timezone

#### Symptom: Duplicate events

**Possible Causes**:
- Multiple sync triggers
- Calendar client creating duplicates
- UID conflicts

**Solutions**:
```bash
# Clean duplicate events
./manage.py clean-duplicates

# Check UID format in logs
grep "UID:" logs/calplanebot.log
```

### 6. Performance Issues

#### Symptom: Slow synchronization or high resource usage

**Possible Causes**:
- Large number of issues/projects
- Frequent webhook triggers
- Memory leaks

**Solutions**:

1. **Adjust Sync Interval**:
   ```bash
   # Increase interval in .env
   echo "SYNC_INTERVAL_SECONDS=600" >> .env
   docker-compose restart
   ```

2. **Monitor Resources**:
   ```bash
   # Check container resources
   docker stats calplanebot_calplanebot_1

   # Monitor memory usage
   docker logs calplanebot_calplanebot_1 | grep "Memory"
   ```

3. **Optimize Configuration**:
   - Reduce log level to WARNING
   - Enable only necessary features
   - Consider horizontal scaling

## Advanced Troubleshooting

### Log Analysis

#### Extract Error Patterns

```bash
# Recent errors
grep ERROR logs/calplanebot.log | tail -20

# Failed synchronizations
grep "FAILED\|ERROR" logs/calplanebot.log | tail -10

# Connection issues
grep "Connection\|timeout\|refused" logs/calplanebot.log
```

#### Debug Logging

Enable detailed logging for troubleshooting:

```bash
# Set debug level
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart

# Monitor detailed logs
docker logs calplanebot_calplanebot_1 -f
```

### Network Diagnostics

#### Test External Connectivity

```bash
# DNS resolution
nslookup your-plane-instance.com
nslookup your-caldav-server.com

# SSL certificate validation
openssl s_client -connect your-plane-instance.com:443 -servername your-plane-instance.com

# Network latency
ping -c 5 your-plane-instance.com
```

#### Firewall and Proxy Issues

```bash
# Test with different protocols
curl -v https://your-plane-instance.com/api/v1/workspaces/
curl -v http://your-plane-instance.com/api/v1/workspaces/

# Check proxy settings
env | grep -i proxy
```

### Database and Storage Issues

#### CalDAV Server Problems

**Baïkal-specific issues**:
```bash
# Check Baïkal logs
docker logs baikal_container 2>&1 | tail -50

# Verify database connectivity
docker exec baikal_container php -r "echo 'DB test';"
```

**General CalDAV issues**:
- Check server logs for authentication failures
- Verify calendar permissions
- Test with different CalDAV clients

### API Compatibility Issues

#### Plane API Version Compatibility

```bash
# Check API version
curl -H "X-API-Key: token" https://your-plane.com/api/version

# Test different endpoints
curl -H "X-API-Key: token" https://your-plane.com/api/v1/
curl -H "X-API-Key: token" https://your-plane.com/api/
```

#### CalDAV Server Compatibility

Test with different CalDAV clients:
- Thunderbird Lightning
- macOS Calendar
- iOS Calendar app
- Android Calendar apps

## Recovery Procedures

### Emergency Service Restart

```bash
# Force stop all containers
docker-compose down --remove-orphans

# Clean up resources
docker system prune -f

# Restart fresh
docker-compose up -d --build
```

### Data Recovery

#### Configuration Backup/Restore

```bash
# Backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Restore
cp .env.backup.20251227_100000 .env
```

#### Calendar Data Recovery

```bash
# Export calendar data
./manage.py export-calendar > calendar_backup.ics

# Clear corrupted events
./manage.py clean-corrupted

# Re-sync from Plane
./manage.py sync --full
```

### Full System Reset

**⚠️ WARNING: This will delete all data**

```bash
# Stop services
docker-compose down

# Remove volumes (CAUTION!)
docker volume rm $(docker volume ls -q | grep calplanebot)

# Remove containers
docker-compose rm -f

# Fresh start
docker-compose up -d
```

## Known Issues and Workarounds

### Current Known Issues

1. **Unicode Handling**: Some special characters may not display correctly in all calendar clients
   - **Workaround**: Use standard ASCII characters for issue names

2. **Timezone Conversion**: Events may show wrong time in some clients
   - **Workaround**: Set `EVENT_TIMEZONE` to match your primary timezone

3. **Large Descriptions**: Very long issue descriptions may be truncated
   - **Workaround**: Keep descriptions under 1000 characters

4. **Concurrent Syncs**: Multiple sync operations may cause conflicts
   - **Workaround**: Increase `SYNC_INTERVAL_SECONDS` to reduce frequency

### Version-Specific Issues

#### Python 3.11 Compatibility
- Issue: Some dependencies may have compatibility issues
- Fix: Use Python 3.11+ and update requirements.txt

#### Docker Compose v2
- Issue: Different syntax from v1
- Fix: Update to docker-compose v2.0+

## Monitoring and Alerting

### Health Check Setup

```bash
# Add to cron for regular monitoring
*/5 * * * * /path/to/manage.py diagnostics >> /var/log/calplanebot/health.log 2>&1
```

### Log Monitoring

```bash
# Monitor for critical errors
tail -f logs/calplanebot.log | grep --line-buffered ERROR

# Alert on service failures
#!/bin/bash
if ! docker ps | grep -q calplanebot; then
    echo "CalPlaneBot service is down!" | mail -s "Alert" admin@example.com
fi
```

### Performance Monitoring

```bash
# Sync duration monitoring
grep "Sync completed" logs/calplanebot.log | tail -10 | grep -o "[0-9.]*s"

# Memory usage tracking
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" calplanebot_calplanebot_1
```

## Support Escalation

### Information to Collect

When reporting issues, always include:

1. **Diagnostic Output**:
   ```bash
   ./manage.py diagnostics
   ```

2. **Service Logs**:
   ```bash
   docker logs calplanebot_calplanebot_1 --tail 100
   ```

3. **Configuration (sanitized)**:
   ```bash
   ./manage.py config
   ```

4. **Environment Details**:
   - OS and version
   - Docker version
   - CalDAV server type and version
   - Plane version

### Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **Documentation**: Check this troubleshooting guide
3. **Community**: Search existing issues for similar problems
4. **Enterprise Support**: Contact commercial support if applicable

### Issue Report Template

```
**Issue Summary:**
Brief description of the problem

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- CalPlaneBot version: x.x.x
- Docker version: xx.xx.x
- CalDAV server: Baïkal/Nextcloud/etc v.x.x
- Plane version: v.x.x

**Diagnostic Output:**
```
Paste output from ./manage.py diagnostics
```

**Logs:**
```
Paste relevant log entries
```
```

## Quick Reference

### Most Common Fixes

| Issue | Quick Fix |
|-------|-----------|
| CalDAV Unauthorized | Create user in CalDAV admin panel |
| Plane API 401 | Generate new API token in Plane |
| Service not responding | `docker-compose restart` |
| Sync not working | Check webhook configuration |
| Events not showing | Refresh calendar client |

### Emergency Commands

```bash
# Quick restart
docker-compose restart

# Full rebuild
docker-compose down && docker-compose up -d --build

# Clean restart
docker-compose down --remove-orphans && docker-compose up -d

# Check all services
docker ps && ./manage.py diagnostics
```

