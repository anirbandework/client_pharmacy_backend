# Frontend Authentication Integration Guide

Complete API documentation for implementing Admin and Staff authentication with OTP.

---

## 📋 Table of Contents
1. [Admin Authentication](#admin-authentication)
2. [Staff Authentication](#staff-authentication)
3. [Error Handling](#error-handling)
4. [React Examples](#react-examples)
5. [State Management](#state-management)

---

## 🔐 Admin Authentication

### 1. Admin Registration

**Endpoint:** `POST /api/auth/admin/register`

**Request:**
```json
{
  "phone": "+919383169659",
  "password": "securePassword123",
  "full_name": "John Doe",
  "email": "john@example.com"  // Optional
}
```

**Response (200):**
```json
{
  "id": 1,
  "phone": "+919383169659",
  "full_name": "John Doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-02-11T10:30:00"
}
```

**Errors:**
- `400`: Phone already registered
- `400`: Invalid phone format
- `400`: Password too short (min 6 chars)

---

### 2. Admin Login (OTP-based) - RECOMMENDED

#### Step 1: Send OTP

**Endpoint:** `POST /api/auth/admin/send-otp`

**Request:**
```json
{
  "phone": "+919383169659",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "message": "OTP sent successfully",
  "expires_in": 300,        // 5 minutes in seconds
  "can_resend_in": 30       // 30 seconds cooldown
}
```

**Errors:**
- `400`: Invalid phone number
- `400`: Invalid password
- `400`: "Please wait X seconds before requesting a new OTP"

#### Step 2: Verify OTP

**Endpoint:** `POST /api/auth/admin/verify-otp`

**Request:**
```json
{
  "phone": "+919383169659",
  "otp_code": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "admin",
  "shop_id": null,
  "shop_name": null
}
```

**Errors:**
- `400`: Invalid OTP code
- `400`: OTP has expired
- `400`: Invalid phone number

---

### 3. Admin Login (Legacy - Email/Password)

**Endpoint:** `POST /api/auth/admin/login`

**Request:**
```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response:** Same as OTP verify response

---

### 4. Get Admin Profile

**Endpoint:** `GET /api/auth/admin/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "phone": "+919383169659",
  "full_name": "John Doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-02-11T10:30:00"
}
```

---

## 👥 Staff Authentication

### 1. Staff Login (OTP-based)

#### Step 1: Send OTP

**Endpoint:** `POST /api/auth/staff/send-otp`

**Request:**
```json
{
  "uuid": "a677dce2-c104-472a-863d-1449b1f8314c",
  "phone": "+919383169659"
}
```

**Response (200):**
```json
{
  "message": "OTP sent successfully",
  "expires_in": 300,
  "can_resend_in": 30
}
```

**Errors:**
- `400`: Invalid UUID
- `400`: Phone number does not match
- `400`: Staff inactive
- `400`: "Please wait X seconds before requesting a new OTP"

#### Step 2: Verify OTP

**Endpoint:** `POST /api/auth/staff/verify-otp`

**Request:**
```json
{
  "uuid": "a677dce2-c104-472a-863d-1449b1f8314c",
  "phone": "+919383169659",
  "otp_code": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "staff",
  "shop_id": 1,
  "shop_name": "Main Pharmacy"
}
```

**Errors:**
- `400`: Invalid OTP code
- `400`: OTP has expired
- `403`: Shop is inactive

---

### 2. Staff Login (Legacy - UUID only)

**Endpoint:** `POST /api/auth/staff/login`

**Request:**
```json
{
  "uuid": "a677dce2-c104-472a-863d-1449b1f8314c"
}
```

**Response:** Same as OTP verify response

---

### 3. Get Staff Profile

**Endpoint:** `GET /api/auth/staff/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 10,
  "shop_id": 1,
  "uuid": "a677dce2-c104-472a-863d-1449b1f8314c",
  "name": "Jane Smith",
  "staff_code": "STAFF001",
  "phone": "+919383169659",
  "email": "jane@example.com",
  "role": "staff",
  "monthly_salary": 25000.0,
  "joining_date": "2024-01-01",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00",
  "last_login": "2024-02-11T15:30:00"
}
```

---

## ⚠️ Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Proceed |
| 400 | Bad Request | Show error message to user |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "Access Denied" |
| 404 | Not Found | Show "Resource not found" |
| 500 | Server Error | Show "Try again later" |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

---

## ⚛️ React Examples

### Admin Login Component

```jsx
import { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/auth';

function AdminLogin() {
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [phone, setPhone] = useState('+91');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);

  // Step 1: Send OTP
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE}/admin/send-otp`, {
        phone,
        password
      });

      setStep('otp');
      setCountdown(30); // Start resend countdown
      
      // Countdown timer
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE}/admin/verify-otp`, {
        phone,
        otp_code: otp
      });

      // Save token
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userType', response.data.user_type);
      
      // Redirect to dashboard
      window.location.href = '/admin/dashboard';

    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResendOTP = () => {
    setOtp('');
    setStep('phone');
  };

  return (
    <div className="login-container">
      <h2>Admin Login</h2>

      {error && <div className="error">{error}</div>}

      {step === 'phone' ? (
        <form onSubmit={handleSendOTP}>
          <input
            type="tel"
            placeholder="Phone (+919383169659)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOTP}>
          <p>OTP sent to {phone}</p>
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          
          {countdown > 0 ? (
            <p>Resend OTP in {countdown}s</p>
          ) : (
            <button type="button" onClick={handleResendOTP}>
              Resend OTP
            </button>
          )}
        </form>
      )}
    </div>
  );
}

export default AdminLogin;
```

---

### Staff Login Component

```jsx
import { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/auth';

function StaffLogin() {
  const [step, setStep] = useState('uuid'); // 'uuid' or 'otp'
  const [uuid, setUuid] = useState('');
  const [phone, setPhone] = useState('+91');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);

  // Step 1: Send OTP
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API_BASE}/staff/send-otp`, {
        uuid,
        phone
      });

      setStep('otp');
      setCountdown(30);
      
      const timer = setInterval(() => {
        setCountdown(prev => prev <= 1 ? 0 : prev - 1);
      }, 1000);

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE}/staff/verify-otp`, {
        uuid,
        phone,
        otp_code: otp
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userType', response.data.user_type);
      localStorage.setItem('shopId', response.data.shop_id);
      localStorage.setItem('shopName', response.data.shop_name);
      
      window.location.href = '/staff/dashboard';

    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Staff Login</h2>

      {error && <div className="error">{error}</div>}

      {step === 'uuid' ? (
        <form onSubmit={handleSendOTP}>
          <input
            type="text"
            placeholder="Staff UUID"
            value={uuid}
            onChange={(e) => setUuid(e.target.value)}
            required
          />
          <input
            type="tel"
            placeholder="Phone (+919383169659)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOTP}>
          <p>OTP sent to {phone}</p>
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          
          {countdown > 0 ? (
            <p>Resend OTP in {countdown}s</p>
          ) : (
            <button type="button" onClick={() => setStep('uuid')}>
              Resend OTP
            </button>
          )}
        </form>
      )}
    </div>
  );
}

export default StaffLogin;
```

---

## 🔧 Axios Configuration

### Setup Interceptor for Auth

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// Add token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 📱 State Management (Context API)

```javascript
// AuthContext.js
import { createContext, useState, useContext, useEffect } from 'react';
import api from './api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');

    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const endpoint = userType === 'admin' ? '/auth/admin/me' : '/auth/staff/me';
      const response = await api.get(endpoint);
      setUser({ ...response.data, userType });
    } catch (error) {
      localStorage.clear();
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

---

## 🎨 UI/UX Best Practices

### OTP Input Component

```jsx
function OTPInput({ value, onChange, length = 6 }) {
  const inputs = useRef([]);

  const handleChange = (index, val) => {
    if (!/^\d*$/.test(val)) return;
    
    const newOTP = value.split('');
    newOTP[index] = val;
    onChange(newOTP.join(''));

    // Auto-focus next input
    if (val && index < length - 1) {
      inputs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !value[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  return (
    <div className="otp-input-group">
      {Array.from({ length }).map((_, index) => (
        <input
          key={index}
          ref={(el) => (inputs.current[index] = el)}
          type="text"
          maxLength={1}
          value={value[index] || ''}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          className="otp-input"
        />
      ))}
    </div>
  );
}
```

---

## 🔒 Security Checklist

- ✅ Store JWT in `localStorage` or `httpOnly` cookies
- ✅ Clear tokens on logout
- ✅ Handle 401 errors globally
- ✅ Validate phone format on frontend
- ✅ Show countdown for OTP resend
- ✅ Disable submit during API calls
- ✅ Clear sensitive data on unmount
- ✅ Use HTTPS in production

---

## 📊 Testing Credentials

### Admin
- Phone: `+919383169659`
- Password: `test@123`

### Staff
- UUID: `a677dce2-c104-472a-863d-1449b1f8314c`
- Phone: `+919383169659`

---

## 🚀 Production Deployment

### Environment Variables

```env
REACT_APP_API_URL=https://your-api.com/api
```

### Update API Base URL

```javascript
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

---

## 📞 Support

For issues or questions:
- Check server logs for OTP codes (development)
- SMS cost: ₹0.25 per OTP
- OTP expires in 5 minutes
- Resend cooldown: 30 seconds

---

**Last Updated:** February 2024
**API Version:** 2.0.0
