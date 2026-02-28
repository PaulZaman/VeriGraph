from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from model_loader import get_model_loader

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

@app.on_event("startup")
async def startup_event():
    """Initialize the model on startup"""
    get_model_loader()

@app.get("/")
async def root():
    return {"message": "Welcome to VeriGraph API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/verify")
async def verify_claim(request: VerifyRequest):
    # Get model loader and make prediction
    loader = get_model_loader()
    prediction = loader.predict(request.claim)
    
    return {
        "status": "success",
        "claim": request.claim,
        "verdict": prediction.get("label", "UNKNOWN"),
        "confidence": prediction.get("confidence", 0.0),
        "probabilities": prediction.get("probabilities", {}),
        "mode": prediction.get("mode", "unknown"),
        "message": "Claim processed successfully"
    }
