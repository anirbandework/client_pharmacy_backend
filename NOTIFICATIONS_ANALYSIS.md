# 🔔 Notifications Module Analysis for 100K Users

## 📊 Endpoint Inventory

### **Total Endpoints: 7**

#### Admin Endpoints (3):
```
POST /api/notifications/admin/send              → Create notification
GET  /api/notifications/admin/sent              → Get sent notifications
GET  /api/notifications/admin/stats/{id}        → Get read statistics
```

#### Staff Endpoints (4):
```
GET  /api/notifications/staff/list              → Get notifications
POST /api/notifications/staff/read/{id}         → Mark as read
GET  /api/notifications/staff/unread-count      → Get unread count
```

---

## 🚨 CRITICAL ISSUES FOR 100K USERS

### **Issue #1: Unread Count Polling** ⚠️ HIGH PRIORITY

**Current Code:**
```python
@router.get("/staff/unread-count")
def get_unread_count(staff, db):
    notifications_data = NotificationService.get_staff_notifications(
        db, staff, include_read=False, limit=1000  # ❌ QUERIES 1000 RECORDS!
    )
    return {"unread_count": len(notifications_data)}
```

**Problem:**
- Staff apps poll this every 5-10 seconds for badge count
- Each call queries up to 1000 notifications
- Complex joins: Notification → ShopTarget/StaffTarget → NotificationRead
- **20K staff × 12 req/min = 240,000 req/min!**
- **Database will crash!**

**Impact on 100K Users:**
```
Active Staff: 20,000
Polling Frequency: Every 5 seconds = 12 req/min
Total Load: 240,000 req/min
Per Instance (3): 80,000 req/min (1,333 req/sec)
Database Queries: 240,000 complex joins/min
Result: DATABASE OVERLOAD 🔥
```

---

### **Issue #2: Notification List Query** ⚠️ MEDIUM PRIORITY

**Current Code:**
```python
@router.get("/staff/list")
def get_staff_notifications(staff, db, limit=50):
    # Complex query with OR conditions
    # Joins: Notification → ShopTarget → NotificationRead
    # No caching
```

**Problem:**
- Complex OR query with subqueries
- No pagination (limit=50 but no offset)
- No caching
- Called frequently when user opens notifications

---

### **Issue #3: Stats Query** ⚠️ LOW PRIORITY

**Current Code:**
```python
@router.get("/admin/stats/{notification_id}")
def get_notification_stats(notification_id, admin, db):
    # Counts all staff in shops
    # Counts all reads
    # No caching
```

**Problem:**
- Counts can be expensive for large shops
- No caching
- Admin might poll this for dashboard

---

## ✅ SOLUTIONS

### **Solution #1: Optimize Unread Count (CRITICAL)**

Add Redis caching + database optimization:

```python
# In service.py
@staticmethod
def get_unread_count_optimized(db: Session, staff: Staff) -> int:
    """Optimized unread count with single query"""
    
    # Single COUNT query instead of fetching all records
    shop_notif_count = db.query(Notification).filter(
        and_(
            Notification.target_type == NotificationTargetType.SHOP,
            Notification.id.in_(
                db.query(NotificationShopTarget.notification_id).filter(
                    NotificationShopTarget.shop_id == staff.shop_id
                )
            ),
            ~Notification.id.in_(
                db.query(NotificationRead.notification_id).filter(
                    NotificationRead.staff_id == staff.id
                )
            ),
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.now()
            )
        )
    ).count()
    
    staff_notif_count = db.query(Notification).filter(
        and_(
            Notification.target_type == NotificationTargetType.STAFF,
            Notification.id.in_(
                db.query(NotificationStaffTarget.notification_id).filter(
                    NotificationStaffTarget.staff_id == staff.id
                )
            ),
            ~Notification.id.in_(
                db.query(NotificationRead.notification_id).filter(
                    NotificationRead.staff_id == staff.id
                )
            ),
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.now()
            )
        )
    ).count()
    
    return shop_notif_count + staff_notif_count
```

**Add Redis Caching:**
```python
# In routes.py
from app.utils.cache import dashboard_cache

@router.get("/staff/unread-count")
def get_unread_count(staff, db):
    # Check cache (30 second TTL)
    cache_key = f"unread_count:{staff.id}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=30)
    if cached is not None:
        return {"unread_count": cached}
    
    # Query database
    count = NotificationService.get_unread_count_optimized(db, staff)
    
    # Cache result
    dashboard_cache.set(cache_key, count)
    
    return {"unread_count": count}
```

