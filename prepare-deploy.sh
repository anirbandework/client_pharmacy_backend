#!/bin/bash

# Quick Deployment Setup Script
# Run this before deploying to Railway

echo "🚀 Pharmacy Management System - Deployment Prep"
echo "================================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Check if .gitignore exists
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local
.env.production

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
celerybeat-schedule

# Testing
.pytest_cache/
.coverage
htmlcov/

# Deployment
railway.json.bak
EOF
    echo "✅ .gitignore created"
else
    echo "✅ .gitignore exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x railway-start.sh
chmod +x start.sh
echo "✅ Scripts are executable"

# Check requirements.txt
if [ -f requirements.txt ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Generate a secure SECRET_KEY
echo ""
echo "🔐 Generate a secure SECRET_KEY for production:"
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
echo ""

echo "================================================"
echo "✅ Deployment prep complete!"
echo ""
echo "Next steps:"
echo "1. Copy the SECRET_KEY above"
echo "2. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Ready for deployment'"
echo "   git remote add origin YOUR_GITHUB_REPO_URL"
echo "   git push -u origin main"
echo ""
echo "3. Follow DEPLOYMENT_GUIDE.md for Railway setup"
echo "================================================"
