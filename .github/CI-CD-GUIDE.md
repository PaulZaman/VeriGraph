# CI/CD Pipeline - Optimized & Inline

## 🚀 Architecture Overview

The CI/CD pipeline has been **completely optimized** for the new 3-tier architecture where the backend no longer contains ML dependencies.

### Key Improvements

✅ **Inline builds** - Everything happens in one workflow
✅ **Fast Docker builds** - ~30 seconds (no heavy ML dependencies)
✅ **Automated testing** - Tests run before every deployment
✅ **Single source of truth** - One workflow per environment

---

## 📁 Workflow Files

### 1. `test.yml` - Development Branch
**Trigger:** Pull requests to `dev`

**Steps:**
- Install Python dependencies (cached)
- Run pytest tests
- Generate test summary

**Duration:** ~45 seconds

---

### 2. `ci-staging.yml` - Staging Pipeline
**Trigger:** Push or PR to `staging` branch

**Backend Steps:**
1. ✅ **Test** - Run pytest tests
2. ✅ **Build** - Build Docker image inline
3. ✅ **Test Docker** - Verify image works
4. ✅ **Deploy** - Deploy to Fly.io staging (on push only)
5. ✅ **Smoke Tests** - Verify deployment health

**Frontend Steps:**
1. ✅ **Install** - npm ci (cached)
2. ✅ **Build** - npm run build
3. ✅ **Verify** - Check dist/ exists

**Duration:** ~2-3 minutes total

**Deployment URL:** https://verigraph-api-staging.fly.dev

---

### 3. `ci-production.yml` - Production Pipeline
**Trigger:** Push or PR to `main` branch

**Same steps as staging but deploys to production**

**Duration:** ~2-3 minutes total

**Deployment URL:** https://verigraph-api.fly.dev

---

## 🐳 Docker Strategy

### Previous Approach (Slow)
```dockerfile
# Base image with ML dependencies
FROM custom-base-image:latest  # 5 min build
COPY code .
```

**Issues:**
- Depended on external base image
- Required separate build pipeline
- Slow when base image changed

### New Approach (Fast)
```dockerfile
# Lightweight Python image
FROM python:3.11-slim
# Install minimal deps (PostgreSQL only)
RUN pip install fastapi sqlalchemy psycopg2-binary
COPY code .
```

**Benefits:**
- ✅ Self-contained (~30 second builds)
- ✅ No external dependencies
- ✅ Layer caching works perfectly
- ✅ Consistent across environments

---

## 🔄 CI/CD Flow Diagram

### Staging Branch
```
PR to staging → Test → Build → [Manual Review]
                                      ↓
Push to staging → Test → Build → Test Docker → Deploy → Smoke Tests
```

### Production Branch
```
PR to main → Test → Build → [Manual Review]
                                ↓
Push to main → Test → Build → Test Docker → Deploy → Smoke Tests
```

---

## ⚡ Performance Benchmarks

| Task | Old | New | Improvement |
|------|-----|-----|-------------|
| Docker Build | 5-8 min | 30-45 sec | **10x faster** |
| Test Run | 1 min | 45 sec | Same |
| Full Pipeline | 8-10 min | 2-3 min | **3x faster** |

---

## 🧪 Testing Strategy

### Unit Tests
- Located in `backend/test_main.py`
- Run on every PR and push
- Test API endpoints, database logic
- Uses `TEST_MODE=true` to avoid external dependencies

### Integration Tests
- Docker image health check
- Smoke tests after deployment
- Verify `/health` and `/` endpoints
- Test actual deployment works

### Smoke Tests (Post-Deploy)
```bash
curl -f https://verigraph-api-staging.fly.dev/health  # Must return 200
curl -f https://verigraph-api-staging.fly.dev/        # Must return JSON
```

---

## 🔧 Local Testing

### Test Backend Locally
```bash
cd backend
python -m pytest test_main.py -v
```

### Test Docker Build Locally
```bash
cd backend
docker build -t verigraph-api:test .
docker run -d -p 8080:8080 -e TEST_MODE=true verigraph-api:test
curl http://localhost:8080/health
```

### Test Frontend Build
```bash
cd frontend
npm ci
npm run build
ls -lh dist/
```

---

## 📝 Workflow Triggers

### Automatic Triggers
- **Push to `staging`** → Deploy to staging
- **Push to `main`** → Deploy to production
- **PR to `dev`** → Run tests only
- **PR to `staging`** → Run tests + build (no deploy)
- **PR to `main`** → Run tests + build (no deploy)

### Path Filters
Workflows only run when relevant files change:
- `backend/**` - Backend code changes
- `frontend/**` - Frontend code changes
- `.github/workflows/*.yml` - Workflow changes

---

## 🎯 Best Practices

1. **Always test locally first** before pushing
2. **Create PRs** for code review before merging
3. **Check CI logs** if deployment fails
4. **Monitor smoke tests** after each deployment
5. **Use TEST_MODE** for development/testing

---

## 🚨 Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify requirements.txt is valid
- Check Fly.io logs: `flyctl logs -a verigraph-api-staging`

### Tests Fail
- Run locally: `pytest -v`
- Check TEST_MODE is set
- Verify database mocks work

### Deployment Fails
- Check Fly.io secrets are set
- Verify fly.toml configuration
- Check resource limits (RAM/CPU)

### Smoke Tests Fail
- Wait 30 seconds (app might be starting)
- Check Fly.io dashboard
- Verify health endpoint works: `curl https://verigraph-api-staging.fly.dev/health`

---

## 📊 Monitoring

### GitHub Actions
- View workflow runs: https://github.com/YOUR_REPO/actions
- Check job summaries for deployment details
- Download artifacts if needed

### Fly.io
- Staging: https://fly.io/apps/verigraph-api-staging
- Production: https://fly.io/apps/verigraph-api
- Logs: `flyctl logs -a APP_NAME`
- Metrics: Check Fly.io dashboard

---

## 🔐 Secrets Required

### GitHub Secrets
- `FLY_API_TOKEN` - Fly.io deployment token

### Fly.io Secrets (set with flyctl)
- `NEON_DB_URL` - PostgreSQL connection string
- `MODEL_STAGE` - "Staging" or "Production"
- `FRONTEND_URL` - CORS allowed origin

**Set secrets:**
```bash
flyctl secrets set NEON_DB_URL="postgresql://..." -a verigraph-api-staging
```

---

## 📚 Related Documentation

- [Fly.io Docs](https://fly.io/docs/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [MIGRATION.md](../MIGRATION.md) - 3-tier architecture migration guide

---

**Last Updated:** March 1, 2026
**Status:** ✅ Active & Optimized
