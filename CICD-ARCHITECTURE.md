# VeriGraph CI/CD & Architecture Documentation

> Complete guide to VeriGraph's architecture, continuous integration/deployment pipeline, ML model lifecycle, and reproducibility workflows

## 📋 Table of Contents
1. [System Architecture](#-system-architecture)
2. [CI/CD Pipeline Overview](#-cicd-pipeline-overview)
3. [Model Promotion Workflow](#-model-promotion-workflow)
4. [Reproducibility Instructions](#-reproducibility-instructions)
5. [Quick Reference](#-quick-reference)

---

## 🏗️ System Architecture

### High-Level System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          VERIGRAPH ARCHITECTURE                             │
└────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   USERS     │
                              └──────┬──────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
            ┌───────▼────────┐              ┌────────▼────────┐
            │   FRONTEND      │              │   FRONTEND      │
            │   (React+Vite)  │              │   (React+Vite)  │
            │   Production    │              │   Staging       │
            └───────┬─────────┘              └────────┬────────┘
                    │                                 │
                    │ HTTPS                           │ HTTPS
                    │                                 │
        ┌───────────▼────────────┐        ┌──────────▼─────────────┐
        │  BACKEND API           │        │  BACKEND API           │
        │  (FastAPI + Python)    │        │  (FastAPI + Python)    │
        │  verigraph-api.fly.dev │        │  verigraph-api-staging │
        │                        │        │  .fly.dev              │
        │  ENV: Production       │        │  ENV: Staging          │
        │  MODEL: Production     │        │  MODEL: Staging        │
        └───────────┬────────────┘        └──────────┬─────────────┘
                    │                                 │
                    └─────────────┬───────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    NEON POSTGRESQL DB     │
                    │  (Shared - All Envs)      │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   DAGSHUB / MLFLOW        │
                    │   (Model Registry)        │
                    │                           │
                    │  • Model Versioning       │
                    │  • Stage Management       │
                    │  • Metrics Tracking       │
                    │  • Artifact Storage       │
                    └───────────────────────────┘
```

### Component Details

#### Frontend (React + Vite + Tailwind CSS)
- **Technology**: React 18, Vite, Tailwind CSS
- **Role**: User interface for fact-checking claims
- **Environments**: 
  - Local Development: `localhost:5173`
  - Staging: Deployed to CDN/Static hosting
  - Production: Deployed to CDN/Static hosting
- **Build Process**: 
  - Linting with ESLint
  - Production builds optimized via Vite
  - Static assets in `dist/` folder

#### Backend API (FastAPI + Python)
- **Technology**: Python 3.11, FastAPI, Uvicorn
- **Role**: Serve ML predictions, manage claims, data persistence
- **Key Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - Health check
  - `POST /verify` - Fact-check claim
- **Deployment**: 
  - Docker containers on Fly.io
  - Python slim base image (no ML libs embedded)
  - Environment-specific configs (fly.toml, fly.staging.toml)
- **Features**:
  - MLflow model loading from DagHub
  - PostgreSQL integration (Neon)
  - Fast startup without bundled ML models

#### Database (Neon PostgreSQL)
- **Technology**: PostgreSQL (Neon serverless)
- **Role**: Store verified claims, user data, history
- **Access**: Shared across staging and production (different schemas)
- **Connection**: Environment variable `NEON_DB_URL`

#### ML Model Registry (DagHub + MLflow)
- **Repository**: `MarcoSrhl/NLP-Fact-checking`
- **Tracked Models**: 
  - `fact-checker-gan` (BERT-GAN Discriminator) - **Primary**
  - `fact-checker-bert` (deprecated, not in CI/CD)
- **Stages**:
  - `None` - Newly logged models
  - `Staging` - Models ready for testing
  - `Production` - Models deployed to production
  - `Archived` - Old/deprecated models
- **Metrics Logged**: Accuracy, F1 Score, Precision, Recall
- **Access**: MLflow API via DagHub tracking URI

---

## 🔄 CI/CD Pipeline Overview

### Branch Strategy & Deployment Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VERIGRAPH CI/CD PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────┘

Feature Branch
     │
     │ PR → dev
     ├──────────► [TEST.YML] ✅
     │            • Backend Unit Tests (pytest)
     │            • Backend Integration Tests
     │            • Docker Build + Health Check
     │            • Frontend Lint + Build
     │            (4 parallel jobs)
     │
     ▼ merge
   dev
     │
     │ PR → staging
     ├──────────► [CI-STAGING.YML] ✅
     │            • Backend Unit Tests
     │            • Backend Integration Tests
     │            • Backend Coverage Report
     │            • Docker Build + Health + Smoke Tests
     │            • Frontend ESLint + Build
     │            (5 parallel jobs)
     │
     ▼ merge
 staging
     │
     │ PUSH (after merge)
     ├──────────► [CI-STAGING.YML] 🚀
     │            • Build Docker Image
     │            • Deploy to Fly.io Staging
     │            • Smoke Tests (health + endpoints)
     │            (1 deploy job)
     │
     │            🌐 https://verigraph-api-staging.fly.dev
     │            📦 MODEL: Staging
     │
     │ PR → main
     ├──────────► [CI-PRODUCTION.YML] ✅
     │            • Backend Unit Tests
     │            • Backend Integration Tests
     │            • Backend Coverage Report
     │            • Docker Build + Health + Smoke Tests
     │            • Frontend ESLint + Build
     │            (5 parallel jobs - final validation)
     │
     ▼ merge
  main
     │
     │ PUSH (after merge)
     ├──────────► [CI-PRODUCTION.YML] 🚀
     │            
     │            JOB 1: PROMOTE MODEL
     │            • Connect to DagHub MLflow
     │            • Find current Staging model
     │            • Archive old Production models
     │            • Promote Staging → Production
     │            • Log promotion details
     │            
     │            JOB 2: DEPLOY BACKEND (depends on Job 1)
     │            • Build Docker Image
     │            • Deploy to Fly.io Production
     │            • Smoke Tests
     │            
     │            🌐 https://verigraph-api.fly.dev
     │            📦 MODEL: Production (auto-promoted)
     │
     ▼
  PRODUCTION
```

### Workflow Files

| Workflow | File | Trigger | Purpose | Jobs |
|----------|------|---------|---------|------|
| **Dev Tests** | `.github/workflows/test.yml` | PR to `dev` | Fast feedback for developers | 4 parallel test jobs |
| **Staging** | `.github/workflows/ci-staging.yml` | PR to `staging` (tests)<br>Push to `staging` (deploy) | Comprehensive validation + staging deploy | PR: 5 parallel jobs<br>Push: 1 deploy job |
| **Production** | `.github/workflows/ci-production.yml` | PR to `main` (tests)<br>Push to `main` (deploy) | Final validation + model promotion + prod deploy | PR: 5 parallel jobs<br>Push: 2 sequential jobs |

### Key CI/CD Principles

✅ **Tests on PRs, Deploy on Push**
- All validation happens before merge (PR)
- After merge, code is already validated, so only deploy (Push)
- No redundant test execution

✅ **Parallel Job Execution**
- Multiple independent jobs run simultaneously
- Fast feedback (3-4 minutes vs 8-10 sequential)
- Clear failure identification by job name

✅ **Progressive Validation**
- `dev`: Basic tests (unit + integration + build)
- `staging`: Comprehensive tests (+ coverage + eslint)
- `main`: Final checkpoint (same as staging)

✅ **Automated Model Promotion**
- Only happens on push to `main`
- Staging model automatically promoted to Production
- Old Production models archived
- No manual intervention needed

✅ **Environment Isolation**
- Staging and Production are separate Fly.io apps
- Different MLflow stages (Staging vs Production models)
- Shared database with environment-specific schemas

### Pipeline Details

#### 1️⃣ Pull Request to `dev` (Test Workflow)

**File**: `.github/workflows/test.yml`

**Jobs (4 parallel)**:
1. **backend-unit-tests**: Run pytest unit tests (non-integration)
2. **backend-integration-tests**: Run integration tests with database
3. **docker-build**: Build Docker image, test container, health checks
4. **frontend**: Install deps, lint, build production bundle

**Duration**: ~2-3 minutes (parallel execution)

**Purpose**: Quick validation for feature branches, fast feedback cycle

---

#### 2️⃣ Pull Request to `staging` (Staging CI Workflow)

**File**: `.github/workflows/ci-staging.yml`

**Jobs (5 parallel)**:
1. **backend-unit-tests**: Unit test validation
2. **backend-integration-tests**: Integration test validation  
3. **backend-coverage**: Full test suite with coverage report
4. **docker-build**: Build + test + health check + smoke tests
5. **frontend**: ESLint + build + artifact validation

**Duration**: ~3-4 minutes (parallel execution)

**Purpose**: Comprehensive pre-staging validation with code quality checks

---

#### 3️⃣ Push to `staging` (Staging Deployment)

**File**: `.github/workflows/ci-staging.yml`

**Jobs (1 deploy)**:
1. **deploy-backend**:
   - Build Docker image
   - Deploy to Fly.io staging app (`verigraph-api-staging`)
   - Wait 15 seconds
   - Run smoke tests:
     - `GET /health` - Health check
     - `GET /` - Root endpoint

**Duration**: ~3-5 minutes

**Result**: 
- 🌐 https://verigraph-api-staging.fly.dev
- Backend loads `MODEL_STAGE=Staging` from environment
- Model loaded from MLflow Staging stage

---

#### 4️⃣ Pull Request to `main` (Production CI Workflow)

**File**: `.github/workflows/ci-production.yml`

**Jobs (5 parallel)** - Same as staging PR:
1. **backend-unit-tests**
2. **backend-integration-tests**
3. **backend-coverage**
4. **docker-build**
5. **frontend**

**Duration**: ~3-4 minutes

**Purpose**: Final comprehensive checkpoint before production

---

#### 5️⃣ Push to `main` (Production Deployment + Model Promotion)

**File**: `.github/workflows/ci-production.yml`

**Jobs (2 sequential)**:

##### Job 1: **promote-model**
```python
# Inline Python script in GitHub Actions:
1. Connect to DagHub MLflow
2. Get latest Staging model for "fact-checker-gan"
3. Log model version, metrics (accuracy, F1)
4. Get current Production models
5. Archive all old Production models
6. Promote Staging model to Production stage
7. Log success summary
```

**Environment Variables**:
- `DAGSHUB_REPO`: Repository path
- `DAGSHUB_USER`: DagHub username
- `DAGSHUB_TOKEN`: DagHub API token

**Output**: Model promoted, old versions archived

##### Job 2: **deploy-backend** (depends on job 1)
```bash
1. Build Docker image (verigraph-api:production)
2. Setup Fly.io CLI
3. Deploy to Fly.io production app (verigraph-api)
4. Wait 15 seconds
5. Run smoke tests:
   - GET https://verigraph-api.fly.dev/health
   - GET https://verigraph-api.fly.dev/
```

**Duration**: ~5-7 minutes total

**Result**:
- ✅ Model promoted from Staging to Production
- ✅ Backend deployed to production
- 🌐 https://verigraph-api.fly.dev
- Backend loads `MODEL_STAGE=Production` from environment
- Newly promoted model served in production

---

## 🤖 Model Promotion Workflow

### Model Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   ML MODEL LIFECYCLE IN VERIGRAPH                        │
└─────────────────────────────────────────────────────────────────────────┘

1. TRAIN MODEL
   ├─ Jupyter Notebook or Python script
   ├─ Log experiments to MLflow
   ├─ Track metrics: accuracy, F1, precision, recall
   └─ Save model artifacts
        │
        ▼
   ┌──────────────────┐
   │  MLflow Registry │
   │  Stage: None     │
   └────────┬─────────┘
            │
            │ MANUAL: Review metrics in DagHub UI
            │ Decision: Is model good enough for staging?
            │
            ▼
   ┌──────────────────┐
   │  MLflow Registry │  ◄──── MANUAL PROMOTION in DagHub UI
   │  Stage: Staging  │        "Transition to Staging"
   └────────┬─────────┘
            │
            │ Push code to 'staging' branch
            │
            ▼
   ┌──────────────────────────┐
   │  STAGING DEPLOYMENT      │
   │  (Fly.io staging app)    │
   │  Load model from:        │
   │  MODEL_STAGE=Staging     │
   └────────┬─────────────────┘
            │
            │ QA Testing:
            │ • Test predictions
            │ • Validate accuracy
            │ • Performance testing
            │ • Integration testing
            │
            │ Push code to 'main' branch (PR + merge)
            │
            ▼
   ┌──────────────────────────┐
   │  CI/CD AUTO-PROMOTION    │  ◄──── AUTOMATIC (GitHub Actions)
   │                          │        On push to main
   │  1. Get Staging model    │
   │  2. Archive old Prod     │
   │  3. Promote to Prod      │
   └────────┬─────────────────┘
            │
            ▼
   ┌──────────────────┐
   │  MLflow Registry │
   │  Stage: Production│ ◄──── Model now in Production stage
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────────────┐
   │  PRODUCTION DEPLOYMENT   │
   │  (Fly.io production app) │
   │  Load model from:        │
   │  MODEL_STAGE=Production  │
   └──────────────────────────┘
            │
            ▼
         LIVE USERS
```

### Model Stage Definitions

| Stage | Purpose | How to Get There | Used By |
|-------|---------|------------------|---------|
| **None** | Newly logged models | Automatic on MLflow log | N/A |
| **Staging** | Ready for testing | **MANUAL** promotion in MLflow UI | Staging environment |
| **Production** | Production-ready | **AUTOMATIC** promotion on merge to main | Production environment |
| **Archived** | Old/deprecated | Auto-archived when new Production promoted | N/A |

### Tracked Model: `fact-checker-gan`

**Model Type**: BERT-GAN Discriminator for fact-checking

**Architecture**:
- BERT-based text encoder
- GAN discriminator for classification
- Multi-class output: SUPPORTED, REFUTED, NOT ENOUGH INFO

**Metrics Tracked**:
- `test_accuracy` or `accuracy`
- `test_f1` or `f1_score` or `f1`
- `precision`
- `recall`

**Artifacts**:
- `discriminator.pt` - PyTorch discriminator weights
- `generator.pt` - PyTorch generator weights (if applicable)
- `gan_meta.pt` - Model metadata and config

### Promotion Steps

#### Step 1: Train & Log Model
```bash
# In Jupyter notebook or training script:
import mlflow
import dagshub

# Initialize tracking
dagshub.init(repo_owner="MarcoSrhl", repo_name="NLP-Fact-checking", mlflow=True)
mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")

# Log model
with mlflow.start_run(run_name="gan-training-v5"):
    # Train model...
    mlflow.log_params({"learning_rate": 0.001, "epochs": 10})
    mlflow.log_metrics({"accuracy": 0.92, "f1_score": 0.89})
    mlflow.pytorch.log_model(model, "model")
    
    # Register model
    mlflow.register_model(
        model_uri=f"runs:/{mlflow.active_run().info.run_id}/model",
        name="fact-checker-gan"
    )
```

#### Step 2: Manual Promotion to Staging
```
1. Visit: https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow
2. Navigate to "Models" → "fact-checker-gan"
3. Find your model version (e.g., v5)
4. Review metrics (accuracy, F1)
5. Click "Transition Model Version Stage"
6. Select "Staging"
7. Add description (optional): "Promoting v5 for staging tests"
8. Confirm
```

**Result**: Model now in Staging stage, ready for deployment

#### Step 3: Deploy to Staging
```bash
# Create PR: dev → staging
git checkout staging
git merge dev
git push origin staging

# Or via GitHub UI: Create PR and merge

# GitHub Actions automatically:
# - Runs 5 parallel validation jobs (PR)
# - Deploys to staging (after merge)
# - Backend loads MODEL_STAGE=Staging
```

#### Step 4: Test in Staging
```bash
# Test prediction endpoint
curl -X POST https://verigraph-api-staging.fly.dev/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "The Eiffel Tower is in Paris"}'

# Response:
# {
#   "status": "success",
#   "claim": "The Eiffel Tower is in Paris",
#   "result": "SUPPORTED",
#   "confidence": 0.94,
#   "mode": "live"
# }
```

**QA Checklist**:
- ✅ Model loads successfully
- ✅ Predictions are accurate
- ✅ Response time acceptable (<2 seconds)
- ✅ No errors in Fly.io logs
- ✅ Confidence scores reasonable

#### Step 5: Automatic Production Promotion
```bash
# Create PR: staging → main
# After approval, merge to main
git checkout main
git merge staging
git push origin main

# GitHub Actions AUTOMATICALLY:
# 1. [JOB: promote-model]
#    - Connects to DagHub MLflow
#    - Gets Staging model version
#    - Archives old Production models
#    - Promotes Staging → Production
#
# 2. [JOB: deploy-backend]
#    - Builds Docker image
#    - Deploys to production Fly.io
#    - Runs smoke tests
```

**No Manual Intervention Required!**

#### Step 6: Verify Production
```bash
# Check deployment
curl https://verigraph-api.fly.dev/health
# {"status": "healthy"}

# Test prediction
curl -X POST https://verigraph-api.fly.dev/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "The Earth is flat"}'

# Response with newly promoted model:
# {
#   "result": "REFUTED",
#   "confidence": 0.98,
#   "mode": "live"
# }
```

### Rollback Process

If you need to rollback to a previous model version:

**Option 1: Manual Rollback via MLflow UI**
```
1. Visit DagHub MLflow UI
2. Find the old model version to restore
3. Transition it to "Production" stage
4. Old production model auto-archived
5. Restart Fly.io production app:
   flyctl apps restart verigraph-api
```

**Option 2: Programmatic Rollback**
```python
from mlflow.tracking import MlflowClient
import mlflow
import os

# Setup
mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")
os.environ["MLFLOW_TRACKING_USERNAME"] = "your-username"
os.environ["MLFLOW_TRACKING_PASSWORD"] = "your-token"

client = MlflowClient()

# Rollback to version 4
client.transition_model_version_stage(
    name="fact-checker-gan",
    version="4",
    stage="Production",
    archive_existing_versions=True  # Archive current production
)

print("✅ Rolled back to version 4")
```

---

## 🔄 Reproducibility Instructions

### Prerequisites

**Required Tools**:
- Python 3.11+
- Node.js 20+
- Docker
- Git
- Fly.io CLI (for deployment)

**Required Accounts**:
- GitHub account (for CI/CD)
- DagHub account (for MLflow)
- Fly.io account (for deployment)
- Neon account (for PostgreSQL)

### 1. Local Development Setup

#### Backend Setup
```bash
# Clone repository
git clone <repository-url>
cd VeriGraph/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
# Database
NEON_DB_URL=postgresql://user:pass@host/db

# MLflow
DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
MODEL_NAME=fact-checker-gan
MODEL_STAGE=Staging

# DagHub Authentication (optional for local)
DAGSHUB_USER=your-username
DAGSHUB_TOKEN=your-token
EOF

# Run backend
uvicorn main:app --reload --port 8000
# Visit: http://localhost:8000/docs
```

#### Frontend Setup
```bash
cd VeriGraph/frontend

# Install dependencies
npm install

# Run dev server
npm run dev
# Visit: http://localhost:5173
```

#### Test Locally
```bash
# Backend tests
cd backend
pytest test_main.py -v

# Frontend lint
cd frontend
npm run lint

# Frontend build
npm run build
```

### 2. Setting Up CI/CD

#### A. Configure GitHub Secrets
```
Repository → Settings → Secrets and variables → Actions

Add the following secrets:
- NEON_DB_URL: Your PostgreSQL connection string
- DAGSHUB_REPO: MarcoSrhl/NLP-Fact-checking
- DAGSHUB_USER: Your DagHub username
- DAGSHUB_TOKEN: Your DagHub API token
- FLY_API_TOKEN: Your Fly.io deployment token
```

**Get DagHub Token**:
1. Visit: https://dagshub.com/user/settings/tokens
2. Click "Create Token"
3. Name: "VeriGraph CI/CD"
4. Permissions: Read, Write
5. Copy token

**Get Fly.io Token**:
```bash
flyctl auth login
flyctl auth token
# Copy the token
```

#### B. Create Fly.io Apps
```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Create staging app
cd backend
flyctl apps create verigraph-api-staging

# Create production app
flyctl apps create verigraph-api

# Create PostgreSQL (optional, use Neon instead)
# flyctl postgres create --name verigraph-db
```

#### C. Configure Fly.io Apps

**fly.staging.toml**:
```toml
app = "verigraph-api-staging"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services.ports]]
  handlers = ["http"]
  port = 80

[[services.ports]]
  handlers = ["tls", "http"]
  port = 443
```

**fly.toml** (production - same structure, different app name):
```toml
app = "verigraph-api"
# ... rest same as staging
```

#### D. Set Fly.io Secrets

**Create .env.staging**:
```bash
NEON_DB_URL=postgresql://user:pass@host/db
DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
MODEL_NAME=fact-checker-gan
MODEL_STAGE=Staging
DAGSHUB_USER=your-username
DAGSHUB_TOKEN=your-token
```

**Create .env.prod**:
```bash
NEON_DB_URL=postgresql://user:pass@host/db
DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
MODEL_NAME=fact-checker-gan
MODEL_STAGE=Production
DAGSHUB_USER=your-username
DAGSHUB_TOKEN=your-token
```

**Push secrets**:
```bash
cd backend

# Push to staging
./deploy-secrets.sh staging

# Push to production
./deploy-secrets.sh prod

# Or both
./deploy-secrets.sh all
```

### 3. Reproducing the ML Model

#### Train New Model
```python
# In Jupyter notebook or training script
import mlflow
import dagshub
import torch
from transformers import BertModel

# Initialize tracking
dagshub.init(repo_owner="MarcoSrhl", repo_name="NLP-Fact-checking", mlflow=True)
mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")

# Set credentials
import os
os.environ["MLFLOW_TRACKING_USERNAME"] = "your-username"
os.environ["MLFLOW_TRACKING_PASSWORD"] = "your-token"

# Train model
with mlflow.start_run(run_name="fact-checker-gan-training"):
    # 1. Load data
    train_data = load_fever_dataset()
    
    # 2. Initialize model
    model = FactCheckerGAN(
        bert_model="bert-base-uncased",
        num_classes=3  # SUPPORTED, REFUTED, NOT ENOUGH INFO
    )
    
    # 3. Train
    trainer = Trainer(model, train_data)
    metrics = trainer.train(epochs=10, lr=0.001)
    
    # 4. Log parameters
    mlflow.log_params({
        "model_type": "bert-gan",
        "bert_model": "bert-base-uncased",
        "epochs": 10,
        "learning_rate": 0.001,
        "batch_size": 32
    })
    
    # 5. Log metrics
    mlflow.log_metrics({
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1"],
        "precision": metrics["precision"],
        "recall": metrics["recall"]
    })
    
    # 6. Log model artifacts
    mlflow.pytorch.log_model(model.discriminator, "discriminator")
    mlflow.pytorch.log_model(model.generator, "generator")
    
    # 7. Register model
    run_id = mlflow.active_run().info.run_id
    mlflow.register_model(
        model_uri=f"runs:/{run_id}/discriminator",
        name="fact-checker-gan"
    )

print("✅ Model trained and logged to MLflow!")
print("📊 View in DagHub: https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")
```

#### Download Existing Model
```bash
cd macmini

# List available models
python list_mlflow_models.py

# Download specific version
python download_mlflow_artifacts.py \
  --model-name fact-checker-gan \
  --version 1 \
  --stage Production

# Models saved to: models/fact-checker-gan_production_v1/
```

### 4. Manual Deployment (Without CI/CD)

#### Deploy Backend Manually
```bash
cd backend

# Deploy to staging
./deploy.sh staging

# Deploy to production (requires confirmation)
./deploy.sh prod
```

#### Deploy Frontend Manually
```bash
cd frontend

# Build
npm run build

# Deploy dist/ folder to your CDN/hosting
# - Netlify: drag-and-drop dist/ folder
# - Vercel: vercel deploy
# - AWS S3: aws s3 sync dist/ s3://bucket-name/
```

### 5. Testing the Complete Pipeline

#### End-to-End Test
```bash
# 1. Create feature branch
git checkout -b feature/test-pipeline

# 2. Make a small change
echo "# Test" >> backend/README.md

# 3. Commit and push
git add .
git commit -m "test: pipeline test"
git push origin feature/test-pipeline

# 4. Create PR to dev
# Visit GitHub, create PR: feature/test-pipeline → dev
# Wait for 4 parallel test jobs to complete

# 5. Merge to dev
# After tests pass, merge PR

# 6. Create PR to staging
# On GitHub: dev → staging
# Wait for 5 parallel validation jobs

# 7. Merge to staging
# After validation, merge PR
# Automatic deployment to staging

# 8. Verify staging
curl https://verigraph-api-staging.fly.dev/health

# 9. Create PR to main
# On GitHub: staging → main
# Wait for 5 final validation jobs

# 10. Merge to main
# After validation, merge PR
# Automatic model promotion + production deployment

# 11. Verify production
curl https://verigraph-api.fly.dev/health

# 12. Check model stage
# Visit: https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow
# Confirm model promoted to Production
```

### 6. Monitoring & Observability

#### Check Backend Logs
```bash
# Staging
flyctl logs -a verigraph-api-staging

# Production
flyctl logs -a verigraph-api

# Real-time logs
flyctl logs -a verigraph-api --follow
```

#### Check Model Loading
```bash
# Look for these log lines on startup:
# INFO:model_loader:Model configuration: fact-checker-gan @ Production
# INFO:model_loader:📊 Model Name: fact-checker-gan
# INFO:model_loader:📊 Stage: Production
# INFO:model_loader:Model loaded successfully!
```

#### Check CI/CD Status
```
GitHub Repository → Actions tab
- View all workflow runs
- Check parallel job status
- Download logs for debugging
```

#### Check Model Registry
```
DagHub: https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow
- Navigate to "Models"
- View "fact-checker-gan"
- Check stages: Production, Staging, Archived
- View version history and metrics
```

### 7. Troubleshooting Common Issues

#### Issue: Model Not Loading
```bash
# Check environment variables
flyctl ssh console -a verigraph-api
env | grep MODEL
env | grep DAGSHUB

# Expected:
# MODEL_NAME=fact-checker-gan
# MODEL_STAGE=Production
# DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
# DAGSHUB_USER=xxx
# DAGSHUB_TOKEN=xxx
```

**Solution**: Update secrets
```bash
cd backend
./deploy-secrets.sh prod
flyctl apps restart verigraph-api
```

#### Issue: CI/CD Tests Failing
```bash
# Run tests locally first
cd backend
pytest test_main.py -v --tb=short

# Check specific test
pytest test_main.py::test_verify -v
```

#### Issue: Deployment Failed
```bash
# Check app status
flyctl status -a verigraph-api

# Check recent releases
flyctl releases -a verigraph-api

# Rollback if needed
flyctl releases rollback -a verigraph-api
```

#### Issue: Model Promotion Failed in CI
```
# Check GitHub Actions logs:
# Repository → Actions → Failed workflow → promote-model job

# Common causes:
1. No Staging model exists
   → Manually promote to Staging in MLflow UI
2. DagHub credentials invalid
   → Update GitHub secrets: DAGSHUB_USER, DAGSHUB_TOKEN
3. Network timeout
   → Re-run workflow in GitHub Actions
```

### 8. Best Practices for Reproducibility

✅ **Always use virtual environments** for Python
✅ **Pin exact versions** in requirements.txt and package.json
✅ **Log all model hyperparameters** to MLflow
✅ **Use consistent random seeds** for training reproducibility
✅ **Document model architecture** in code comments
✅ **Tag Git commits** with model version numbers
✅ **Test locally before pushing** to CI/CD
✅ **Monitor logs** after each deployment
✅ **Keep .env files secure** (never commit to Git)
✅ **Backup model artifacts** regularly (MLflow handles this)

---

## 🎯 Quick Reference

### Common Commands

```bash
# Local Development
cd backend && uvicorn main:app --reload
cd frontend && npm run dev

# Tests
pytest test_main.py -v                    # Backend tests
npm run lint                               # Frontend lint

# Deployment
./deploy.sh staging                        # Deploy backend to staging
./deploy.sh prod                           # Deploy backend to production
./deploy-secrets.sh all                    # Update secrets

# Docker
docker build -t verigraph-api:local .     # Build image
docker run -p 8080:8080 verigraph-api     # Run container

# Fly.io
flyctl logs -a verigraph-api              # View logs
flyctl status -a verigraph-api            # Check status
flyctl ssh console -a verigraph-api       # SSH into container
flyctl apps restart verigraph-api         # Restart app

# Model Management
python list_mlflow_models.py              # List all models
python download_mlflow_artifacts.py       # Download model
python scripts/promote_model_to_production.py  # Manual promotion
```

### URLs

| Environment | Backend API | MLflow UI |
|-------------|-------------|-----------|
| **Staging** | https://verigraph-api-staging.fly.dev | https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow |
| **Production** | https://verigraph-api.fly.dev | https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow |
| **Local** | http://localhost:8000 | N/A |

### Branch → Environment Mapping

| Branch | Test Workflow | Deploy Environment | Model Stage |
|--------|---------------|-------------------|-------------|
| `feature/*` | ✅ PR to dev | N/A | N/A |
| `dev` | ✅ PR to staging | N/A | N/A |
| `staging` | ✅ PR to main | 🚀 Staging (Fly.io) | Staging |
| `main` | ✅ (already tested) | 🚀 Production (Fly.io) | Production (auto-promoted) |

### Contact & Support

- **CI/CD Issues**: Check `.github/workflows/` and logs in GitHub Actions
- **Model Issues**: Check DagHub MLflow UI and backend logs
- **Deployment Issues**: Check Fly.io logs with `flyctl logs`
- **Documentation**: Refer to `/backend/docs/` for detailed guides

---

**Last Updated**: March 4, 2026  
**Version**: 1.0  
**Maintained By**: VeriGraph Team
