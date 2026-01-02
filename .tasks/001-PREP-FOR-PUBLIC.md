# Task 001: Prepare Repository for Public Release

**Status**: In Progress
**Created**: 2026-01-02
**Goal**: Clean up the MNP Data Archive project for public release on GitHub

---

## 🎯 Objectives

1. Remove or gitignore generated/temporary files
2. Improve .gitignore for cleaner repository
3. Secure sensitive information (API keys, database credentials)
4. Restructure documentation for human readability
5. Move LLM-specific context to separate files
6. Clean up unused or outdated files
7. Improve overall project documentation

---

## 📋 Task Checklist

### 1. Security Audit ✅ CRITICAL

- [ ] **Verify .env files are gitignored**
  - ✅ Already in .gitignore: `.env`, `.env.local`, `frontend/.env.local`
  - [ ] Confirm no .env files are tracked in git: `git ls-files | grep -E '\.env'`
  - [ ] Check git history for accidentally committed secrets: `git log --all --full-history -- "*.env"`

- [ ] **Review API token usage**
  - ✅ MATCHPLAY_API_TOKEN is in .env (not committed)
  - ✅ .env.example exists with placeholder values
  - [ ] Audit all Python files for hardcoded secrets
  - [ ] Check api/services/matchplay_client.py (uses env var ✓)

- [ ] **Database credentials**
  - ✅ DATABASE_URL in .env (not committed)
  - ✅ .env.example has safe placeholder values
  - [ ] Confirm no production database URLs in code

- [ ] **Review Railway/Vercel configs**
  - [ ] Check railway.toml for sensitive data
  - [ ] Check vercel.json for sensitive data
  - [ ] Ensure deployment docs don't expose production URLs/credentials

---

### 2. Generated Files & Reports Cleanup

**Status**: Reports are ~12MB of generated output