**Add Rate Limit:**
```python
# In rate_limit.py
HIGH_FREQUENCY_LIMITS = {
    "/api/attendance/wifi/heartbeat": {"limit": 3, "window": 60},
    "/api/attendance/wifi/status": {"limit": 120, "window": 60},
    "/api/notifications/staff/unread-count": {"limit": 120, "window": 60}  # 2 req/sec
}
```

---

### **Solution #2: Add Pagination to List**

```python
@router.get("/staff/list")
def get_staff_notifications(
    staff, db,
    include_read: bool = False,
    limit: int = 20,  # Reduced from 50
    offset: int = 0   # Add pagination
):
    # ... existing code with offset ...
```

---

### **Solution #3: Cache Stats**

```python
@router.get("/admin/stats/{notification_id}")
def get_notification_stats(notification_id, admin, db):
    # Check cache (60 second TTL)
    cache_key = f"notif_stats:{notification_id}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=60)
    if cached:
        return cached
    
    stats = NotificationService.get_notification_stats(db, notification_id)
    # ... existing code ...
    
    result = schemas.NotificationStats(...)
    dashboard_cache.set(cache_key, result)
    return result
```

---

## 📊 Load Impact After Fixes

### **Before Optimization:**
```
Unread Count Endpoint:
- Queries: 1000 records per request
- Load: 240,000 req/min
- Database: 240,000 complex queries/min
- Result: CRASH 🔥
```

### **After Optimization:**
```
Unread Count Endpoint:
- Cache Hit Rate: 90% (30s TTL)
- Database Queries: 24,000/min (90% cached)
- Query Type: Single COUNT (optimized)
- Load: 240,000 req/min (mostly from cache)
- Result: STABLE ✅
```

---

## 🎯 Rate Limiting Strategy

### **Notifications Module:**
```
High-Frequency:
├─ /api/notifications/staff/unread-count → 120/min (2 req/sec) + 30s cache

Standard (User-Type):
├─ /api/notifications/admin/send         → 300/min (admin)
├─ /api/notifications/admin/sent         → 300/min (admin)
├─ /api/notifications/admin/stats/{id}   → 300/min (admin) + 60s cache
├─ /api/notifications/staff/list         → 100/min (staff)
└─ /api/notifications/staff/read/{id}    → 100/min (staff)
```

---

## 💾 Database Optimization

### **Add Indexes:**
```sql
-- Critical for unread count query
CREATE INDEX idx_notification_reads_staff_notif 
ON notification_reads(staff_id, notification_id);

CREATE INDEX idx_notification_shop_targets_shop 
ON notification_shop_targets(shop_id, notification_id);

CREATE INDEX idx_notification_staff_targets_staff 
ON notification_staff_targets(staff_id, notification_id);

CREATE INDEX idx_notifications_expires 
ON notifications(expires_at) WHERE expires_at IS NOT NULL;
```

---

## ✅ REQUIRED CHANGES

### **Priority 1 (CRITICAL):**
1. ✅ Optimize unread count query (use COUNT instead of fetching records)
2. ✅ Add Redis caching (30s TTL)
3. ✅ Add rate limit (120 req/min)
4. ✅ Add database indexes

### **Priority 2 (RECOMMENDED):**
1. ✅ Add pagination to list endpoint
2. ✅ Cache stats endpoint (60s TTL)
3. ✅ Reduce default limit from 50 to 20

---

## 📈 Final Load Estimate

### **With Optimizations:**
```
Unread Count:
- Total: 240,000 req/min
- Cache hits: 216,000 req/min (90%)
- Database: 24,000 req/min
- Per instance: 8,000 DB queries/min (133 req/sec)

List Endpoint:
- Total: ~10,000 req/min (when users check)
- Per instance: 3,333 req/min (55 req/sec)

Total Notifications Load:
- Per instance: ~11,333 DB queries/min (188 req/sec)
- Combined with other modules: ~573 req/sec
- Capacity: 500 req/sec
- Result: NEED 4 INSTANCES (not 3) ⚠️
```

---

## 🚨 FINAL VERDICT

### **Current State:** ❌ NOT PRODUCTION READY
- Unread count will crash database
- No caching on high-frequency endpoint
- No rate limiting

### **With Fixes:** ✅ PRODUCTION READY
- Optimized queries
- Redis caching (90% hit rate)
- Rate limiting in place
- **Requires 4 Railway instances (not 3)**

---

## 💰 Cost Impact

### **3 Instances (Current Plan):**
```
Load: 573 req/sec per instance
Capacity: 500 req/sec
Result: OVERLOAD ❌
```

### **4 Instances (Recommended):**
```
Load: 430 req/sec per instance
Capacity: 500 req/sec
Headroom: 14%
Cost: $80/month (vs $60 for 3)
Result: STABLE ✅
```

**Additional $20/month for stability**
