# ML Model Production Workflow

This document explains how ML models are promoted from Staging to Production and deployed to Fly.io.

## Overview

VeriGraph uses a two-stage model deployment workflow:
- **Staging**: For testing and validation
- **Production**: For live production use

## Model Stages

### Staging
- Used by default in local development
- Used by the staging Fly.io app (`verigraph-api-staging`)
- Models can be tested here before promotion

### Production
- Automatically promoted when code is pushed to `main` branch
- Used by the production Fly.io app (`verigraph-api`)
- Represents the stable, production-ready model

## Automatic Promotion Workflow

When you push code to the `main` branch, the following happens automatically:

1. **GitHub Actions Workflow Triggered** (`.github/workflows/deploy-production.yml`)
   - Runs on every push to `main` that affects backend code

2. **Model Promotion Step**
   - Script: `backend/scripts/promote_model_to_production.py`
   - Actions:
     - Finds the current model in Staging
     - Archives the old Production model (if exists)
     - Promotes the Staging model to Production
     - Logs the promotion details

3. **Deployment to Fly.io**
   - The app is deployed with `MODEL_STAGE=Production`
   - The production app automatically loads the newly promoted model

## Environment Configuration

Each environment has its own `MODEL_STAGE` configuration:

### Local Development (`.env`)
```bash
MODEL_STAGE=Staging  # Use Staging for local development
```

### Staging Environment (`.env.staging`)
```bash
MODEL_STAGE=Staging  # Use Staging for staging environment
```

### Production Environment (`.env.prod`)
```bash
MODEL_STAGE=Production  # Use Production for production environment
```

## Manual Promotion

If you need to manually promote a model to Production:

```python
# Run the promotion script
cd backend
python scripts/promote_model_to_production.py
```

Requirements:
- `DAGSHUB_USER` and `DAGSHUB_TOKEN` environment variables set
- MLflow installed: `pip install mlflow`

## Setting Up Secrets in Fly.io

Before deploying, you need to set all environment secrets (defined in `.env.staging` and `.env.prod`):

```bash
# For staging (reads from .env.staging)
./backend/deploy-secrets.sh staging

# For production (reads from .env.prod)
./backend/deploy-secrets.sh prod

# For both
./backend/deploy-secrets.sh all
```

This deploys ALL environment variables from your `.env` files, including:
- `DAGSHUB_USER`: Your DagHub username
- `DAGSHUB_TOKEN`: Your DagHub API token
- `MODEL_STAGE`: The model stage to use (Staging or Production)
- Plus all other configuration variables

## Deployment Flow

### Development to Staging
1. Develop and test locally with Staging model
2. Push to feature branch or `develop`
3. Deploy to staging: `./backend/deploy.sh staging`
4. Test on staging environment

### Staging to Production
1. Create a Pull Request to `main`
2. Review and approve the PR
3. Merge to `main`
4. **GitHub Actions automatically**:
   - Promotes Staging model to Production
   - Deploys to production Fly.io app
5. Production app now uses the Production model

## Model Versioning

The system ensures:
- Only ONE model can be in Staging at a time
- Only ONE model can be in Production at a time
- Old Production models are automatically archived
- Multiple models can be in Archived state

If multiple models are found in the same stage, the deployment will fail with a clear error message.

## Monitoring

### Check Current Model Stage

The API logs show which model is loaded on startup:

```
INFO:model_loader:Model configuration: fact-checker-bert @ Production
INFO:model_loader:📊 Model Name: fact-checker-bert
INFO:model_loader:📊 Stage: Production
```

### Check Model in MLflow

Visit: https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow

You can see:
- Current models in each stage
- Model versions and their metadata
- Promotion history

## Rollback Process

If you need to rollback to a previous model:

1. Go to DagHub MLflow UI
2. Find the model version you want to rollback to
3. Transition it to Production stage (this will archive the current Production model)
4. Restart the Fly.io production app

Or use the MLflow API:

```python
from mlflow.tracking import MlflowClient
import mlflow

mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")
client = MlflowClient()

# Transition a specific version to Production
client.transition_model_version_stage(
    name="fact-checker-bert",
    version="2",  # Version number to rollback to
    stage="Production",
    archive_existing_versions=True
)
```

## Troubleshooting

### Model Not Found in Stage

**Error**: `No models in Production stage for 'fact-checker-bert'`

**Solution**: 
- Check if a model is actually in Production stage in MLflow
- If not, manually promote one or push to `main` to trigger auto-promotion

### Multiple Models in Same Stage

**Error**: `Multiple models in Production stage: versions [1, 2]`

**Solution**: 
- Go to MLflow UI and move one model to Archived stage
- Only one model should be in each active stage

### Authentication Failed

**Error**: Model promotion or loading fails with auth errors

**Solution**:
- Ensure `DAGSHUB_USER` and `DAGSHUB_TOKEN` are set in Fly.io secrets
- Run: `./backend/deploy-secrets.sh prod` to update all secrets
- Verify credentials are correct in `.env.prod`

## Best Practices

1. **Always test in Staging first**: Never promote directly to Production without testing
2. **Keep Staging and Production in sync**: The Staging model should be tested before promotion
3. **Monitor after promotion**: Check logs and metrics after automatic promotion
4. **Document model changes**: Add notes in MLflow when promoting models
5. **Use version tags**: Tag model versions with meaningful names (e.g., `v1.2-improved-accuracy`)

## Related Documentation

- [DagHub Authentication](./DAGSHUB_AUTH.md) - Setting up DagHub credentials
- [Model Integration](./MODEL_INTEGRATION.md) - How models are loaded and used
- [README](./README.md) - General backend documentation
