# Model Integration with DagHub

This document explains how the VeriGraph backend integrates with ML models hosted on DagHub.

## Overview

The backend uses MLflow to load and serve models from DagHub. The model is loaded on application startup and used to make predictions on fact-checking claims.

## DagHub Repository

- **Repository:** https://dagshub.com/MarcoSrhl/NLP-Fact-checking
- **Experiments:** https://dagshub.com/MarcoSrhl/NLP-Fact-checking/experiments

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Model Configuration
DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking
MODEL_NAME=fact-checker-bert
MODEL_VERSION=1

# Optional: For private repos or authenticated access
# DAGSHUB_USER=your-username
# DAGSHUB_TOKEN=your-dagshub-token
```

### Model Versions

- `1` - Current version in Staging
- `2`, `3`, etc. - Use a specific model version number
- `latest` - Always use the newest model version (if available)
- `production`, `staging` - Use models tagged with specific stages

## How It Works

### 1. Model Loading

The `model_loader.py` module handles:
- Connecting to DagHub's MLflow tracking server
- Loading the specified model version
- Caching the model in memory for fast predictions

### 2. Prediction Flow

```
Client Request → FastAPI → Model Loader → MLflow Model → Prediction Result
```

### 3. Fallback Mode

If the model fails to load (network issues, authentication, etc.), the API runs in **mock mode**:
- Returns simulated predictions
- Logs warnings about mock mode
- API remains functional for testing

## Usage

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file with DagHub credentials (if needed)

3. Start the server:
```bash
uvicorn main:app --reload
```

4. The model will load on startup. Check logs for:
```
INFO:model_loader:Connected to DagHub repo: MarcoSrhl/NLP-Fact-checking
INFO:model_loader:Loading model from: models:/fact-checker-bert/1
INFO:model_loader:Model loaded successfully!
```

### Making Predictions

Send a POST request to `/verify`:

```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"claim":"The Eiffel Tower is in Paris"}'
```

Response:
```json
{
  "status": "success",
  "claim": "The Eiffel Tower is in Paris",
  "result": "SUPPORTED",
  "confidence": 0.92,
  "mode": "live",
  "message": "Claim processed successfully"
}
```

### Response Fields

- `result`: Prediction result (e.g., "SUPPORTED", "REFUTED", "NOT ENOUGH INFO")
- `confidence`: Model confidence score (0.0 to 1.0)
- `mode`: 
  - `"live"` - Real model prediction
  - `"mock"` - Fallback/simulated prediction
  - `"error"` - Prediction failed

## Deployment

### Fly.io Secrets

When deploying to Fly.io, add the DagHub secrets:

```bash
# Staging
fly secrets set DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking \
  MODEL_NAME=fact-checker-bert \
  MODEL_VERSION=1 \
  --app verigraph-api-staging

# Production
fly secrets set DAGSHUB_REPO=MarcoSrhl/NLP-Fact-checking \
  MODEL_NAME=fact-checker-bert \
  MODEL_VERSION=1 \
  --app verigraph-api
```

Or use the deployment script:
```bash
./deploy-secrets.sh staging
./deploy-secrets.sh production
```

## Troubleshooting

### Model won't load

1. Check DagHub repository access (is it public?)
2. Verify model name and version in DagHub MLflow UI
3. Check logs for specific error messages
4. Test MLflow connection:

```python
import mlflow
mlflow.set_tracking_uri("https://dagshub.com/MarcoSrhl/NLP-Fact-checking.mlflow")
mlflow.search_registered_models()
```

### Slow predictions

- Model loads on first request after startup
- Consider using a GPU-enabled instance for large models
- Implement caching for frequently-checked claims

### Authentication issues

For private repos, set these environment variables:
```bash
DAGSHUB_USER=your-username
DAGSHUB_TOKEN=your-dagshub-access-token
```

Get your token from: https://dagshub.com/user/settings/tokens

## Model Updates

To update the model in production:

1. Train and register new model in DagHub/MLflow
2. Tag it with appropriate stage (e.g., "production")
3. Update `MODEL_VERSION` environment variable
4. Redeploy or restart the application

The model will automatically reload on next startup.

## Customizing Predictions

To modify prediction logic, edit `model_loader.py`:

```python
def predict(self, claim: str) -> dict:
    # Add preprocessing
    processed_claim = preprocess(claim)
    
    # Make prediction
    result = self.model.predict(processed_claim)
    
    # Add postprocessing
    return custom_format(result)
```

## Next Steps

- [ ] Add model versioning metadata to responses
- [ ] Implement prediction caching with Redis
- [ ] Add model performance monitoring
- [ ] Set up A/B testing for multiple models
- [ ] Configure auto-scaling based on prediction load
