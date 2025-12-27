# Apple Calendar Connection Guide for Plane CalDAV

## Front Matter

- **Title**: Apple Calendar Connection Guide for Plane CalDAV
- **Version**: 1.0
- **Date**: December 27, 2025
- **Authors**: bivex
- **Revision History**:
  - v1.0 (December 27, 2025): Initial release

## Introduction

### Purpose of the Document
This document provides step-by-step instructions for end users to connect Apple Calendar to the Plane project management system via CalDAV synchronization. It enables users to view Plane issues as calendar events in Apple Calendar applications.

### Scope of the System or Product
This guide covers the connection and synchronization process for macOS and iOS/iPadOS devices. It includes basic setup, troubleshooting, and verification procedures. Advanced server administration is covered in separate documentation.

### Target Audience and Prerequisites
- **Target Audience**: End users of Apple devices (macOS, iOS, iPadOS) with basic computer skills who need to synchronize Plane project tasks with their calendar.
- **Prerequisites**:
  - Access to a Plane account with active projects.
  - Apple device with Calendar app installed.
  - Internet connection.
  - Basic familiarity with device settings.

### Referenced Documents and Standards
- Plane User Guide
- Apple Calendar Help Documentation


## Concept of Operations

### Overview of System Functions
The Plane CalDAV integration allows users to view project issues from Plane as calendar events in Apple Calendar. The system synchronizes data every 5 minutes, creating events with issue titles, due dates, and descriptions. This enables better task management and deadline tracking.

### Typical User Roles and Scenarios
- **Project Manager**: Monitors team tasks and deadlines in calendar view.
- **Team Member**: Views assigned tasks and schedules work accordingly.
- **Executive**: Oversees project timelines and progress.

### Operating Environment and Constraints
- Supported platforms: macOS 12+, iOS 15+, iPadOS 15+.
- Requires internet connectivity for synchronization.
- One-way sync (Plane to CalDAV); changes in Apple Calendar do not update Plane.
- Server: cal.x-x.top (Digest authentication required).

## Installation and Configuration

### System Requirements
- Apple device with supported OS version.
- CalDAV-compatible server credentials.
- Network access to cal.x-x.top.

### Installation Steps
See Procedures section below for platform-specific setup.

### Configuration and Initial Setup
After adding the CalDAV account, configure calendar visibility in the Calendar app.

### Verification After Installation
Follow the Testing Connection procedures to confirm successful setup.

## Procedures

### Task: Connect Apple Calendar on macOS

**Purpose**: Establish CalDAV connection for calendar synchronization.

**Preconditions**:
- Device is connected to internet.
- You have admin credentials for cal.x-x.top.

**Steps**:
1. Open **System Settings**.
2. Navigate to **Internet Accounts**.
3. Click **+** to add an account.
4. Select **Other Accounts** → **CalDAV Account**.
5. Select "**Manual**" account type.
6. Enter connection details:
   - Username: `admin`
   - Password: `7jLkj01111(*Ebn|m`
   - Server Address: `cal.x-x.top`
7. Click **Sign In**.
8. Wait 10-30 seconds for verification.
9. Click **Done**.

**Result**: CalDAV account appears in Internet Accounts with green status indicator.

**Warnings**: Do not use "Automatic" account type, as it may fail with Digest authentication.

### Task: Connect Apple Calendar on iOS/iPadOS

**Purpose**: Establish CalDAV connection for calendar synchronization.

**Preconditions**:
- Device is connected to internet.
- You have admin credentials for cal.x-x.top.

**Steps**:
1. Open **Settings** app.
2. Scroll down and tap **Calendar**.
3. Tap **Accounts**.
4. Tap **Add Account**.
5. Select **Other** → **Add CalDAV Account**.
6. Enter server information:
   - Server: `cal.x-x.top`
   - User Name: `admin`
   - Password: `7jLkj01111(*Ebn|m`
   - Description: `Plane CalDAV`
