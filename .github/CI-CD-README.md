# CI/CD Pipeline Documentation

> **Complete guide to VeriGraph's automated testing, deployment, and ML model promotion workflows**

## 📋 Table of Contents
- [Quick Visual Overview](#-quick-visual-overview)
- [Branch Strategy](#-branch-strategy)
- [Workflow Overview](#-workflow-overview)
- [Quality Gates](#-quality-gates)
- [Deployment Targets](#-deployment-targets)
- [Detailed Workflow Breakdown](#-detailed-workflow-breakdown)

---

## 🎨 Quick Visual Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VeriGraph CI/CD Flow                        │
└─────────────────────────────────────────────────────────────────────┘

Feature Branch
     │
     │ PR → dev
     ├──────────► [Run Tests] ✅
     │
     ▼
   dev branch
     │
     │ PR → staging
     ├──────────► [Tests + Build] ✅
     │
     ▼ (merge)
 staging branch
     │
     │ PUSH (merge)
     ├──────────► [Tests + Build + Deploy to Staging] ✅
     │            [Smoke Tests] ✅
     │            [Check Model Readiness] 📊
     │            
     │            🌐 https://verigraph-api-staging.fly.dev
     │
     │ PR → main
     ├──────────► [Tests + Build] ✅
     │
     ▼ (merge)
  main branch
     │
     │ PUSH (merge)
     ├──────────► [Tests] ✅
     │            [Promote Models with Quality Gates] 🎯
     │            ├─ Check metrics: Accuracy ≥75%, F1 ≥70%
     │            ├─ If PASS: Staging → Production ✅
     │            └─ If FAIL: Block deployment ❌
     │            [Build + Deploy to Production] 🚀
     │            
     │            🌐 https://verigraph-api.fly.dev
     │
     ▼
  PRODUCTION
```

---

## 🌳 Branch Strategy

VeriGraph uses a **three-tier branch strategy** for progressive deployment:

```
dev (development)
  ↓
staging (pre-production)
  ↓
main (production)
```

### Branch Purposes

| Branch | Purpose | CI/CD | Deployment |
|--------|---------|-------|------------|
| **dev** | Active development, feature integration | Tests only | None |
| **staging** | Pre-production testing, QA validation | Tests + Deploy | Fly.io Staging |
| **main** | Production-ready code | Tests + Model Promotion + Deploy | Fly.io Production |

---

## 🔄 Workflow Overview

### Summary Table

| Event | Branch | Workflow File | Tests | Build | Deploy | Model Promotion |
|-------|--------|---------------|-------|-------|--------|-----------------|
| **PR → dev** | `dev` | `test.yml` | ✅ | ❌ | ❌ | ❌ |
| **PR → staging** | `staging` | `ci-staging.yml` | ✅ | ✅ | ❌ | ❌ |
| **PR → main** | `main` | `ci-production.yml` | ✅ | ✅ | ❌ | ❌ |
| **Push to staging** | `staging` | `ci-staging.yml` | ✅ | ✅ | ✅ Staging | ❌ |
| **Push to main** | `main` | `ci-production.yml` | ✅ | ✅ | ✅ Production | ✅ |

---

## 🚦 Quality Gates

### Model Promotion Quality Gates

When code is pushed to **main** branch, ML models are automatically promoted from **Staging → Production** if they meet these thresholds:

| Metric | Minimum Threshold |
|--------|-------------------|
| **Accuracy** | ≥ 75% |
| **F1 Score** | ≥ 70% |

**Models Tracked:**
- `fact-checker-gan` (BERT-GAN Discriminator)
- `fact-checker-bert` (BERT Baseline)

**Promotion Behavior:**
- ✅ If quality gates **pass**: Model promoted to Production, old Production version archived
- ❌ If quality gates **fail**: Promotion blocked, CI pipeline fails
- ℹ️ If model already in Production: Skip promotion (idempotent)

---

## 🌐 Deployment Targets

| Environment | URL | Branch | Fly.io App |
|-------------|-----|--------|------------|
| **Staging** | https://verigraph-api-staging.fly.dev | `staging` | `verigraph-api-staging` |
| **Production** | https://verigraph-api.fly.dev | `main` | `verigraph-api` |

---

## 📖 Detailed Workflow Breakdown

### 1️⃣ Pull Request to `dev` Branch

**Workflow:** `.github/workflows/test.yml`

**Trigger:**
```yaml
on:
  pull_request:
    branches:
      - dev
    paths:
      - 'backend/**'
      - '.github/workflows/test.yml'
```

**Steps:**
1. ✅ **Run Backend Tests**
   - Python unit tests with pytest
   - Test mode enabled (no external dependencies)
   
2. ✅ **Test Quality Gate Logic**
   - Validates model promotion logic
   - Ensures quality gate calculations work correctly

**Purpose:** Fast feedback loop for developers. Only tests code, no builds or deployments.

---

### 2️⃣ Pull Request to `staging` Branch

**Workflow:** `.github/workflows/ci-staging.yml`

**Trigger:**
```yaml
on:
  pull_request:
    branches:
      - staging
    paths:
      - 'backend/**'
      - 'frontend/**'
      - '.github/workflows/ci-staging.yml'
```

**Steps:**

#### Backend
1. ✅ **Run Tests**
2. ✅ **Build Docker Image**
   - Builds `verigraph-api:staging` image
   - Validates Dockerfile and dependencies

#### Frontend
1. ✅ **Install Dependencies** (npm ci)
2. ✅ **Build Production Bundle** (npm run build)

**Purpose:** Validate that code can be built and packaged before merging to staging.

---

### 3️⃣ Push to `staging` Branch (Merge)

**Workflow:** `.github/workflows/ci-staging.yml`

**Trigger:**
```yaml
on:
  push:
    branches:
      - staging
```

**Steps:**

#### Backend Pipeline
1. ✅ **Run Tests**
2. ✅ **Build Docker Image** (`verigraph-api:staging`)
3. ✅ **Test Docker Image**
   - Start container
   - Verify `/health` endpoint
4. 🚀 **Deploy to Fly.io Staging**
   - App: `verigraph-api-staging`
   - Config: `fly.staging.toml`
5. ✅ **Smoke Tests**
   - Wait 15s for deployment
   - Test `/health` endpoint
   - Test root endpoint `/`
6. 📊 **Check Model Promotion Readiness**
   - Queries MLflow/DagHub for Staging models
   - Reports metrics vs quality gate thresholds
   - Informational only (doesn't block)

#### Frontend Pipeline
1. ✅ **Build Production Bundle**

**Result:** Code deployed to staging environment for QA testing.

---

### 4️⃣ Pull Request to `main` Branch

**Workflow:** `.github/workflows/ci-production.yml`

**Trigger:**
```yaml
on:
  pull_request:
    branches:
      - main
    paths:
      - 'backend/**'
      - 'frontend/**'
      - '.github/workflows/ci-production.yml'
```

**Steps:**

#### Backend
1. ✅ **Run Tests**
2. ✅ **Build Docker Image**
   - Builds `verigraph-api:production` image

#### Frontend
1. ✅ **Install Dependencies**
2. ✅ **Build Production Bundle**

**Purpose:** Final validation before production deployment. No actual deployment or model promotion on PR.

---

### 5️⃣ Push to `main` Branch (Merge) - **PRODUCTION DEPLOYMENT**

**Workflow:** `.github/workflows/ci-production.yml`

**Trigger:**
```yaml
on:
  push:
    branches:
      - main
```

**Steps:**

#### Backend Pipeline

##### 1. Tests & Validation
- ✅ **Run Tests**

##### 2. Model Promotion 🎯 **[CRITICAL STEP]**

**GAN Model Promotion:**
- Script: `scripts/promote_with_quality_gate.py`
- Model: `fact-checker-gan`
- Thresholds: Accuracy ≥75%, F1 ≥70%

**Process:**
```
1. Connect to MLflow (DagHub)
2. Fetch Staging model metrics
3. Validate quality gates
4. Compare with current Production model
5. If gates pass:
   ✅ Promote Staging → Production
   📁 Archive old Production version
6. If gates fail:
   ❌ Block pipeline (fail CI)
```

**BERT Model Promotion:**
- Same process for `fact-checker-bert`

##### 3. Docker & Deployment
- ✅ **Build Docker Image** (`verigraph-api:production`)
- ✅ **Test Docker Image**
- 🚀 **Deploy to Fly.io Production**
  - App: `verigraph-api`
  - Config: `fly.toml`

##### 4. Verification
- ✅ **Smoke Tests**
- 📋 **Deployment Summary**

#### Frontend Pipeline
- ✅ **Build Production Bundle**

**Result:** 
- ✅ Models promoted to Production (if quality gates pass)
- ✅ Code deployed to production environment
- ✅ Production ML models in sync with production code

---

## 🔐 Required Secrets

Configure these in GitHub repository settings → Secrets and variables → Actions:

| Secret | Purpose | Used In |
|--------|---------|---------|
| `NEON_DB_URL` | PostgreSQL database connection | All workflows |
| `DAGSHUB_REPO` | DagHub repository (e.g., `owner/repo`) | Staging, Production |
| `DAGSHUB_USER` | DagHub username | Staging, Production |
| `DAGSHUB_TOKEN` | DagHub API token | Staging, Production |
| `FLY_API_TOKEN` | Fly.io deployment token | Staging, Production |

---

## 🛠️ Local Testing

### Test Model Promotion Locally

```bash
cd backend
python scripts/test_promotion_local.py
```

This script will:
1. List all model versions (Production, Staging, Archived)
2. Show Staging model metrics
3. Show current Production model
4. Prompt for promotion confirmation
5. Execute promotion with archive of old Production version

---

## 🎯 Best Practices

### Before Merging to main:

1. ✅ **Test on staging first**
   - Merge to `staging` branch
   - Verify deployment works
   - Test application functionality

2. ✅ **Check model metrics**
   - Review Staging model performance
   - Ensure metrics meet quality gates (≥75% accuracy, ≥70% F1)
   - If below thresholds, retrain before promoting

3. ✅ **Review PR carefully**
   - Check all tests pass
   - Verify Docker build succeeds
   - No breaking changes

### Model Training Workflow:

```
1. Train model locally/notebook
2. Log to MLflow/DagHub with metrics
3. Manually promote to Staging stage in MLflow UI
4. Merge code to staging branch → test deployment
5. If metrics good: merge to main → automatic Production promotion
```

---

## 🔍 Monitoring & Debugging

### Check Deployment Status

**Staging:**
```bash
curl https://verigraph-api-staging.fly.dev/health
```

**Production:**
```bash
curl https://verigraph-api.fly.dev/health
```

### View Model Status

**DagHub/MLflow UI:**
- https://dagshub.com/MarcoSrhl/NLP-Fact-checking
- Navigate to "Models" → View stages (Production, Staging, Archived)

### CI/CD Logs

GitHub Actions:
- Repository → Actions tab
- Select workflow run
- View logs for each step

---

## ⚡ Quick Reference Guide

### Common Scenarios

#### "I want to test my changes"
```bash
# Create PR to dev
git checkout -b feature/my-feature
# ... make changes ...
git push origin feature/my-feature
# Create PR to dev → CI runs tests only
```

#### "I want to deploy to staging"
```bash
# Merge to staging (after PR approved)
git checkout staging
git merge dev
git push origin staging
# → CI runs: tests + build + deploy to staging
# → Check: https://verigraph-api-staging.fly.dev
```

#### "I want to deploy to production"
```bash
# Merge to main (after staging tested)
git checkout main
git merge staging
git push origin main
# → CI runs: tests + model promotion + build + deploy to production
# → Check: https://verigraph-api.fly.dev
```

#### "Model promotion failed - what now?"

If you see:
```
❌ Quality Gate Failed
Accuracy 0.72 below threshold 0.75
```

**Solutions:**
1. **Retrain model** with more data or better hyperparameters
2. **Lower thresholds** (edit workflow files - not recommended)
3. **Skip promotion** temporarily (remove model promotion step - not recommended)

**Recommended:** Improve model training until metrics meet thresholds.

#### "How do I check model metrics before promoting?"

On staging branch after deployment:
1. Check GitHub Actions logs → "Check Model Promotion Readiness" step
2. Or visit: https://dagshub.com/MarcoSrhl/NLP-Fact-checking
3. Navigate to Models → fact-checker-gan → Staging stage
4. View metrics in the Staging model version

---

## 🚨 Troubleshooting

### Issue: "Model promotion hangs in CI"

**Cause:** DagHub OAuth authentication triggered in automated environment

**Solution:** Already fixed! Scripts now detect `CI` environment variable and skip OAuth.

**Verify fix:**
```python
# In promote_with_quality_gate.py
if not os.getenv("CI"):
    dagshub.init(...)  # Only runs locally
else:
    print("Skipping dagshub.init() in CI")  # CI path
```

### Issue: "Deployment failed - connection refused"

**Check:**
1. Fly.io token valid: `flyctl auth token`
2. App exists: `flyctl apps list`
3. Secrets configured in GitHub

### Issue: "Tests pass locally but fail in CI"

**Common causes:**
- Environment variables not set in GitHub Secrets
- Database connection issues (check `NEON_DB_URL`)
- Python version mismatch (CI uses 3.11)

---

## 📊 Metrics & Performance

### Quality Gate Thresholds

Current thresholds are based on baseline model performance:

| Model | Metric | Threshold | Rationale |
|-------|--------|-----------|-----------|
| GAN | Accuracy | ≥75% | Minimum acceptable for fact-checking |
| GAN | F1 Score | ≥70% | Balanced precision/recall |
| BERT | Accuracy | ≥75% | Baseline comparison |
| BERT | F1 Score | ≥70% | Baseline comparison |

**To modify thresholds:**

Edit workflow files:
```yaml
# .github/workflows/ci-production.yml
env:
  MIN_ACCURACY: "0.75"  # Change here
  MIN_F1_SCORE: "0.70"  # Change here
```

---

## 🔄 Model Lifecycle

```
┌──────────────┐
│   Training   │  Local/Notebook: Train model with MLflow logging
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Logging    │  MLflow: Log metrics, params, artifacts
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Staging    │  Manual: Promote to "Staging" stage in MLflow UI
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validation  │  CI/CD: staging branch deployment + metrics check
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Production  │  AUTO: main branch push → quality gates → promotion
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Archived   │  AUTO: Old production versions archived on promotion
└──────────────┘
```

---

## 📞 Support

For CI/CD issues:
1. Check workflow logs in GitHub Actions
2. Verify secrets are configured correctly
3. Test model promotion locally with `test_promotion_local.py`
4. Review quality gate thresholds in workflow files

---

**Last Updated:** March 3, 2026  
**Maintained By:** VeriGraph Team
