# Plane ↔ CalDAV Integration Contract

## Core Principles

### 1. Single Source of Truth
**Plane is the master.**
CalDAV calendar is read-only mirror, changes in calendar are ignored.

### 2. Event Creation Rule
**No `target_date` → No event**

| Plane Issue | Calendar Event |
|-------------|----------------|
| Has `target_date` (due date) | ✅ Creates ALL-DAY event |
| No `target_date` | ❌ No event created |
| `target_date` removed | ❌ Event deleted from calendar |

`start_date` is **ignored** for calendar sync.

### 3. Event Type
**ALL-DAY events only**

Plane stores dates without time → CalDAV uses `VALUE=DATE`:
```ical
DTSTART;VALUE=DATE:20250110
DTEND;VALUE=DATE:20250111
```

**Why:** Prevents visual stacking, represents deadlines correctly.

### 4. Completion Handling
**COMPLETED ≠ delete**

| Issue State | Calendar Event |
|-------------|----------------|
| Active | `STATUS:CONFIRMED` |
| Completed | `STATUS:COMPLETED` (strikethrough) |
| Deleted | Event deleted |

Completed tasks stay in calendar (strikethrough) to preserve history.

### 5. UID Invariant
**UID never changes**

Format: `plane-issue-{issue.id}@calplanebot`

Stable UID enables proper update tracking across systems.

### 6. Sync Direction
**One-way: Plane → CalDAV**

- Webhook triggers: `create`, `update`, `delete`
- Periodic full sync every 5 minutes
- Calendar changes are **not** synced back to Plane

### 7. Calendar Mapping
**1 Plane Project → 1 CalDAV Calendar**

Calendar name: `Plane: {project_name}`

### 8. Event Updates
**UPDATE, not delete+create**

Preserves calendar client state (alarms, client-side notes).

## Event Field Mapping

| Plane Field | CalDAV Field | Notes |
|-------------|--------------|-------|
| `target_date` | DTSTART/DTEND | ALL-DAY format |
| `name` | SUMMARY | Prefixed with `[{sequence_id}]` |
| `description` | DESCRIPTION | With assignees, priority, state |
| `completed_at` | STATUS | COMPLETED if set, else CONFIRMED |
| `labels` | CATEGORIES | |
| `priority` | COLOR | urgent=red, high=orange, etc. |
| issue URL | URL | Direct link to Plane |

## Implementation Notes

- Event creation uses `ics.Event.make_all_day()` for DATE format
- RFC 5545: ALL-DAY events require `DTEND = DTSTART + 1 day`
- Retries: 3 attempts with exponential backoff for CalDAV operations
- Calendar cache: 1 hour TTL to reduce CalDAV roundtrips

## Edge Cases

1. **Issue without dates**: Skipped (no event created)
2. **Removed target_date**: Event deleted from calendar
3. **Issue deleted**: Event deleted via webhook `action=delete`
4. **Duplicate sync**: UID prevents duplicates, UPDATE used instead

---

**Last updated:** 2025-12-27
**Author:** CalPlaneBot