7. Tap **Next**.
8. Wait 10-30 seconds for verification.
9. Tap **Save**.

**Result**: CalDAV account appears in Calendar accounts list.

**Warnings**: If connection fails, use Advanced Settings with SSL enabled and port 443.

### Task: Configure Advanced Settings (Troubleshooting)

**Purpose**: Manually configure connection parameters if basic setup fails.

**Preconditions**: Basic setup attempt has failed.

**Steps** (iOS):
1. During account setup, tap **Advanced Settings**.
2. Configure:
   - Use SSL: ON
   - Port: 443
   - Account URL: `https://cal.x-x.top/dav.php/`
3. Tap **Next** and **Save**.

**Steps** (macOS):
1. Go to **System Settings** → **Internet Accounts**.
2. Select the CalDAV account and click details (i icon).
3. Update settings:
   - Server Address: `cal.x-x.top`
   - Port: 443
   - Use SSL: Enabled
   - Path: `/dav.php/`
4. Click **OK**.

**Result**: Connection established with manual parameters.

### Task: Test Connection

**Purpose**: Verify successful synchronization.

**Preconditions**: CalDAV account is configured.

**Steps**:
1. Open **Calendar** app.
2. Check for Plane calendars in sidebar (macOS) or Calendars view (iOS).
3. Create a test issue in Plane.
4. Wait 5 minutes for sync.
5. Refresh Calendar app (pull down on iOS or View → Refresh on macOS).

**Result**: New issue appears as calendar event.

## Troubleshooting and Error Handling

### Common Issues and Resolutions

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| Unable to Verify Account | "Unable to Verify Account Information" error | Use "Manual" account type; check password accuracy |
| No Calendars Found | Account connects but no calendars appear | Wait 1-2 minutes; refresh Calendar app |
| Connection Timeout | Setup hangs at verification | Check internet connection; try Advanced Settings |
| Sync Not Working | Events don't update | Verify server status; restart Calendar app |

### Error Messages and Meaning
- **HTTP 401**: Invalid credentials - check username/password.
- **HTTP 207**: Success - calendars discovered.
- **Connection refused**: Server unreachable - check network/firewall.

### Escalation or Support Contact
For persistent issues, check diagnostic logs or contact system administrator.

## Information for Uninstallation or Decommissioning

### Conditions for Uninstallation
When you no longer need CalDAV synchronization or are switching devices.

### Uninstallation Steps

**macOS**:
1. Open **System Settings** → **Internet Accounts**.
2. Select the CalDAV account.
3. Click **-** to remove.
4. Confirm deletion.

**iOS/iPadOS**:
1. Open **Settings** → **Calendar** → **Accounts**.
2. Select the CalDAV account.
3. Tap **Delete Account**.
4. Confirm deletion.

### Data Backup, Migration, or Clean-up
- No user data is stored locally; calendars will be removed from device.
- Re-add account later to restore synchronization.

## Appendices

### Glossary
- **CalDAV**: Protocol for calendar synchronization over the internet.
- **Digest Authentication**: Secure authentication method requiring username/password.
- **One-way Sync**: Data flows from Plane to Apple Calendar only.
- **Preconditions**: Requirements that must be met before performing a task.
- **Postconditions**: Expected results after completing a task.

### Acronyms and Abbreviations
- **CalDAV**: Calendaring Extensions to WebDAV
- **HTTP**: HyperText Transfer Protocol
- **SSL**: Secure Sockets Layer
- **iOS**: iPhone Operating System
- **macOS**: Macintosh Operating System

### Index
- Account setup: See Procedures
- Advanced settings: See Procedures, Troubleshooting
- Authentication: See Introduction, Troubleshooting
- Calendars: See Concept of Operations, Testing
- Connection issues: See Troubleshooting
- Credentials: See Front Matter, Procedures
- macOS setup: See Procedures
- iOS setup: See Procedures
- Sync frequency: See Concept of Operations
- Testing: See Procedures
- Uninstall: See Uninstallation
- Verification: See Procedures
