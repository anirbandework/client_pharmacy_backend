#!/bin/bash

# Deploy rate limit fix to production

echo "🚀 Deploying rate limit fix to production..."
echo ""
echo "Changes made:"
echo "  ✓ Added /api/auth/staff/me to rate limit skip list"
echo "  ✓ Added /api/auth/admin/me to rate limit skip list"
echo "  ✓ Added /api/rbac/my-permissions to rate limit skip list"
echo ""
echo "This will prevent 429 errors on authentication endpoints."
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Please initialize git first."
    exit 1
fi

# Add changes
git add app/middleware/rate_limit.py

# Commit
git commit -m "fix: Add auth verification endpoints to rate limit skip list

- Skip rate limiting for /api/auth/staff/me
- Skip rate limiting for /api/auth/admin/me  
- Skip rate limiting for /api/rbac/my-permissions
- Prevents 429 errors on login and auth checks"

echo ""
echo "✅ Changes committed!"
echo ""
echo "To deploy to Railway:"
echo "  git push origin main"
echo ""
echo "Or if you have Railway CLI:"
echo "  railway up"
