#!/bin/bash

echo "🚀 Building Face Attendance System for Production..."

# Create production build of frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "📋 Production build completed!"
echo ""
echo "📂 Files ready for deployment:"
echo "  - Backend: ./backend/ (Python Flask)"
echo "  - Frontend: ./frontend/build/ (Static files)"
echo ""
echo "🌐 Deployment options:"
echo "  - Docker: docker-compose up --build"
echo "  - Static hosting: Deploy frontend/build/ to Netlify/Vercel"
echo "  - Server hosting: Deploy backend/ to Heroku/Railway/DigitalOcean"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"