- [ ] **Reports directory cleanup**
  - Current state:
    - `reports/output/` - 80KB of generated markdown reports
    - `reports/charts/` - 12MB of generated PNG charts
  - ✅ Already in .gitignore: `reports/output`, `reports/charts/`
  - [ ] Confirm these directories are not tracked: `git ls-files reports/output reports/charts`
  - [ ] Decision: Keep report generators? (YES - they're core functionality)
  - [ ] Decision: Keep report configs? (YES - they're examples/documentation)
  - [ ] Add README to reports/output/ explaining these are generated
  - [ ] Add README to reports/charts/ explaining these are generated

- [ ] **Other generated files**
  - [ ] Check for any .db, .sqlite files
  - [ ] Check for any temporary .json files (already gitignored)
  - [ ] Review __pycache__ directories (already gitignored)

---

### 3. .gitignore Improvements

Current .gitignore is good but could be enhanced:

- [ ] **Add report-specific ignores**
  ```
  # Generated reports and charts (examples in configs/)
  reports/output/*.md
  reports/charts/*.png
  !reports/output/.gitkeep
  !reports/charts/.gitkeep
  ```

- [ ] **Add task directory** (if keeping tasks private)
  ```
  # Private task tracking
  .tasks/
  ```

- [ ] **Verify all environment files covered**
  ```
  # Environment files
  .env
  .env.*
  !.env.example
  ```

- [ ] **Add common Python/Node patterns missed**
  - [ ] `.pytest_cache/`
  - [ ] `.mypy_cache/`
  - [ ] `*.pyc`
  - [ ] `.coverage`

---

### 4. Documentation Restructuring

**Current state**:
- README.md - Contains detailed MNP match structure (210 lines)
- CLAUDE.md - Comprehensive project guide with LLM context
- Various docs in mnp-app-docs/

**Goals**:
- README.md should be concise, human-focused, getting-started guide
- Move MNP match structure details to LLM-specific context file
- Improve navigation between docs

#### 4.1 Create New Documentation Structure

- [ ] **Create `.claude/MNP_MATCH_STRUCTURE.md`**
  - Move detailed match structure from README.md
  - Include JSON examples, scoring rules, round details
  - This is LLM context (humans already know this)

- [ ] **Rewrite README.md for humans**
  - Project overview (what it does, why it exists)
  - Quick start guide (setup, run locally)
  - Technology stack
  - Directory structure (high-level)
  - Link to detailed docs
  - Contribution guidelines (if accepting contributions)
  - License information

- [ ] **Update .claude/CLAUDE.md**
  - Keep as comprehensive LLM guide
  - Reference new MNP_MATCH_STRUCTURE.md
  - Clean up redundant sections
  - Update file paths if needed

- [ ] **Create CONTRIBUTING.md** (optional)
  - How to set up development environment
  - How to run tests
  - Code style guidelines
  - How to submit issues/PRs

- [ ] **Review and update mnp-app-docs/**
  - Ensure deployment docs don't expose sensitive info
  - Update any outdated information
  - Add links to new doc structure

#### 4.2 Documentation Index

- [ ] **Create docs/INDEX.md**
  - Central hub for all documentation
  - Organized by audience (developers, analysts, LLMs)
  - Quick links to common tasks

---

### 5. Unused/Outdated Files Audit

- [ ] **Review reports/generators/**
  - 15 generators listed in CLAUDE.md
  - [ ] Confirm all are working
  - [ ] Remove any deprecated generators
  - [ ] Update reports/README.md with current list

- [ ] **Review reports/configs/**
  - 23 config files
  - [ ] Remove any obsolete configs
  - [ ] Ensure all have clear naming
  - [ ] Add comments/documentation to complex configs

- [ ] **Check for backup/temp files**
  - [ ] Find: `*.bak`, `*.tmp`, `*~`, `*.old`
  - [ ] Find: `temp/`, `tmp/`, `backup/`

- [ ] **Review root directory**
  - [ ] machine_variations.json - Still used? (YES - referenced in docs)
  - [ ] Check for any scripts that should be in etl/ or reports/

---

### 6. Frontend Cleanup

- [ ] **Check for sensitive data in frontend**
  - [ ] Review frontend/lib/api.ts for hardcoded URLs
  - [ ] Confirm NEXT_PUBLIC_API_URL is environment-based
  - [ ] Check for any console.logs with sensitive data

- [ ] **node_modules**
  - ✅ Already gitignored
  - [ ] Confirm not tracked: `git ls-files frontend/node_modules`

---

### 7. Git Submodule (mnp-data-archive)

- [ ] **Review submodule status**
  - Is mnp-data-archive public or private?
  - [ ] If private: Document how others can access/contribute
  - [ ] If public: Ensure .gitmodules references public URL
  - [ ] Add documentation on updating submodule

---

### 8. Final Quality Checks

- [ ] **License**
  - [ ] Add LICENSE file (MIT, Apache 2.0, GPL, etc.)
  - [ ] Update headers in files if required

- [ ] **Code of Conduct** (if accepting contributions)
  - [ ] Add CODE_OF_CONDUCT.md

- [ ] **GitHub-specific files**
  - [ ] Add .github/ISSUE_TEMPLATE/
  - [ ] Add .github/PULL_REQUEST_TEMPLATE.md
  - [ ] Add .github/workflows/ (CI/CD if desired)

- [ ] **Run final security scan**
  ```bash
  # Check for exposed secrets in git history
  git log --all --full-history --source --find-object=<any-secret>

  # Use git-secrets or similar tool
  # https://github.com/awslabs/git-secrets
  ```

- [ ] **Test fresh clone**
  - Clone to new directory
  - Follow README setup instructions
  - Verify nothing broken
  - Check for missing files

---

## 🚨 Before Making Public

**CRITICAL CHECKLIST**:

1. [ ] All .env files confirmed not in git: `git log --all -- "*.env"`
2. [ ] No API tokens in code: `git grep -i "token\|key\|secret" -- "*.py" "*.ts" "*.tsx" "*.json"`
3. [ ] No production URLs exposed in docs
4. [ ] README.md is welcoming and clear
5. [ ] LICENSE file added
6. [ ] Fresh clone test completed successfully

---

## 📝 Notes

- Keep reports/generators - they're core functionality
- Keep reports/configs - they're examples/documentation
- Reports output/charts are generated, should be gitignored
- .tasks directory is personal, consider gitignoring
- MNP match structure is valuable for LLMs, not needed for human README

---

## 🎓 Resources

- [GitHub's guide to open sourcing](https://opensource.guide/)
- [Choosing a license](https://choosealicense.com/)
- [git-secrets tool](https://github.com/awslabs/git-secrets)
- [Pre-commit hooks](https://pre-commit.com/)

---

## ✅ Completion Criteria

- [ ] No secrets or sensitive data in repository
- [ ] Clean git history (no accidentally committed secrets)
- [ ] Documentation is clear and human-friendly
- [ ] .gitignore prevents future accidental commits
- [ ] Fresh clone works with documented setup
- [ ] README explains project value and how to contribute
- [ ] All generated files are gitignored
- [ ] License clearly stated

---

**Status Legend**:
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- ✅ Verified
