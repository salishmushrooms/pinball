# 🔄 Quick Sync Checklist

Use this checklist when switching between computers.

---

## 📤 Before Leaving This Computer (Mini)

```bash
# 1. Check what changed
git status

# 2. Stage and commit
git add .
git commit -m "Your descriptive message here"

# 3. Push to remote
git push origin main
```

✅ Done! Your code changes are synced.

---

## 📥 When Starting on Other Computer (Laptop)

```bash
# 1. Navigate to project
cd /path/to/MNP

# 2. Pull latest changes
git pull origin main

# 3. Check if dependencies changed
git diff HEAD@{1} requirements.txt package.json

# 4. If requirements.txt changed:
conda activate mnp
pip install -r requirements.txt

# 5. If package.json changed:
cd frontend
npm install
cd ..

# 6. Database: Choose ONE option below
```

### Option A: Quick Reload (Recommended - 30 seconds)

```bash
# Reload from source data
python etl/load_season.py --season 22
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22
```

### Option B: Check If Database Already Has Data

```bash
# Quick check
psql mnp_analyzer -c "SELECT COUNT(*) FROM scores;"

# If it returns ~11,000, you're good!
# If it returns 0 or error, use Option A
```

---

## 🚀 Start Development

```bash
# Terminal 1: Backend
conda activate mnp
python -m uvicorn api.main:app --reload

# Terminal 2: Frontend (new terminal)
cd frontend
npm run dev
```

Open http://localhost:3000 🎉

---

## ⚠️ Important Notes

1. **Database is LOCAL** - Each computer has its own database
2. **Always git pull before starting work**
3. **Always git push when done**
4. **Frontend .env.local** - Create manually on each computer if missing:
   ```bash
   cd frontend
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

---

## 🆘 Quick Fixes

### "Database doesn't exist"
```bash
cd schema
./setup_database.sh
cd ..
python etl/load_season.py --season 22
```

### "Module not found" (Python)
```bash
conda activate mnp
pip install -r requirements.txt
```

### "Module not found" (Frontend)
```bash
cd frontend
npm install
```

### "API connection refused"
```bash
# Start backend in separate terminal
python -m uvicorn api.main:app --reload
```

---

**See [WORKING_ACROSS_COMPUTERS.md](WORKING_ACROSS_COMPUTERS.md) for detailed guide**
