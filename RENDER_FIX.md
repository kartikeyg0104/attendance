# Render Deployment Fix Guide

## Current Issue
The frontend is deployed but cannot connect to the backend. The error "Backend connection lost" indicates the backend API is not accessible.

## Solution

### 1. Backend Deployment
Your backend should be deployed as a separate service on Render with this URL:
`https://attendance-backend-y0rt.onrender.com`

### 2. Environment Variables
Make sure your backend service on Render has these environment variables:

```
FLASK_ENV=production
PORT=5002
ALLOWED_ORIGINS=https://attendance-frontend-mkwg.onrender.com
```

### 3. Frontend Configuration
The frontend is already configured correctly in `config.ts`:
- Production: `https://attendance-backend-y0rt.onrender.com`
- Development: `http://localhost:5002`

### 4. Render Service Configuration

#### Backend Service (render.yaml):
```yaml
services:
  - type: web
    name: attendance-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PORT
        value: 5002
      - key: ALLOWED_ORIGINS
        value: https://attendance-frontend-mkwg.onrender.com
```

#### Frontend Service:
```yaml
  - type: web
    name: attendance-frontend
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm run start
    envVars:
      - key: NODE_ENV
        value: production
```

### 5. Quick Fix Steps

1. **Check Backend Status**: Visit `https://attendance-backend-y0rt.onrender.com/api/health`
2. **If backend is down**: Redeploy the backend service on Render
3. **Check Environment Variables**: Ensure all required env vars are set
4. **Verify CORS**: Make sure ALLOWED_ORIGINS includes your frontend domain

### 6. Test Backend Connection
Visit: `https://attendance-backend-y0rt.onrender.com/api/health`
Expected response: `{"status": "healthy", "message": "Face Recognition API is running"}`

If this returns an error, the backend service needs to be fixed/redeployed.