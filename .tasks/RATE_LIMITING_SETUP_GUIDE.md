# Rate Limiting Setup Guide for Railway

**Created**: 2026-01-02
**Status**: Partially implemented (main endpoints done)

---

## ✅ What's Been Done

### 1. Dependencies Added

Added to `requirements.txt`:
```
slowapi==0.1.9
```

### 2. Main App Updated

Modified `api/main.py`:
- ✅ Imported slowapi limiter
- ✅ Initialized limiter with IP-based key function
- ✅ Added rate limit exception handler
- ✅ Added rate limits to root endpoints:
  - `/` - 120 requests/minute
  - `/seasons` - 120 requests/minute
  - `/health` - 300 requests/minute (health checks need high limit)

---

## 🔧 How to Complete Setup

### Step 1: Install Dependencies

```bash
# Local development
pip install -r requirements.txt

# Railway will automatically install on next deploy
```

### Step 2: Add Rate Limits to Router Endpoints

You need to add rate limiting to each router file. Here's the pattern:

#### Example: `api/routers/players.py`

At the top of the file, import the limiter:
```python
from api.main import limiter
```

Then add the decorator to each endpoint:
```python
@router.get("/")
@limiter.limit("30/minute")  # List endpoints - lower limit
async def get_players(request: Request, ...):
    ...

@router.get("/{player_key}")
@limiter.limit("60/minute")  # Detail endpoints - moderate limit
async def get_player(request: Request, player_key: str, ...):
    ...
```

**IMPORTANT**: You must add `request: Request` as the first parameter to all endpoints that use rate limiting.

### Step 3: Suggested Rate Limits by Endpoint Type

#### Tier 1: List/Search Endpoints (30/minute)
- `GET /players` - Player search/list
- `GET /teams` - Team list
- `GET /machines` - Machine list
- `GET /venues` - Venue list

#### Tier 2: Detail Endpoints (60/minute)
- `GET /players/{key}` - Player details
- `GET /teams/{key}` - Team details
- `GET /machines/{key}` - Machine details
- `GET /venues/{key}` - Venue details

#### Tier 3: Stats Endpoints (45/minute)
- `GET /players/{key}/machine-stats` - Player machine stats
- `GET /teams/{key}/machine-stats` - Team machine stats
- `GET /machines/{key}/percentiles` - Machine percentiles

#### Tier 4: Heavy Computation (10/minute)
- `GET /matchups/analyze` - Team matchup predictions
- `GET /predictions/machine` - Machine predictions
- `GET /matchplay/*` - External API calls

#### Tier 5: Lightweight (120/minute)
- `GET /` - Root
- `GET /seasons` - Seasons list
- `GET /health` - Health check

---

## 📝 Router Files to Update

Complete list of routers that need rate limiting:

1. ✅ `api/main.py` - DONE
2. ⏳ `api/routers/players.py` - TODO
3. ⏳ `api/routers/teams.py` - TODO
4. ⏳ `api/routers/machines.py` - TODO
5. ⏳ `api/routers/venues.py` - TODO
6. ⏳ `api/routers/matchups.py` - TODO
7. ⏳ `api/routers/predictions.py` - TODO
8. ⏳ `api/routers/matchplay.py` - TODO
9. ⏳ `api/routers/seasons.py` - TODO

---

## 🚀 Deployment to Railway

Once you've added rate limits to routers:

```bash
# 1. Commit changes
git add requirements.txt api/main.py api/routers/*.py
git commit -m "Add rate limiting to API endpoints"

# 2. Push to GitHub
git push origin main

# 3. Railway will auto-deploy
# Watch the deployment logs in Railway dashboard
```

Railway will:
1. Detect the updated `requirements.txt`
2. Install `slowapi`
3. Restart the API with rate limiting enabled

---

## 🧪 Testing Rate Limits

### Test Locally

```bash
# Start API locally
uvicorn api.main:app --reload --port 8000

# Test rate limit (run this script multiple times rapidly)
for i in {1..35}; do
  curl http://localhost:8000/players
  echo "Request $i"
done

# After 30 requests, you should get:
# HTTP 429 Too Many Requests
# {"error":"Rate limit exceeded: 30 per 1 minute"}
```

### Test on Railway

```bash
# Test production rate limits
for i in {1..35}; do
  curl https://pinball-production.up.railway.app/players
  echo "Request $i"
done
```

---

## 📊 Monitoring Rate Limits

### View Limit Headers

Rate limit info is returned in response headers:

```bash
curl -I https://pinball-production.up.railway.app/

# Headers:
# X-RateLimit-Limit: 120
# X-RateLimit-Remaining: 119
# X-RateLimit-Reset: 1609459200
```

### Railway Metrics

Monitor in Railway dashboard:
- Total requests
- 429 response codes
- Response times
- CPU/Memory usage

---

## ⚙️ Configuration Options

### Customize Key Function

Current: IP-based (`get_remote_address`)

Alternative options:

```python
# 1. Header-based (for API keys)
def get_api_key(request: Request):
    return request.headers.get("X-API-Key", get_remote_address(request))

limiter = Limiter(key_func=get_api_key)

# 2. User-based (if you add auth)
def get_user_id(request: Request):
    return request.state.user.id if hasattr(request.state, 'user') else get_remote_address(request)

limiter = Limiter(key_func=get_user_id)
```

### Storage Backend

Default: In-memory (resets on restart)

For production with multiple instances:

```python
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import redis

# Use Redis for shared rate limit state
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

---

## 🎯 Next Steps

**Minimal (for immediate protection):**
1. ✅ Main endpoints have rate limits
2. Deploy to Railway
3. Monitor usage for 1 week

**Recommended (for complete protection):**
1. Add rate limits to all router endpoints
2. Test locally
3. Deploy to Railway
4. Monitor for 429 errors
5. Adjust limits based on real usage

**Optional (for scaling):**
1. Set up Redis on Railway
2. Use Redis-backed rate limiting
3. Add API key system for higher limits
4. Add custom error messages

---

## 📖 Resources

- [slowapi GitHub](https://github.com/laurents/slowapi)
- [FastAPI Rate Limiting](https://fastapi.tiangolo.com/advanced/middleware/)
- [Railway Redis Plugin](https://docs.railway.app/databases/redis)

---

## 🆘 Troubleshooting

### Error: "Cannot import limiter from api.main"

**Fix**: Move limiter initialization to a separate file:

```python
# api/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Then import in both `main.py` and routers:
```python
from api.rate_limit import limiter
```

### Error: "Missing required parameter: request"

**Fix**: Add `request: Request` to your endpoint function:
```python
# Before
@router.get("/")
def get_players(search: str = None):
    ...

# After
@router.get("/")
@limiter.limit("30/minute")
def get_players(request: Request, search: str = None):
    ...
```

### Rate limits not working after Railway deploy

**Check**:
1. Verify `slowapi` in deployed `requirements.txt`
2. Check Railway build logs for errors
3. Test endpoint returns rate limit headers
4. Ensure Railway isn't behind Cloudflare (which might cache)

---

**Status**: Main endpoints protected, routers need individual attention
