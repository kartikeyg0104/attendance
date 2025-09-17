# Quick Fix for Backend Connection Issue

## The Problem
Your frontend at `https://attendance-frontend-mkwg.onrender.com` cannot connect to the backend at `https://attendance-backend-y0rt.onrender.com`.

## Solution Steps

### 1. Check Backend Status
Visit: https://attendance-backend-y0rt.onrender.com/api/health
- If this returns an error, your backend service is down
- If it works, the issue is CORS or network related

### 2. Backend Service Requirements
Your backend service on Render needs:

**Environment Variables:**
```
FLASK_ENV=production
PORT=5002
ALLOWED_ORIGINS=https://attendance-frontend-mkwg.onrender.com,http://localhost:3000
```

**Build Command:** `pip install -r requirements.txt`
**Start Command:** `python app.py`

### 3. Frontend Configuration
The frontend is correctly configured in `config.ts`:
- Production: `https://attendance-backend-y0rt.onrender.com`
- Development: `http://localhost:5002`

### 4. Quick Fix Options

#### Option A: Redeploy Backend
1. Go to your Render dashboard
2. Find the "attendance-backend" service
3. Click "Manual Deploy" to restart it
4. Check the logs for any errors

#### Option B: Update Backend URL
If the backend URL changed, update `frontend/src/config.ts`:
```typescript
export const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://YOUR-NEW-BACKEND-URL.onrender.com'
  : 'http://localhost:5002';
```

#### Option C: Deploy Fresh Backend
1. Create new web service on Render
2. Connect your GitHub repo
3. Set root directory to `backend`
4. Use the environment variables above

### 5. Test the Fix
After deployment:
1. Visit the backend health check: `YOUR-BACKEND-URL/api/health`
2. Should return: `{"status":"healthy","message":"Face Recognition API is running"}`
3. Refresh your frontend - warning should disappear

### 6. Logs to Check
- Backend service logs on Render
- Browser developer console for network errors
- CORS errors in browser console