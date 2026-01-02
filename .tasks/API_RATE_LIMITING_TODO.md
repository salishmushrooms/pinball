# API Rate Limiting - Recommendation

**Status**: Not currently implemented
**Priority**: Medium (before significant public usage)
**Created**: 2026-01-02

## Current State

The MNP Analyzer API currently has:
- ✅ Caching middleware (1 week cache for GET requests)
- ✅ CORS configured (allow all origins)
- ✅ Pagination limits on list endpoints (max 500 results)
- ❌ **No rate limiting middleware**

## Why Rate Limiting?

With the production API URL public (https://pinball-production.up.railway.app), rate limiting prevents:
- Abuse or DoS attacks
- Excessive costs on Railway Hobby plan
- One user monopolizing resources
- Accidental runaway scripts

## Recommended Solution

Use **slowapi** (FastAPI-compatible rate limiting):

```bash
pip install slowapi
```

### Implementation Example

```python
# In api/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add rate limit decorator to endpoints
@app.get("/players")
@limiter.limit("60/minute")  # 60 requests per minute per IP
async def get_players(...):
    ...
```

### Suggested Rate Limits

**Tier 1 - List/Search Endpoints** (most expensive):
- 30 requests/minute
- Examples: `/players`, `/machines`, `/teams`

**Tier 2 - Detail Endpoints** (moderate):
- 60 requests/minute
- Examples: `/players/{key}`, `/machines/{key}`

**Tier 3 - Lightweight Endpoints** (cheap):
- 120 requests/minute
- Examples: `/health`, `/seasons`, `/`

**Tier 4 - Heavy Computation** (very expensive):
- 10 requests/minute
- Examples: `/matchups/analyze`, `/predictions/machine`

## Alternative: Railway Built-in Protection

Railway provides some DDoS protection, but it's not customizable per-endpoint.

## Monitoring

Once implemented, track:
- Rate limit hits (429 responses)
- Top IPs by request count
- Endpoint usage patterns

Railway's metrics dashboard shows:
- Total requests
- Response times
- Memory/CPU usage

## Timeline

- **Before Beta**: Optional (low public usage expected)
- **Before v1.0**: Recommended
- **If costs spike**: Critical

## Resources

- [slowapi documentation](https://github.com/laurents/slowapi)
- [FastAPI rate limiting guide](https://fastapi.tiangolo.com/advanced/middleware/)
- [Railway metrics dashboard](https://railway.app)

---

**Decision**: Defer until usage patterns emerge, but implement before significant public adoption.
