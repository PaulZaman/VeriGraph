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

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs
