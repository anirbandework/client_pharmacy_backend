# Frontend Error Handling Guide

## Backend Changes
The backend now returns user-friendly error messages in this format:

```json
{
  "error": "Invalid Indian phone number",
  "field": "phone",
  "message": "Invalid Indian phone number"
}
```

## Frontend Implementation Examples

### React/TypeScript Example

```typescript
// API utility function
async function sendOTP(phone: string, password: string) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/super-admin/send-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phone, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      // Handle validation errors (422)
      if (response.status === 422) {
        throw new Error(errorData.error || errorData.message || 'Validation error');
      }
      
      // Handle other errors (400, 401, etc.)
      throw new Error(errorData.detail || 'An error occurred');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
}

// Component usage
function SuperAdminLogin() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await sendOTP(phone, password);
      // Handle success
      console.log('OTP sent:', result.message);
    } catch (err) {
      // Display error to user
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSendOTP}>
      <input
        type="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="Phone Number"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      
      {error && (
        <div className="error-message" style={{ color: 'red' }}>
          {error}
        </div>
      )}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Sending...' : 'Send OTP'}
      </button>
    </form>
  );
}
```

### Axios Example

```typescript
import axios from 'axios';

// Create axios instance with interceptor
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      // Handle validation errors (422)
      if (status === 422) {
        const message = data.error || data.message || 'Validation error';
        return Promise.reject(new Error(message));
      }
      
      // Handle other errors
      const message = data.detail || data.message || 'An error occurred';
      return Promise.reject(new Error(message));
    }
    
    return Promise.reject(error);
  }
);

// Usage
async function sendOTP(phone: string, password: string) {
  try {
    const response = await api.post('/auth/super-admin/send-otp', {
      phone,
      password,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}
```

### React Hook Form with Zod Validation (Recommended)

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Define validation schema
const loginSchema = z.object({
  phone: z.string()
    .regex(/^\+?91\d{10}$/, 'Invalid Indian phone number')
    .transform(val => {
      // Normalize phone number
      let phone = val.replace(/[^\d+]/g, '').replace('+', '');
      if (!phone.startsWith('91') && phone.length === 10) {
        phone = '91' + phone;
      }
      return '+' + phone;
    }),
  password: z.string()
    .min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

function SuperAdminLogin() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/super-admin/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        if (response.status === 422) {
          // Set field-specific error
          const field = errorData.field || 'root';
          const message = errorData.error || errorData.message;
          setError(field as any, { message });
        } else {
          setError('root', { message: errorData.detail || 'An error occurred' });
        }
        return;
      }

      const result = await response.json();
      console.log('Success:', result);
    } catch (error) {
      setError('root', { message: 'Network error. Please try again.' });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input
          {...register('phone')}
          type="tel"
          placeholder="Phone Number (+919876543210)"
        />
        {errors.phone && (
          <span className="error">{errors.phone.message}</span>
        )}
      </div>

      <div>
        <input
          {...register('password')}
          type="password"
          placeholder="Password"
        />
        {errors.password && (
          <span className="error">{errors.password.message}</span>
        )}
      </div>

      {errors.root && (
        <div className="error-message">{errors.root.message}</div>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending...' : 'Send OTP'}
      </button>
    </form>
  );
}
```

## Phone Number Format

The backend expects phone numbers in the format: `+919876543210`

Valid inputs that will be normalized:
- `9876543210` → `+919876543210`
- `+919876543210` → `+919876543210`
- `919876543210` → `+919876543210`

Invalid inputs:
- `+919383169654111` (too many digits)
- `123456` (too few digits)
- `+1234567890` (wrong country code)

## Error Types

### 422 Unprocessable Entity (Validation Error)
```json
{
  "error": "Invalid Indian phone number",
  "field": "phone",
  "message": "Invalid Indian phone number"
}
```

### 400 Bad Request (Business Logic Error)
```json
{
  "detail": "Phone number not registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid credentials"
}
```

## Best Practices

1. **Client-side validation**: Validate phone numbers on the frontend before sending to backend
2. **User-friendly messages**: Display clear, actionable error messages
3. **Field highlighting**: Highlight the specific field with the error
4. **Format hints**: Show phone number format examples in placeholders
5. **Auto-formatting**: Consider auto-formatting phone numbers as user types
