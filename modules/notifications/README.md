# Notifications Module

Efficient notification system for admins to send messages to shops and staff.

## Features

- ✅ **Shop-level notifications**: Send to all staff in selected shops
- ✅ **Direct staff notifications**: Send to specific staff members
- ✅ **Organization-scoped**: Admins can only notify their organization's shops/staff
- ✅ **Read tracking**: Track which staff have read notifications
- ✅ **Statistics**: View read rates and engagement
- ✅ **Expiry support**: Optional expiration dates for notifications
- ✅ **Type classification**: Info, Warning, Urgent, Announcement

## Database Schema

### Tables
1. **notifications** - Main notification content
2. **notification_shop_targets** - Shops targeted by notification
3. **notification_staff_targets** - Staff targeted directly
4. **notification_reads** - Track read status per staff

### Efficient Design
- Shop notifications automatically visible to all staff in that shop
- No duplicate storage - one notification, multiple targets
- Indexed queries for fast retrieval
- Cascade deletes for cleanup

## API Endpoints

### Admin Endpoints

#### Send Notification
```bash
POST /api/notifications/admin/send
Authorization: Bearer <admin_token>

{
  "title": "Important Update",
  "message": "Please review the new inventory procedures",
  "type": "info",  # info, warning, urgent, announcement
  "target_type": "shop",  # shop or staff
  "shop_ids": [1, 2, 3],  # For shop target
  "staff_ids": [],  # For staff target
  "expires_at": "2024-12-31T23:59:59"  # Optional
}
```

#### Get Sent Notifications
```bash
GET /api/notifications/admin/sent?limit=50
Authorization: Bearer <admin_token>
```

#### Get Notification Statistics
```bash
GET /api/notifications/admin/stats/{notification_id}
Authorization: Bearer <admin_token>

Response:
{
  "total_sent": 1,
  "total_recipients": 15,
  "total_read": 10,
  "read_percentage": 66.67
}
```

### Staff Endpoints

#### Get Notifications
```bash
GET /api/notifications/staff/list?include_read=false&limit=50
Authorization: Bearer <staff_token>

Response:
{
  "notifications": [...],
  "unread_count": 5,
  "total_count": 20
}
```

#### Mark as Read
```bash
POST /api/notifications/staff/read/{notification_id}
Authorization: Bearer <staff_token>
```

#### Get Unread Count
```bash
GET /api/notifications/staff/unread-count
Authorization: Bearer <staff_token>

Response:
{
  "unread_count": 5
}
```

## Usage Examples

### Example 1: Notify All Staff in Multiple Shops
```python
# Admin sends notification to Shop 1 and Shop 2
# All staff in both shops will see it
{
  "title": "Holiday Schedule",
  "message": "Shop will close early on Friday",
  "type": "announcement",
  "target_type": "shop",
  "shop_ids": [1, 2]
}
```

### Example 2: Notify Specific Staff Members
```python
# Admin sends to specific staff only
{
  "title": "Training Session",
  "message": "Mandatory training tomorrow at 10 AM",
  "type": "urgent",
  "target_type": "staff",
  "staff_ids": [5, 8, 12]
}
```

### Example 3: Urgent Notification with Expiry
```python
{
  "title": "System Maintenance",
  "message": "System will be down from 2-4 PM today",
  "type": "urgent",
  "target_type": "shop",
  "shop_ids": [1, 2, 3, 4],
  "expires_at": "2024-01-15T16:00:00"
}
```

## Notification Types

- **info**: General information
- **warning**: Important warnings
- **urgent**: Requires immediate attention
- **announcement**: Company-wide announcements

## Security

- ✅ Organization-scoped: Admins can only send to their organization
- ✅ Validation: Checks shop/staff access before sending
- ✅ Authentication: All endpoints require valid JWT tokens
- ✅ Read-only for staff: Staff can only read and mark as read

## Performance Optimizations

1. **Efficient Queries**: Uses JOINs and subqueries for fast retrieval
2. **Indexed Columns**: notification_id, staff_id, shop_id, created_at
3. **Cascade Deletes**: Automatic cleanup of related records
4. **Pagination**: Limit parameter to control result size
5. **Smart Filtering**: Excludes expired and already-read notifications

## Integration

Add to main.py:
```python
from modules.notifications import router as notifications_router
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
```

Run migration to create tables:
```bash
# Tables will be created automatically on first run
# Or manually create using alembic
```
