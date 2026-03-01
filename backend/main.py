from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from data_service import get_data_service

# Load environment variables
load_dotenv()

# Database setup
Base = declarative_base()

class Verification(Base):
    """Verification task model"""
    __tablename__ = 'verifications'
    
    id = Column(String, primary_key=True)
    claim = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    status = Column(String, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Global database session
db_session = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global db_session
    # Startup: Initialize database connection
    db_url = os.getenv("NEON_DB_URL")
    
    # In test mode, use SQLite in-memory database
    if os.getenv("TEST_MODE", "false").lower() == "true" and not db_url:
        db_url = "sqlite:///:memory:"
    
    if not db_url:
        raise ValueError("NEON_DB_URL environment variable is required")
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    yield
    # Shutdown: cleanup
    if db_session:
        db_session.close()

app = FastAPI(title="VeriGraph API", version="1.0.0", lifespan=lifespan)

# Get environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Configure CORS
allowed_origins = [FRONTEND_URL]
if ENVIRONMENT == "development":
    allowed_origins.append("http://localhost:5173")  # Always allow local dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerifyRequest(BaseModel):
    claim: str


@app.get("/")
async def root():
    return {"message": "Welcome to VeriGraph API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/verify")
async def verify_claim(request: VerifyRequest):
    """Create a new verification task"""
    # Determine environment based on MODEL_STAGE or ENVIRONMENT
    model_stage = os.getenv("MODEL_STAGE", "Staging")
    environment = 'staging' if model_stage == 'Staging' else 'production'
    
    # Create verification task
    task_id = str(uuid.uuid4())
    task = Verification(
        id=task_id,
        claim=request.claim,
        environment=environment,
        status='pending',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db_session.add(task)
    db_session.commit()
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Verification task created. Use GET /verify/{task_id} to check status."
    }

@app.get("/verify/{task_id}")
async def get_verification(task_id: str):
    """Get verification task status and results"""
    task = db_session.query(Verification).filter(Verification.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "task_id": task.id,
        "claim": task.claim,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }
    
    if task.status == 'completed' and task.result:
        response.update({
            "verdict": task.result.get("label", "UNKNOWN"),
            "confidence": task.result.get("confidence", 0.0),
            "probabilities": task.result.get("probabilities", {}),
            "mode": task.result.get("mode", "unknown")
        })
    elif task.status == 'failed':
        response["error"] = task.error
    
    return response


# ==============================================================================
# Data Viewing Endpoints
# ==============================================================================

@app.get("/data/runs")
async def list_training_runs():
    """List all training runs with their models and data counts"""
    service = get_data_service()
    runs = service.list_training_runs()
    
    return {
        "status": "success",
        "count": len(runs),
        "runs": runs
    }


@app.get("/data/model/{model_id}")
async def get_model_training_data(
    model_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """Get training data for a specific model"""
    service = get_data_service()
    data = service.get_model_data(model_id, limit)
    
    return {
        "status": "success",
        "model_id": model_id,
        "count": len(data),
        "data": data
    }


@app.get("/data/model/{model_id}/stats")
async def get_model_data_stats(model_id: str):
    """Get statistics about training data for a model"""
    service = get_data_service()
    stats = service.get_model_stats(model_id)
    
    if not stats:
        return {
            "status": "error",
            "message": f"No data found for model {model_id}"
        }
    
    return {
        "status": "success",
        **stats
    }


@app.get("/data/model/{model_id}/search")
async def search_model_claims(
    model_id: str,
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Search claims in model training data"""
    service = get_data_service()
    results = service.search_claims(model_id, q, limit)
    
    return {
        "status": "success",
        "model_id": model_id,
        "query": q,
        "count": len(results),
        "results": results
    }


@app.get("/data")
async def get_current_model_training_data():
    """
    Get training data for the currently active model based on MODEL_STAGE environment.
    Automatically determines which model to show based on Staging/Production stage.
    """
    service = get_data_service()
    result = service.get_current_model_data()
    
    return result

