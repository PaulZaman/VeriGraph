# CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment.

## Workflow Overview

### 1. **Pull Requests to `dev`** → Run Tests Only
- **Workflow:** `.github/workflows/test.yml`
- **Triggers:** Pull requests targeting the `dev` branch
- **Actions:**
  - Run unit tests
  - Run integration tests
  - No deployment
- **Purpose:** Validate code changes before merging to dev

### 2. **Push to `staging`** → Deploy to Staging + Smoke Tests
- **Workflow:** `.github/workflows/deploy-staging.yml`
- **Triggers:** Pushes to the `staging` branch
- **Actions:**
  - Deploy to Fly.io staging app (`verigraph-api-staging`)
  - Run smoke tests against staging URL
  - Verify endpoints: `/health`, `/`, `/verify`
- **URL:** https://verigraph-api-staging.fly.dev
- **Environment:** `staging`

### 3. **Push to `main`** → Deploy to Production (with Approval)
- **Workflow:** `.github/workflows/deploy-production.yml`
- **Triggers:** Pushes to the `main` branch
- **Actions:**
  - Deploy to Fly.io production app (`verigraph-api`)
  - Run health check
  - Generate deployment summary
- **URL:** https://verigraph-api.fly.dev
- **Environment:** `production` (requires manual approval in GitHub)

## Branch Strategy

```
dev (local)
  ↓
  PR → run tests
  ↓
staging
  ↓
  auto-deploy to staging + smoke tests
  ↓
main
  ↓
  manual approval → deploy to production
```

## Setup Required

### 1. GitHub Secrets
Add the following secret to your GitHub repository:
- `FLY_API_TOKEN`: Your Fly.io API token

To get your Fly.io token:
```bash
fly auth token
```

Then add it to GitHub:
- Go to **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Name: `FLY_API_TOKEN`
- Value: Your token

### 2. (Optional) Enable Manual Approval for Production

To require manual approval before production deployments:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `production`
4. Check **Required reviewers** and add yourself or team members
5. Click **Save protection rules**

Then update `.github/workflows/deploy-production.yml` and add this after line 12:
```yaml
    environment:
      name: production
      url: https://verigraph-api.fly.dev
```

Without this, production deployments will run automatically when you push to `main`.

## Development Workflow

1. **Local Development**
   ```bash
   git checkout dev
   # Make changes
   git add .
   git commit -m "Your changes"
   git push origin dev
   ```
   - Dev branch is for local development only
   - No automatic deployment

2. **Deploy to Staging**
   ```bash
   git checkout staging
   git merge dev
   git push origin staging
   ```
   - Automatically deploys to staging
   - Runs smoke tests
   - Monitor the Actions tab for results

3. **Deploy to Production**
   ```bash
   git checkout main
   git merge staging
   git push origin main
   ```
   - Triggers production deployment workflow
   - Requires manual approval in GitHub Actions
   - Verify health check after deployment

## Monitoring Deployments

- **GitHub Actions:** Check the Actions tab for workflow runs
- **Fly.io Dashboard:** Monitor app status and logs
- **Staging logs:** `fly logs --app verigraph-api-staging`
- **Production logs:** `fly logs --app verigraph-api`

## Rollback

If a production deployment fails:

```bash
# Rollback on Fly.io
fly releases --app verigraph-api
fly releases rollback <version> --app verigraph-api
```

Or redeploy a previous commit:
```bash
git checkout main
git reset --hard <previous-commit-sha>
git push origin main --force
```
