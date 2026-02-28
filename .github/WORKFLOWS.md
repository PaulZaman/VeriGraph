# GitHub Actions CI/CD Workflows

This project uses GitHub Actions for automated testing and deployment to Fly.io.

## Workflows

### 1. **Test** (`test.yml`)
- **Trigger:** Pull requests targeting `dev` branch
- **Actions:**
  - Run unit tests with pytest
  - Run integration tests (if available)
- **No deployment**

### 2. **Deploy to Dev** (`deploy-dev.yml`)
- **Trigger:** Push to `dev` branch
- **Actions:**
  - Deploy to Fly.io dev app (`verigraph-api-dev`)
  - Verify deployment with health check

### 3. **Deploy to Staging** (`deploy-staging.yml`)
- **Trigger:** Push to `staging` branch
- **Actions:**
  - Deploy to Fly.io staging app (`verigraph-api-staging`)
  - Run smoke tests against staging URL:
    - Health check endpoint
    - Root endpoint
    - Verify endpoint (POST)

### 4. **Deploy to Production** (`deploy-production.yml`)
- **Trigger:** Push to `main` branch
- **Actions:**
  - **Requires manual approval** (GitHub Environment: `production`)
  - Deploy to Fly.io production app (`verigraph-api`)
  - Verify deployment with health check
  - Create deployment summary

## Setup Instructions

### 1. Create Fly.io Apps

```bash
# Create the dev app (if not already created)
fly apps create verigraph-api-dev
```

### 2. Add GitHub Secret

Add your Fly.io API token to GitHub repository secrets:

1. Get your Fly.io token:
   ```bash
   fly auth token
   ```

2. In GitHub:
   - Go to repository **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `FLY_API_TOKEN`
   - Value: Paste your Fly.io token
   - Click **Add secret**

### 3. Set Up Production Environment

For production deployments with manual approval:

1. Go to repository **Settings** → **Environments**
2. Click **New environment**
3. Name: `production`
4. Check **Required reviewers**
5. Add yourself or team members as reviewers
6. Click **Save protection rules**

### 4. Deploy Secrets to Fly.io

Don't forget to set your environment variables:

```bash
cd backend

# Deploy secrets to all environments
./deploy-secrets.sh all

# Or individually
./deploy-secrets.sh dev      # For dev app
./deploy-secrets.sh staging  # For staging app
./deploy-secrets.sh prod     # For production app
```

## Branching Strategy

```
Pull Request → dev
    ↓ (runs tests)

Push to dev
    ↓ (deploys to dev)

Push to staging
    ↓ (deploys to staging + smoke tests)

Push to main
    ↓ (requires approval → deploys to production)
```

## Environment URLs

- **Dev:** https://verigraph-api-dev.fly.dev
- **Staging:** https://verigraph-api-staging.fly.dev
- **Production:** https://verigraph-api.fly.dev

## Testing Locally

Run tests before pushing:

```bash
cd backend
pip install pytest pytest-cov httpx
pytest -v
```

## Workflow Status

Check workflow runs in the **Actions** tab of your GitHub repository.
