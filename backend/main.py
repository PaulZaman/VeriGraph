from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import Optional
from data_service import get_data_service

# Load environment variables
load_dotenv()

app = FastAPI(title="VeriGraph API", version="1.0.0")

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
    # TODO: Implement actual verification logic
    return {
        "status": "success",
        "claim": request.claim,
        "result": "SUPPORTED",
        "confidence": 0.85,
        "message": "Claim received and processed"
    }


# ==============================================================================
# Data Viewing Endpoints
# ==============================================================================

@app.get("/data/files")
async def list_data_files():
    """List available data files"""
    service = get_data_service()
    files = service.get_available_files()
    return {
        "status": "success",
        "files": files,
        "count": len(files)
    }


@app.get("/data/stats")
async def get_data_stats():
    """Get statistics about loaded data"""
    service = get_data_service()
    stats = service.get_stats()
    return {
        "status": "success",
        "data": stats
    }


@app.post("/data/load")
async def load_data(filename: Optional[str] = None):
    """Load data into memory (optionally specify a file)"""
    service = get_data_service()
    
    # Initialize DVC if not already done
    if not service.initialize_dvc():
        return {
            "status": "error",
            "message": "Failed to initialize DVC. Make sure DVC is set up and data is available."
        }
    
    # Load the data
    success = service.load_data(filename)
    
    if success:
        stats = service.get_stats()
        return {
            "status": "success",
            "message": f"Loaded {stats.get('triples', 0)} triples",
            "stats": stats
        }
    else:
        return {
            "status": "error",
            "message": "Failed to load data"
        }


@app.get("/data/entity/{entity_name}")
async def get_entity(entity_name: str):
    """Get information about a specific DBpedia entity"""
    service = get_data_service()
    
    if not service.is_loaded:
        return {
            "status": "error",
            "message": "Data not loaded. Call /data/load first."
        }
    
    entity_info = service.get_entity_info(entity_name)
    
    if entity_info:
        return {
            "status": "success",
            "entity": entity_info
        }
    else:
        return {
            "status": "not_found",
            "message": f"Entity '{entity_name}' not found in loaded data"
        }


@app.get("/data/search")
async def search_entities(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """Search for entities by label"""
    service = get_data_service()
    
    if not service.is_loaded:
        return {
            "status": "error",
            "message": "Data not loaded. Call /data/load first."
        }
    
    results = service.search_entities(q, limit)
    
    return {
        "status": "success",
        "query": q,
        "results": results,
        "count": len(results)
    }
