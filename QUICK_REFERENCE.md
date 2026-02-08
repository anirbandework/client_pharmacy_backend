# 🚀 Quick Deployment Reference Card

## 📊 Cost Breakdown
- **Backend (Railway Pro)**: $20/month
- **Frontend (Vercel)**: FREE
- **Total**: $20/month for 500 users

---

## 🔗 Important Links

### Services
- Railway: https://railway.app
- Vercel: https://vercel.com
- GitHub: https://github.com

### Documentation
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

---

## ⚡ Quick Commands

### Backend Deployment
```bash
# Prepare for deployment
chmod +x prepare-deploy.sh
./prepare-deploy.sh

# Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# Railway CLI (optional)
npm install -g @railway/cli
railway login
railway link
railway up
```

### Frontend Deployment
```bash
# Deploy to Vercel
npm install -g vercel
vercel login
vercel --prod
```

---

## 🔧 Environment Variables

### Backend (Railway)
```
DATABASE_URL=<auto-set>
REDIS_URL=<auto-set>
PORT=<auto-set>
SECRET_KEY=<generate-new>
GEMINI_API_KEY=AIzaSyAua0xL2ASGli-K07HAOvlnPMurlU2oAuk
```

### Frontend (Vercel)
```
VITE_API_URL=https://your-app.railway.app
```

---

## 🎯 Deployment Checklist

### Backend (Railway)
- [ ] Code on GitHub
- [ ] Railway project created
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] Environment variables set
- [ ] Upgraded to Pro ($20/month)
- [ ] Deployed successfully
- [ ] Run `python setup_auth.py`

### Frontend (Vercel)
- [ ] Code on GitHub
- [ ] `vercel.json` created
- [ ] API config updated
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Deployed successfully
- [ ] Backend CORS updated

---

## 🔍 Testing URLs

### Backend
```bash
# Health check
curl https://your-app.railway.app/health

# API docs
https://your-app.railway.app/docs

# Test endpoint
curl https://your-app.railway.app/api/customers/
```

### Frontend
```
https://your-app.vercel.app
```

---

## 🆘 Quick Troubleshooting

### Backend Issues
```bash
# Check logs
railway logs

# Check environment variables
railway variables

# Restart service
railway up --detach
```

### Frontend Issues
```bash
# Check build logs
vercel logs

# Check environment variables
vercel env ls

# Redeploy
vercel --prod
```

### CORS Issues
Update `main.py`:
```python
allowed_origins = [
    "http://localhost:5173",
    "https://your-app.vercel.app",
]
```

---

## 📈 Scaling Guide

### Current Setup (500 users)
- Railway Pro: $20/month
- 8GB RAM, 8 vCPU
- PostgreSQL included
- Redis included

### If You Grow (1000+ users)
- Railway Scale: $50/month
- 16GB RAM, 16 vCPU
- Or add horizontal scaling

### Vercel
- Always FREE for your use case
- Handles millions of requests
- Global CDN included

---

## 🔐 Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Change admin password after setup
- [ ] Update CORS with actual domains
- [ ] Remove test credentials
- [ ] Enable Railway monitoring
- [ ] Set up error tracking (optional)

---

## 📞 Support

### Railway
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Email: team@railway.app

### Vercel
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support
- Discord: https://vercel.com/discord

---

## 🎉 Success Indicators

### Backend is Working
- ✅ Health check returns 200
- ✅ API docs accessible
- ✅ Database connected
- ✅ Celery workers running

### Frontend is Working
- ✅ Page loads
- ✅ API calls succeed
- ✅ Login works
- ✅ No CORS errors

### System is Production-Ready
- ✅ Both deployed
- ✅ CORS configured
- ✅ Environment variables set
- ✅ Admin password changed
- ✅ Monitoring enabled

---

## 📚 Full Guides

- **Complete Guide**: `DEPLOYMENT_GUIDE.md`
- **Frontend Guide**: `FRONTEND_DEPLOYMENT.md`
- **Environment Template**: `.env.production.template`

---

**Total Time to Deploy**: ~30 minutes
**Monthly Cost**: $20
**Capacity**: 500 concurrent users
**Uptime**: 99.9%+

🚀 You're ready to go live!
