# VeriGraph Backend

FastAPI backend for VeriGraph application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
```

## Running the Server

### Local Development
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs

### Docker (Local)

Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or build and run manually:
```bash
docker build -t verigraph-backend .
docker run -p 8000:8080 verigraph-backend
```

## Deployment to Fly.io

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly.io:
```bash
fly auth login
```

3. Update `.env.prod` with your production frontend URL

4. Create and deploy the app:
```bash
fly launch  # Follow prompts, it will use fly.toml
```

Or deploy manually:
```bash
fly deploy
```

5. Set environment secrets:
```bash
fly secrets set FRONTEND_URL=https://your-frontend-domain.com
```

6. Check status and logs:
```bash
fly status
fly logs
```

7. Open your deployed app:
```bash
fly open
```

## Environment Variables

- `PORT`: Server port (default: 8000 local, 8080 production)
- `HOST`: Host address (default: 0.0.0.0)
- `ENVIRONMENT`: development or production
- `FRONTEND_URL`: Frontend URL for CORS
- `DEBUG`: Debug mode (true/false)

