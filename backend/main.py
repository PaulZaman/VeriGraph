from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
import requests
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


@app.get("/graph/entity/{entity}")
async def get_entity_graph(
    entity: str,
    depth: int = Query(1, ge=1, le=2, description="Graph depth (1 or 2 hops)")
):
    """
    Query DBpedia for entity relationships and return graph data.
    Entity should be a DBpedia resource name (e.g., 'Paris', 'France', 'Barack_Obama')
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Clean entity name - replace spaces with underscores
        entity_clean = entity.replace(" ", "_")
        entity_uri = f"http://dbpedia.org/resource/{entity_clean}"
        
        logger.info(f"Querying DBpedia for entity: {entity_clean}")
        
        # Simplified SPARQL query - get outgoing relationships only
        # Keep it simple to avoid timeouts
        sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbp: <http://dbpedia.org/property/>
        
        SELECT DISTINCT ?predicate ?object ?objectLabel
        WHERE {{
          <{entity_uri}> ?predicate ?object .
          OPTIONAL {{ ?object rdfs:label ?objectLabel . FILTER(LANG(?objectLabel) = "en") }}
          FILTER(isIRI(?object) && STRSTARTS(STR(?object), "http://dbpedia.org/resource/"))
          FILTER(!STRSTARTS(STR(?object), "http://dbpedia.org/resource/Template:"))
          FILTER(!STRSTARTS(STR(?object), "http://dbpedia.org/resource/Category:"))
          FILTER(!STRSTARTS(STR(?object), "http://dbpedia.org/resource/File:"))
          FILTER(
            (STRSTARTS(STR(?predicate), "http://dbpedia.org/ontology/") || 
             STRSTARTS(STR(?predicate), "http://dbpedia.org/property/")) &&
            ?predicate != dbo:wikiPageWikiLink &&
            ?predicate != dbo:wikiPageUsesTemplate &&
            ?predicate != dbo:wikiPageExternalLink &&
            ?predicate != dbo:wikiPageID &&
            ?predicate != dbo:wikiPageRevisionID &&
            ?predicate != dbo:thumbnail
          )
        }}
        LIMIT 100
        """
        
        # Query DBpedia SPARQL endpoint with longer timeout
        sparql_endpoint = "https://dbpedia.org/sparql"
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "VeriGraph/1.0"
        }
        params = {
            "query": sparql_query,
            "format": "json"
        }
        
        logger.info("Sending request to DBpedia...")
        response = requests.get(sparql_endpoint, params=params, headers=headers, timeout=20)
        
        logger.info(f"DBpedia response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"DBpedia error: {response.text[:200]}")
            raise HTTPException(status_code=500, detail=f"DBpedia query failed with status {response.status_code}")
        
        results = response.json()
        logger.info(f"Got {len(results.get('results', {}).get('bindings', []))} results from DBpedia")
        
        # Parse results into nodes and edges
        nodes = {}
        edges = []
        filtered_count = {"template": 0, "category": 0, "file": 0, "wikipage": 0, "kept": 0}
        
        # Add center node
        nodes[entity_uri] = {
            "id": entity_uri,
            "label": entity_clean.replace("_", " "),
            "type": "center"
        }
        
        for binding in results.get("results", {}).get("bindings", []):
            object_uri = binding.get("object", {}).get("value", "")
            predicate = binding.get("predicate", {}).get("value", "")
            object_label = binding.get("objectLabel", {}).get("value", "")
            
            # Skip if not a valid DBpedia resource
            if not object_uri or not object_uri.startswith("http://dbpedia.org/resource/"):
                continue
            
            # Skip templates, categories, and files
            if "/Template:" in object_uri:
                filtered_count["template"] += 1
                continue
            if "/Category:" in object_uri:
                filtered_count["category"] += 1
                continue
            if "/File:" in object_uri:
                filtered_count["file"] += 1
                continue
            
            # WHITELIST: Only accept predicates from ontology or property namespaces
            # This filters out most Wikipedia metadata
            if not (predicate.startswith("http://dbpedia.org/ontology/") or 
                    predicate.startswith("http://dbpedia.org/property/")):
                filtered_count["wikipage"] += 1
                continue
            
            # Blacklist specific metadata predicates even if they're in dbo: namespace
            predicate_name = predicate.split("/")[-1]
            if predicate_name in ["wikiPageWikiLink", "wikiPageUsesTemplate", "wikiPageExternalLink", 
                                   "wikiPageID", "wikiPageRevisionID", "thumbnail"]:
                filtered_count["wikipage"] += 1
                continue
            
            filtered_count["kept"] += 1
            
            if not object_label:
                object_label = object_uri.split("/")[-1].replace("_", " ")
            
            # Add node
            nodes[object_uri] = {
                "id": object_uri,
                "label": object_label,
                "type": "entity"
            }
            
            # Add edge (all outgoing from center)
            predicate_label = predicate.split("/")[-1].replace("_", " ")
            edges.append({
                "source": entity_uri,
                "target": object_uri,
                "label": predicate_label,
                "type": "relationship"
            })
        
        logger.info(f"Filtered: {filtered_count}")
        logger.info(f"Returning {len(nodes)} nodes and {len(edges)} edges")
        
        return {
            "status": "success",
            "entity": entity,
            "nodes": list(nodes.values()),
            "edges": edges,
            "count": {
                "nodes": len(nodes),
                "edges": len(edges)
            }
        }
        
    except requests.Timeout:
        logger.error("DBpedia query timeout")
        raise HTTPException(status_code=504, detail="DBpedia query timeout - try a simpler entity")
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error querying DBpedia: {str(e)}")

