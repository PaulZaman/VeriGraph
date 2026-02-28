from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="VeriGraph API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
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
