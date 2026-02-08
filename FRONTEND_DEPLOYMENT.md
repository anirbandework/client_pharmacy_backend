# 🎨 Frontend Deployment Guide (Vercel)

Quick guide to deploy your React + Vite frontend to Vercel.

**✅ Backend is Live!** Your Railway backend URL:
`https://web-production-3ca8.up.railway.app`

---

## 📁 Files to Create in Your Frontend Project

### 1. Create `vercel.json` (in frontend root)

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

### 2. Create `.env.production` (in frontend root)

```env
VITE_API_URL=https://web-production-3ca8.up.railway.app
```

### 3. Update Your API Configuration

Create or update `src/config/api.js`:

```javascript
// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiConfig = {
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// Example API client
export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'GET',
      headers: apiConfig.headers,
      credentials: 'include', // For cookies/auth
    });
    return response.json();
  },
  
  post: async (endpoint, data) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: apiConfig.headers,
      credentials: 'include',
      body: JSON.stringify(data),
    });
    return response.json();
  },
  
  // Add PUT, DELETE, etc. as needed
};
```

### 4. Update Your API Calls

Replace hardcoded URLs:

```javascript
// ❌ Before
fetch('http://localhost:8000/api/customers')

// ✅ After
import { api } from './config/api';
api.get('/api/customers')
```

---

## 🚀 Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Easiest)

1. **Push to GitHub**
   ```bash
   cd your-frontend-folder
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. **Go to Vercel**
   - Visit https://vercel.com
   - Click "Add New" → "Project"
   - Import your frontend repository

3. **Configure Project**
   - Framework Preset: **Vite** (auto-detected)
   - Root Directory: `./` (or your frontend folder)
   - Build Command: `npm run build` (auto-filled)
   - Output Directory: `dist` (auto-filled)

4. **Add Environment Variable**
   - Click "Environment Variables"
   - Add: `VITE_API_URL` = `https://web-production-3ca8.up.railway.app`
   - Apply to: Production, Preview, Development

5. **Deploy**
   - Click "Deploy"
   - Wait 1-2 minutes
   - Your site is live! 🎉

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy to production
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? pharmacy-frontend
# - Directory? ./
# - Override settings? No
```

---

## 🔧 Post-Deployment Configuration

### 1. Get Your Vercel URL

After deployment, you'll get a URL like:
```
https://pharmacy-frontend.vercel.app
```

### 2. Update Backend CORS

Go to your backend code and update `main.py`:

```python
allowed_origins = [
    "http://localhost:5173",
    "https://client-pharmacy-frontend.vercel.app",  # Your actual Vercel URL
]
```

**Already done!** ✅ Your backend is configured with this URL.

If you change domains, commit and push - Railway will auto-deploy!

### 3. Test the Connection

Open your Vercel URL and check:
- [ ] Page loads correctly
- [ ] API calls work
- [ ] Login works
- [ ] No CORS errors in browser console

---

## 🎯 Environment Variables Reference

### Development (.env.development)
```env
VITE_API_URL=http://localhost:8000
```

### Production (Vercel Dashboard)
```env
VITE_API_URL=https://web-production-3ca8.up.railway.app
```

### Accessing in Code
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

---

## 🔄 Continuous Deployment

### Automatic Deployments

Vercel automatically deploys on every push:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Vercel automatically builds and deploys!
```

### Preview Deployments

Every branch and PR gets a preview URL:
- `main` branch → Production
- Other branches → Preview URLs
- Pull requests → Preview URLs

---

## 🎨 Custom Domain (Optional)

### Add Your Domain

1. **Buy a domain** (Namecheap, GoDaddy, etc.)

2. **In Vercel Dashboard**:
   - Go to Project Settings → Domains
   - Click "Add"
   - Enter your domain: `yourpharmacy.com`

3. **Update DNS Records**:
   - Add records shown by Vercel
   - Wait 24-48 hours for propagation

4. **SSL Certificate**:
   - Vercel automatically provisions SSL
   - Your site will be `https://yourpharmacy.com`

---

## 📊 Monitoring & Analytics

### Built-in Analytics

Vercel provides free analytics:
- Page views
- Unique visitors
- Top pages
- Performance metrics

Access at: Project → Analytics

### Performance Monitoring

Check Web Vitals:
- Largest Contentful Paint (LCP)
- First Input Delay (FID)
- Cumulative Layout Shift (CLS)

---

## 🐛 Troubleshooting

### Build Fails

**Check build logs**:
1. Go to Vercel Dashboard → Deployments
2. Click failed deployment
3. Check logs for errors

**Common issues**:
```bash
# Missing dependencies
npm install

# Type errors
npm run build  # Test locally first

# Environment variables
# Make sure VITE_API_URL is set in Vercel
```

### API Calls Fail

**CORS Error**:
- Check backend CORS includes your Vercel URL
- Check browser console for exact error

**Wrong API URL**:
```javascript
// Debug: Log the API URL
console.log('API URL:', import.meta.env.VITE_API_URL);
```

### Page Not Found (404)

Make sure `vercel.json` has the rewrite rule:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 💡 Pro Tips

### 1. Preview Deployments

Test changes before production:
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and push
git push origin feature/new-feature

# Vercel creates preview URL automatically!
```

### 2. Environment-Specific Code

```javascript
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;

if (isDev) {
  console.log('Development mode');
}
```

### 3. Optimize Build

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
};
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] `vercel.json` created
- [ ] `.env.production` configured
- [ ] API configuration updated
- [ ] All API calls use environment variable
- [ ] Code pushed to GitHub

### Deployment
- [ ] Project created in Vercel
- [ ] Environment variables set
- [ ] Build successful
- [ ] Site accessible

### Post-Deployment
- [ ] Backend CORS updated
- [ ] API calls working
- [ ] Login working
- [ ] No console errors
- [ ] Custom domain configured (optional)

---

## 🎉 You're Live!

Your frontend is now deployed on Vercel!

**Free Forever Includes**:
- Unlimited deployments
- 100GB bandwidth/month
- Global CDN
- Automatic SSL
- Preview deployments

**Your URLs**:
- Backend API: `https://web-production-3ca8.up.railway.app`
- API Docs: `https://web-production-3ca8.up.railway.app/docs`
- Frontend: `https://your-app.vercel.app` (after deployment)

Need help? Check Vercel docs: https://vercel.com/docs
