# Authentication Issues Fix

## Problems Identified

### 1. 429 Too Many Requests
**Cause**: Frontend is calling `/api/auth/staff/me` and `/api/rbac/my-permissions` frequently (likely on every route change or component mount), hitting rate limits.

**Solution**: Added these endpoints to the rate limit skip list in `app/middleware/rate_limit.py`

### 2. 401 Unauthorized  
**Possible Causes**:
- JWT token expired (current expiry: 24 hours)
- Token not being sent correctly from frontend
- CORS issues preventing credentials from being sent
- Token stored in wrong format in frontend

## Changes Made

### File: `app/middleware/rate_limit.py`

Added to `SKIP_RATE_LIMIT` list:
```python
"/api/auth/staff/me",
"/api/auth/admin/me",
"/api/rbac/my-permissions"
```

These endpoints are now exempt from rate limiting since they're called frequently for auth verification.

## Deployment Steps

1. **Commit changes**:
   ```bash
   git add app/middleware/rate_limit.py
   git commit -m "fix: Skip rate limiting for auth verification endpoints"
   ```

2. **Push to Railway**:
   ```bash
   git push origin main
   ```

3. **Verify deployment**:
   - Check Railway logs for successful deployment
   - Test login on frontend
   - Check browser console for errors

## Frontend Checks Needed

If 401 errors persist after deployment, check frontend:

### 1. Token Storage
```javascript
// Check if token is stored correctly
localStorage.getItem('token') // or sessionStorage
```

### 2. Token Format in Requests
```javascript
// Should be:
headers: {
  'Authorization': `Bearer ${token}`
}
```

### 3. Token Expiration Handling
```javascript
// Frontend should handle 401 by:
// 1. Clearing stored token
// 2. Redirecting to login
// 3. Showing appropriate message
```

### 4. CORS Credentials
```javascript
// If using fetch:
fetch(url, {
  credentials: 'include', // or 'same-origin'
  headers: {
    'Authorization': `Bearer ${token}`
  }
})

// If using axios:
axios.defaults.withCredentials = true;
```

## Testing After Deployment

1. **Clear browser cache and cookies**
2. **Login fresh** with valid credentials
3. **Check Network tab** in browser DevTools:
   - Verify Authorization header is present
   - Check response status codes
   - Look for CORS errors in console

4. **Check Railway logs**:
   ```bash
   railway logs
   ```
   Look for authentication errors or rate limit messages

## Additional Recommendations

### Increase Token Expiry (Optional)
If users are getting logged out too frequently, increase token expiry in `modules/auth/service.py`:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days instead of 1 day
```

### Add Token Refresh Endpoint (Recommended)
Implement a `/api/auth/refresh` endpoint to get new tokens without re-login:

```python
@router.post("/auth/refresh")
def refresh_token(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate new token with same user data
    token_data = {
        "user_id": current_user["token_data"].user_id,
        "user_type": current_user["token_data"].user_type,
        # ... other fields
    }
    new_token = AuthService.create_access_token(token_data)
    return {"access_token": new_token, "token_type": "bearer"}
```

### Frontend Token Refresh Logic
```javascript
// Call refresh endpoint before token expires
// Or on 401 error, try refresh once before logout
```

## Monitoring

After deployment, monitor:
- Login success rate
- 401 error frequency  
- 429 error frequency
- User session duration

## Rollback Plan

If issues persist:
```bash
git revert HEAD
git push origin main
```

Then investigate frontend token handling before retrying.
