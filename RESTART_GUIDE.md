# MNP App Restart Guide

Quick reference for restarting services to apply updates.

---

## 🚀 Quick Restart (Most Common)

If you've made changes to frontend components or pages:

```bash
# Stop all services
# Press Ctrl+C in each terminal window running services

# Restart frontend (from /Users/test_1/Pinball/MNP/pinball/frontend)
cd /Users/test_1/Pinball/MNP/pinball/frontend
npm run dev
```

---

## 📋 Full Service Restart

### 1. **Check What's Running**

```bash
# From project root
lsof -ti:3000,8000
```

If you see process IDs, services are running.

---

### 2. **Stop All Services**

**Option A: If running in terminals**
- Press `Ctrl+C` in each terminal window

**Option B: Force kill processes**
```bash
# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9

# Kill API (port 8000)
lsof -ti:8000 | xargs kill -9
```

---

### 3. **Restart Frontend**

```bash
cd /Users/test_1/Pinball/MNP/pinball/frontend
npm run dev
```

**Expected output:**
```
> frontend@0.1.0 dev
> next dev

  ▲ Next.js 16.0.4
  - Local:        http://localhost:3000

Ready in Xms
```

**Access at:** http://localhost:3000

---

### 4. **Restart API** (If needed)

```bash
cd /Users/test_1/Pinball/MNP/pinball

# Activate conda environment
source /Users/test_1/opt/anaconda3/bin/activate mnp

# Start API
uvicorn api.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Access at:** http://localhost:8000/docs

---

## 🔍 Troubleshooting

### Frontend Won't Start

**Problem:** Port 3000 already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Try starting again
cd frontend && npm run dev
```

**Problem:** Module not found errors
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

### API Won't Start

**Problem:** Port 8000 already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Try starting again
source /Users/test_1/opt/anaconda3/bin/activate mnp
uvicorn api.main:app --reload --port 8000
```

**Problem:** Conda environment not found
```bash
# Check available environments
conda env list

# If 'mnp' is not listed, create it
conda create -n mnp python=3.11
source /Users/test_1/opt/anaconda3/bin/activate mnp
pip install -r requirements.txt
```

---

### Database Connection Issues

**Problem:** API can't connect to PostgreSQL

```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it
brew services start postgresql@15

# Check connection
psql -U mnp_user -d mnp_db -c "SELECT 1;"
```

---

## 🎯 When to Restart What

| You Changed... | Restart This |
|----------------|--------------|
| React component in `frontend/components/` | Frontend only |
| Page in `frontend/app/` | Frontend only |
| CSS in `frontend/app/globals.css` | Frontend only |
| API endpoint in `api/routers/` | API only (or just wait - auto-reload) |
| Database schema | Database + API |
| Environment variables | Both frontend and API |
| Dependencies (package.json) | Frontend + reinstall |
| Dependencies (requirements.txt) | API + reinstall |

---

## 📝 Common Workflows

### After Migrating a Page Component

```bash
# 1. Stop frontend (Ctrl+C in terminal)
# 2. Restart
cd /Users/test_1/Pinball/MNP/pinball/frontend
npm run dev

# 3. Open browser and hard refresh
# Chrome/Firefox: Cmd+Shift+R
# Safari: Cmd+Option+R
```

---

### After Changing Design System (globals.css)

```bash
# Usually no restart needed - Next.js hot reloads CSS
# But if changes don't appear:

# 1. Stop frontend (Ctrl+C)
# 2. Clear Next.js cache
cd /Users/test_1/Pinball/MNP/pinball/frontend
rm -rf .next

# 3. Restart
npm run dev
```

---

### After Installing New npm Package

```bash
cd /Users/test_1/Pinball/MNP/pinball/frontend

# 1. Install package
npm install <package-name>

# 2. Restart (Ctrl+C then)
npm run dev
```

---

### Clean Restart (Nuclear Option)

If something is really broken:

```bash
# 1. Kill all services
lsof -ti:3000,8000 | xargs kill -9

# 2. Clean frontend
cd /Users/test_1/Pinball/MNP/pinball/frontend
rm -rf .next node_modules
npm install
npm run dev

# 3. In new terminal, restart API
cd /Users/test_1/Pinball/MNP/pinball
source /Users/test_1/opt/anaconda3/bin/activate mnp
uvicorn api.main:app --reload --port 8000
```

---

## 🌐 Browser Cache

After restarting, always do a **hard refresh** in your browser:

- **Chrome/Firefox:** `Cmd+Shift+R`
- **Safari:** `Cmd+Option+R`

Or open DevTools and right-click the refresh button → "Empty Cache and Hard Reload"

---

## 📍 Service URLs

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API Base:** http://localhost:8000/api

---

## ⚡ Pro Tips

1. **Use separate terminal windows** for frontend and API so you can see logs
2. **Keep API running** - it auto-reloads when you change code
3. **Frontend hot reloads** - you usually don't need to restart
4. **Hard refresh browser** after changes to see updates
5. **Check terminal logs** if something doesn't work - errors show there

---

**Last Updated:** 2025-11-26
