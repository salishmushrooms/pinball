# MNP App Restart Guide

> **Note**: This guide has been consolidated into the comprehensive development guide.
>
> **See**: [.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md) for complete development workflows

---

## 🚀 Quick Restart

**Stop services**: Press `Ctrl+C` in each terminal window

**Restart API**:
```bash
conda activate mnp
uvicorn api.main:app --reload --port 8000
```

**Restart Frontend**:
```bash
cd frontend
npm run dev
```

**Force kill if needed**:
```bash
lsof -ti:3000 | xargs kill -9  # Kill frontend
lsof -ti:8000 | xargs kill -9  # Kill API
```

---

For detailed troubleshooting, debugging, and complete workflows, see [.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md).
