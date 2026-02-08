# 🚀 Deployment Guide - Railway + Vercel

Complete guide to deploy your Pharmacy Management System for 500 users.

**Total Cost: $20/month**
- Backend (Railway Pro): $20/month
- Frontend (Vercel): FREE

---

## 📋 Prerequisites

1. GitHub account
2. Railway account (https://railway.app)
3. Vercel account (https://vercel.com)
4. Your code pushed to GitHub

---

## 🔧 Part 1: Backend Deployment (Railway)

### Step 1: Push Code to GitHub

```bash
cd "/Users/anirbande/Desktop/client backend"
git init
git add .
git commit -m "Initial commit - ready for deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your backend repository**

### Step 3: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "PostgreSQL"**
3. Railway auto-creates `DATABASE_URL` variable

### Step 4: Add Redis

1. Click **"+ New"** again
2. Select **"Database" → "Redis"**
3. Railway auto-creates `REDIS_URL` variable

### Step 5: Configure Environment Variables

In Railway project settings, add these variables:

```env
# Auto-configured by Railway (don't add manually)
DATABASE_URL=postgresql://...  (auto-set)
REDIS_URL=redis://...          (auto-set)
PORT=8000                      (auto-set)

# Add these manually:
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REMINDER_DAYS_BEFORE=5
CASH_DIFFERENCE_LIMIT=100.0
GEMINI_API_KEY=AIzaSyAua0xL2ASGli-K07HAOvlnPMurlU2oAuk

# WhatsApp (optional)
WHATSAPP_API_URL=https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT/Messages.json
WHATSAPP_TOKEN=your_token_here
WHATSAPP_FROM_NUMBER=+14155238886
```

### Step 6: Upgrade to Pro Plan

1. Go to **Project Settings → Plan**
2. Select **"Pro Plan" ($20/month)**
3. This gives you:
   - 8GB RAM
   - 8 vCPU
   - Handles 500 concurrent users
   - Always-on workers

### Step 7: Deploy!

Railway will automatically:
- Install dependencies
- Run migrations
- Start Celery workers
- Start FastAPI server

**Your API will be live at**: `https://your-app.railway.app`

### Step 8: Initialize Database

After first deployment, run setup:

```bash
# In Railway project, go to "Settings" → "Deploy"
# Add this as a one-time command:
python setup_auth.py
```

Or use Railway CLI:
```bash
railway run python setup_auth.py
```

---

## 🎨 Part 2: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

In your React + Vite project, create `.env.production`:

```env
VITE_API_URL=https://your-app.railway.app
```

### Step 2: Update API Calls

Make sure your frontend uses the environment variable:

```javascript
// src/config/api.js or similar
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_URL,
  // ... your API methods
};
```

### Step 3: Create `vercel.json`

In your frontend root:

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

### Step 4: Deploy to Vercel

**Option A: Via Vercel Dashboard**
1. Go to https://vercel.com
2. Click **"Add New" → "Project"**
3. Import your frontend GitHub repo
4. Vercel auto-detects Vite
5. Add environment variable:
   - `VITE_API_URL` = `https://your-app.railway.app`
6. Click **"Deploy"**

**Option B: Via CLI**
```bash
cd your-frontend-folder
npm install -g vercel
vercel login
vercel --prod
```

**Your frontend will be live at**: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

After getting your Vercel URL, update backend `main.py`:

```python
allowed_origins = [
    "http://localhost:5173",
    "https://your-app.vercel.app",  # Add your actual Vercel URL
]
```

Commit and push - Railway auto-deploys!

---

## 🔒 Part 3: Security Checklist

### Backend (Railway)

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Update admin password after first login
- [ ] Remove test credentials
- [ ] Enable Railway's built-in DDoS protection
- [ ] Set up Railway's monitoring

### Frontend (Vercel)

- [ ] Add your production domain to CORS
- [ ] Enable Vercel's security headers
- [ ] Set up custom domain (optional)
- [ ] Configure Vercel Analytics (optional)

---

## 📊 Part 4: Monitoring & Maintenance

### Railway Dashboard

Monitor:
- CPU usage
- Memory usage
- Request count
- Error logs

Access logs:
```bash
railway logs
```

### Vercel Dashboard

Monitor:
- Page views
- Build status
- Deployment history
- Performance metrics

---

## 🔄 Part 5: Continuous Deployment

### Automatic Deployments

Both Railway and Vercel auto-deploy on git push:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Railway and Vercel automatically deploy!
```

### Rollback if Needed

**Railway**: Go to Deployments → Select previous → Redeploy
**Vercel**: Go to Deployments → Select previous → Promote to Production

---

## 🧪 Part 6: Testing Production

### Test Backend

```bash
# Health check
curl https://your-app.railway.app/health

# API docs
open https://your-app.railway.app/docs

# Test login
curl -X POST https://your-app.railway.app/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@pharmacy.com","password":"admin123"}'
```

### Test Frontend

1. Open `https://your-app.vercel.app`
2. Test login
3. Test API calls
4. Check browser console for errors

---

## 💡 Part 7: Custom Domains (Optional)

### Add Custom Domain to Railway

1. Go to Project Settings → Domains
2. Click "Add Domain"
3. Enter your domain (e.g., `api.yourpharmacy.com`)
4. Add DNS records as shown

### Add Custom Domain to Vercel

1. Go to Project Settings → Domains
2. Click "Add"
3. Enter your domain (e.g., `yourpharmacy.com`)
4. Add DNS records as shown

---

## 🆘 Troubleshooting

### Backend Issues

**Problem**: Database connection fails
```bash
# Check DATABASE_URL is set
railway variables

# Check PostgreSQL is running
railway logs --service postgresql
```

**Problem**: Celery workers not running
```bash
# Check logs
railway logs | grep celery

# Restart deployment
railway up --detach
```

### Frontend Issues

**Problem**: API calls fail (CORS)
- Check backend CORS includes your Vercel URL
- Check `VITE_API_URL` is set correctly

**Problem**: Build fails
```bash
# Check build logs in Vercel dashboard
# Ensure all dependencies are in package.json
```

---

## 📈 Scaling for Growth

### If you exceed 500 users:

**Railway**:
- Upgrade to higher tier ($50/month for 16GB RAM)
- Add horizontal scaling (multiple instances)

**Vercel**:
- Still FREE (handles millions of requests)
- Add Pro plan ($20/month) for advanced analytics

---

## 🎯 Quick Reference

### Important URLs

- **Backend API**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`
- **Frontend**: `https://your-app.vercel.app`
- **Railway Dashboard**: https://railway.app/dashboard
- **Vercel Dashboard**: https://vercel.com/dashboard

### Important Commands

```bash
# Railway CLI
railway login
railway link
railway logs
railway run python setup_auth.py
railway variables

# Vercel CLI
vercel login
vercel --prod
vercel logs
vercel env pull
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Code pushed to GitHub
- [ ] Environment variables documented
- [ ] Database migrations ready
- [ ] Frontend API URL configurable

### Backend (Railway)
- [ ] Project created
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] Environment variables set
- [ ] Upgraded to Pro plan
- [ ] Initial deployment successful
- [ ] Database initialized (setup_auth.py)
- [ ] Health check passes

### Frontend (Vercel)
- [ ] Project created
- [ ] Environment variables set
- [ ] Build successful
- [ ] Deployment successful
- [ ] API calls working

### Post-Deployment
- [ ] Admin password changed
- [ ] CORS updated with production URLs
- [ ] Custom domains configured (optional)
- [ ] Monitoring set up
- [ ] Team notified of URLs

---

## 🎉 You're Live!

Your Pharmacy Management System is now running in production!

**Cost**: $20/month for 500 users
**Uptime**: 99.9%+
**Scalability**: Ready to grow

Need help? Check Railway and Vercel documentation or contact support.
