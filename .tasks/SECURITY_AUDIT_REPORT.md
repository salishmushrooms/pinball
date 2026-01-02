# Security Audit Report
**Date**: 2026-01-02
**Purpose**: Pre-public release security assessment

---

## 🚨 CRITICAL ISSUES (Must Fix Before Public)

### 1. **Matchplay API Token Exposed in Git History**

**Severity**: 🔴 CRITICAL

**Issue**: Your Matchplay API token is committed in git history in the `.env` file.

**Exposed Token**: `686|KBAqD8HiHT8rdS3YeCOELTXf6luD0p98RvTHO7npa4898fa7`

**Commits**:
- `2f29238c51faaa9b795029f26ad1e27e0478b86d` (Dec 2, 2025)
- `e39ba29e9c91c9a5fcfa82ceaf0eeb4031e54e3a` (Nov 24, 2025)

**Impact**: Anyone with access to the repository can view this token and make API calls to Matchplay.events on your behalf.

**Required Actions**:
1. ✅ **REVOKE the exposed token IMMEDIATELY** at https://app.matchplay.events (Account Settings → API tokens)
2. ✅ **Generate a new token** and update your local `.env` file
3. ✅ **Remove `.env` from git history** using one of these methods:
   - Option A: BFG Repo-Cleaner (recommended, easier)
   - Option B: git filter-branch (more complex)
4. ✅ **Force push** the cleaned history (⚠️ this rewrites history)
5. ✅ **Verify** `.env` is gitignored going forward

**Commands to Remove from History**:

```bash
# Option A: Using BFG Repo-Cleaner (recommended)
# Install: brew install bfg
bfg --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Option B: Using git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

git reflog expire --expire=now --all
git gc --prune=now --aggressive

# After either option:
git push origin --force --all
git push origin --force --tags
```

---

### 2. **Production URLs Exposed in Documentation**

**Severity**: 🟡 MEDIUM

**Issue**: Production Railway URL is documented in multiple files:
- `.claude/CLAUDE.md`
- `mnp-app-docs/DATABASE_OPERATIONS.md`
- `mnp-app-docs/DEPLOYMENT_CHECKLIST.md`

**Exposed URL**: `https://pinball-production.up.railway.app`

**Impact**:
- Reveals your production infrastructure
- Could enable targeted attacks or scraping
- Exposes API documentation endpoint

**Recommendation**:
- Replace with placeholder URLs in documentation (e.g., `https://your-api.railway.app`)
- OR: Accept that API URL is public (many open-source projects do this)
- Consider rate limiting on production API

**Files to Update** (if replacing):
```
.claude/CLAUDE.md:197
mnp-app-docs/DATABASE_OPERATIONS.md (4 occurrences)
mnp-app-docs/DEPLOYMENT_CHECKLIST.md (3 occurrences)
```

---

## ✅ GOOD FINDINGS (Already Secure)

### 1. **Environment Files Properly Gitignored**

✅ `.gitignore` includes:
```
.env
.env.local
frontend/.env.local
```

✅ Current status: `.env` is in `.gitignore` but was historically tracked (see Critical Issue #1)

### 2. **No Hardcoded Database Credentials**

✅ All database connections use environment variables
✅ Code examples in docs use placeholder passwords (`changeme`, `YOUR_PASSWORD`)

Files checked:
- `etl/config.py` - Uses `os.getenv('DATABASE_URL', ...)`
- `api/services/matchplay_client.py` - Uses `os.getenv('MATCHPLAY_API_TOKEN')`

### 3. **Frontend API URL is Environment-Based**

✅ `frontend/lib/api.ts:52` uses:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

No hardcoded production URLs in code.

### 4. **Deployment Configs Are Clean**

✅ `railway.toml` - No secrets, only build configuration
✅ `vercel.json` - Only framework specification

### 5. **Good .env.example Template**

✅ `.env.example` exists with placeholder values
✅ Includes helpful comments about where to get tokens

---

## ⚠️ RECOMMENDATIONS (Best Practices)

### 1. **Improve .env.example**

Current `.env.example` is good but could include:
```bash
# Frontend (if running locally)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. **Add .env to .gitignore Explicitly**

Current `.gitignore` line 53:
```
.env
```

Consider making it more explicit:
```
# Environment files (NEVER commit these!)
.env
.env.*
!.env.example
```

### 3. **Document Security in README**

Add a security section to README:
```markdown
## Security

- Never commit `.env` files or API tokens
- Production credentials are managed via Railway/Vercel environment variables
- To report security issues, contact: [your contact method]
```

### 4. **Consider Adding Pre-commit Hooks**

Prevent future accidents with [git-secrets](https://github.com/awslabs/git-secrets) or [pre-commit](https://pre-commit.com/):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
```

### 5. **Database Password Consideration**

The example password "changeme" appears in multiple doc files. This is fine for local development, but ensure:
- Production database uses strong password
- Production password is only in Railway environment variables
- No production passwords in any committed files

### 6. **Production URL in Docs - Decision Needed**

**Options**:
1. **Keep it** - Many open-source APIs publish their URLs. Just ensure:
   - Rate limiting is enabled
   - No sensitive data in API responses
   - API has proper error handling

2. **Remove it** - Replace with placeholders:
   - `https://your-api-domain.railway.app`
   - Document that users should replace with their own

**My Recommendation**: Option 1 (keep it) IF:
- ✅ You have rate limiting
- ✅ API only returns public league data
- ✅ No admin/write endpoints exposed

---

## 📋 Pre-Public Checklist

Before making repository public:

- [ ] **CRITICAL**: Revoke exposed Matchplay API token
- [ ] **CRITICAL**: Generate new Matchplay API token
- [ ] **CRITICAL**: Remove `.env` from git history (BFG or filter-branch)
- [ ] **CRITICAL**: Force push cleaned history
- [ ] **CRITICAL**: Update local `.env` with new token
- [ ] Verify `.env` is not tracked: `git ls-files | grep .env` (should only show .env.example)
- [ ] Verify token is not in history: `git log --all -S "686|KBA" --source --all`
- [ ] Review production URL strategy (keep vs replace)
- [ ] Add security section to README
- [ ] Consider adding pre-commit hooks
- [ ] Test fresh clone to ensure setup works

---

## 🔍 Scan Results Summary

### Files Scanned
- ✅ All `.env*` files
- ✅ Python files (`*.py`)
- ✅ TypeScript files (`*.ts`, `*.tsx`)
- ✅ Configuration files (`*.json`, `*.toml`)
- ✅ Documentation files (`*.md`)
- ✅ Git history

### Sensitive Patterns Searched
- API keys/tokens
- Database URLs/credentials
- Environment variables
- Production URLs
- Secrets/passwords

### Clean Areas
- ✅ No hardcoded secrets in source code
- ✅ No database credentials in code
- ✅ Environment variables properly used
- ✅ Deployment configs clean
- ✅ Frontend uses env-based config

---

## 🎯 Next Steps

1. **IMMEDIATE** (before making public):
   - Revoke Matchplay token
   - Clean git history
   - Verify no secrets in repo

2. **RECOMMENDED** (before making public):
   - Add security section to README
   - Decide on production URL strategy
   - Add LICENSE file

3. **NICE TO HAVE** (can do after public):
   - Set up pre-commit hooks
   - Add SECURITY.md for vulnerability reporting
   - Document rate limiting strategy

---

**Report Generated By**: Claude Code Security Audit
**Status**: 🔴 **DO NOT MAKE PUBLIC** until critical issues are resolved
