# DagHub Authentication Setup

To download model artifacts from DagHub, you need authentication credentials.

## Getting DagHub Credentials

### Option 1: Ask Repo Owner (Easiest)
Ask **@MarcoSrhl** (the repo owner) to:
1. Go to https://dagshub.com/user/settings/tokens
2. Create a **read-only token** with name "verigraph-api"
3. Share the token with you

### Option 2: Fork/Clone Repo (If you have access)
If you have access to the NLP-Fact-checking repo:
1. Go to https://dagshub.com/user/settings/tokens
2. Click "Create Token"
3. Name it "verigraph-api"
4. Select **read-only** permissions
5. Copy the token (you won't see it again!)

## Setting Up Credentials

### Local Development

1. Edit `backend/.env`:
```bash
DAGSHUB_USER=MarcoSrhl
DAGSHUB_TOKEN=your_token_here
```

2. Restart your server:
```bash
uvicorn main:app --reload
```

### Staging/Production (Fly.io)

1. Add credentials to `.env.staging` and `.env.prod`:
```bash
DAGSHUB_USER=MarcoSrhl
DAGSHUB_TOKEN=your_token_here
```

2. Set secrets in Fly.io:
```bash
# Make script executable
chmod +x backend/set-dagshub-secrets.sh

# Set for staging
./backend/set-dagshub-secrets.sh staging

# Set for production
./backend/set-dagshub-secrets.sh prod

# Or both at once
./backend/set-dagshub-secrets.sh all
```

3. Deploy:
```bash
./backend/deploy.sh staging
./backend/deploy.sh prod
```

## Verifying It Works

Check the logs to see if model downloads successfully:

**Local:**
```bash
# You should see:
# ✓ Using DagHub authentication
# ✓ Found staging model v3
# 📥 Downloading model artifacts...
# ✅ Model loaded successfully!
```

**Fly.io:**
```bash
fly logs --app verigraph-api-staging

# Look for the same log messages
```

## Troubleshooting

### "No artifacts found to download"
- Check that DAGSHUB_USER and DAGSHUB_TOKEN are set
- Verify token has read permissions
- Make sure token hasn't expired

### "401 Unauthorized"
- Token is invalid or expired
- Get a new token from DagHub

### "Model not loaded, returning mock prediction"
- Check the logs for specific error messages
- Verify the token is correctly set in environment variables
